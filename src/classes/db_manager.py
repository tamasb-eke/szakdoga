from typing import List, Dict, Optional
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session
from model.database import Answer, Run, Human
from .DAO.AnswerDAO import AnswerDAO
from .DAO.llmDAO import LLMDAO
from .DAO.TaskDAO import TaskDAO
from .DAO.RunDAO import RunDAO
from .DAO.HumanDAO import HumanDAO
from scripts.safe_operation import safe_operation
from scripts.basic_tools import get_enviromental_variable
from scripts.logger.logger import get_logger
from model.schemas import ValidationStatus, RunSchema


class Database:
   def __init__(self):
      self.logger = get_logger(__name__)
      self.database_url = get_enviromental_variable('DATABASE_PATH')
      self.engine = create_engine(self.database_url)
      self.session = Session(self.engine)
      self.llm = LLMDAO(self.session, self.logger)
      self.answer = AnswerDAO(self.session, self.logger)
      self.task = TaskDAO(self.session, self.logger)
      self.run = RunDAO(self.session, self.logger)
      self.human = HumanDAO(self.session, self.logger)
      
   def close(self):
      """Close the database session"""
      self.session.close()

   def __enter__(self):
      """Allows use in 'with' statements"""
      return self

   def __exit__(self, exc_type, exc_val, exc_tb):
      """Automatically closes session on exit"""
      self.close()

   @safe_operation(default_return=[])
   def create_questions(self, amount: int = 100) -> List[Dict[str, str]]:
      """
      Fetches a list of source/target word pairs from existing answers.
      Useful for generating test sets.
      """

      stmt = (
         select(Answer.sourceWord, Answer.targetWord)
         .limit(amount)
      )
      
      results = self.session.execute(stmt).mappings().all()
      return [dict(r) for r in results]
   
   @safe_operation(default_return=False)
   def already_asked(self, run_id: int, human_id: str) -> bool:
      """
      Checks if a specific human has already contributed answers to a specific run.
      """

      stmt = (
         select(1)
         .join(Run, Run.id == Answer.run_id)
         .join(Human, Human.id == Run.person_id)
         .where(and_(
               Human.id == human_id,
               Run.id == run_id
         ))
         .limit(1)
      )

      result = self.session.scalar(stmt)
      return result is not None
   
   @safe_operation()
   def evaluation(self, run_id: int) -> None:
      """Prints out the evaluation statistics for a specific run."""
      

      weighting = {
         ValidationStatus.TOO_SHORT_CHAIN_LENGTH : 0.8,
         ValidationStatus.REPEATING_WORDS : 0.6,
         ValidationStatus.NOT_NEIGHBORS : 0.4,
         ValidationStatus.NOT_IN_ACCAPTABLE_TXT_LIST : 0.2,
         ValidationStatus.TRUE : 0
      }

      is_successful = self.run.get_column_value(run_id, RunSchema.successful)
      
      if str(is_successful).lower() == "false":
         self.logger.warning(f"Run {run_id} was unsuccessful. Results may be affected.")

      distribution = self.answer.get_validation_stats(run_id)
      total_answers = self.run.get_number_of_questions(run_id)

      print("\n\n")
      print("*" * 50 + " ANSWERS " + "*" * 50)
      print(f"Number of answers: {total_answers} | Run ID: {run_id}")
      print("\n")

      weighted_sum = 0
      total_items = 0

      for validation_type, count in distribution.items():
         weight = weighting.get(validation_type, 0)
         weighted_sum += count * weight
         total_items += count
         percentage = (count / total_answers * 100) if total_answers > 0 else 0
         
         print(f"{validation_type:<50} {count} ({percentage:.1f}%)")
      
      if total_items > 0:
         final_score = (weighted_sum / (total_items * 0.8)) * 100
      else:
         final_score = 0.0
         
      print(f'\nError weight sum_percent: {final_score:.2f}%')


_db_instance: Optional[Database] = None

def get_database() -> Database:
   """
   Get the global database instance. Creates it if it doesn't exist.
   """
   global _db_instance
   if _db_instance is None:
      _db_instance = Database()
   return _db_instance

def close_database():
   """Close the global database connection."""
   global _db_instance
   if _db_instance is not None:
      _db_instance.close()
      _db_instance = None