from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session
from model.database import Answer, Run, Human
from .DAO.AnswerDAO import AnswerDAO
from .DAO.llmDAO import LLMDAO
from .DAO.TaskDAO import TaskDAO
from .DAO.RunDAO import RunDAO
from .DAO.HumanDAO import HumanDAO


class Database:
   from scripts.safe_operation import safe_operation

   def __init__(self):
      from scripts.basic_tools import get_enviromental_variable
      self.database_url = get_enviromental_variable('DATABASE_PATH')
      self.engine = create_engine(self.database_url)
      self.session = Session(self.engine)

      self.llm = LLMDAO(self.session)
      self.answer = AnswerDAO(self.session)
      self.task = TaskDAO(self.session)
      self.run = RunDAO(self.session)
      self.human = HumanDAO(self.session)

   def close(self):
      """Close the database session"""
      self.session.close()

   @safe_operation(default_return=[])
   def create_questions(self, amount:int = 100) -> list[dict]:
      """
      Creates a question that was not been asked based on a person_id
      """
      q = (
         self.session.query(Answer)
         .limit(amount)
         .all()
      )

      return [
         {
            'sourceWord': r.sourceWord,
            'targetWord': r.targetWord,
         } for r in q
      ] if q else []
   
   @safe_operation(default_return=True)
   def already_asked(self, run_id:int, human_id:str) -> bool:
      """
      Checks if a question had been asked based on a human_id and a run_id
      
      :param run_id: The ID of the run you want to get a question for
      :param human_id: The ID of the human you want to get a questions
      """
      q = (
         self.session.query(Answer.sourceWord, Answer.targetWord)
         .join(Run, Run.id == Answer.run_id)
         .join(Human, Human.id == Run.person_id)
         .where(and_(
            Human.id == human_id,
            Run.id == run_id
            )
         )
      )

      if q.first():
         return True
      return False
   
   @safe_operation()
   def evaluation(self, run_id:int) -> None:
      """It's print out the result a run based on the run_id"""
      
      from scripts.logger.logger import get_logger
      logger = get_logger(__name__)

      if self.run.get_(run_id, "successful") == "True":

         distribution = self.answer.get_all_error(run_id)
         total_answers = self.run.get_number_of_questions(run_id)

         logger.info("\n\n")
         logger.info("*" * 50 + "ANSWERS" + "*" * 50)
         logger.info(f"Number of answers: {total_answers}  run id:{run_id}")
         logger.info("\n")

         for key, value in distribution.items():
            percentage = (value / total_answers * 100) if total_answers else 0
            logger.info(f"{key}:{' ' * (50 - len(key))}{value} ({percentage:.1f}%)")
         
      else:
         logger.error(f"The running was unsuccessful: {run_id}")



# Global database instance
_db_instance = None

def get_database() -> Database:
   """
   Get the global database instance.
   Creates it if it doesn't exist yet.
   """
   global _db_instance
   if _db_instance is None:
      _db_instance = Database()
   return _db_instance


def close_database():
   """Close the global database connection"""
   global _db_instance
   if _db_instance is not None:
      _db_instance.close()
      _db_instance = None

