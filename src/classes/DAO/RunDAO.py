from sqlalchemy.orm import Session
from sqlalchemy import insert, func, delete, or_
from model.database import Run, Answer, Human
from scripts.safe_operation import safe_operation
from datetime import datetime
from model.variables import RunColumn

class RunDAO:
   
    def __init__(self, session:Session):
        self.session = session
   
    @safe_operation()
    def get_all(self) -> dict:
        """An SQL query that return with all the data from Run table in a list of dictionaries"""
        q = self.session.query(Run).all()
        
        return {
            r.id : {
                'llm_id' : r.llm_id,
                'person_id': r.person_id,
                'task_id' : r.task_id,
                'json_path' : r.json_path,
                'date' : r.date,
                'successfull' : r.successful
            } for r in q
        } if q else {}
    

    def get_latest_id(self) -> int:
        """Return with the id of the run that was last time"""
        q = self.session.query(Run).order_by(Run.id.desc()).first()
        
        if q:
            return q.id
        
        # if no run.id we need to crash because it will later on cause problem. Better to crash soon
        raise ValueError(f"Can not find lastest run_id from database")


    @safe_operation(default_return=0)
    def get_number_of_questions(self, run_id:int) -> int | None:
        """Return with the number of answers for a given run"""
        query = (
            self.session.query(func.count(Answer.id))
            .filter(Answer.run_id == run_id)
        )

        return query.scalar()

    @safe_operation()
    def insert(self, llm_id:int = 0, person_id:str = None, task_id:int = 1, json_path:str = 'logs', successful:str = 'False', date: str = datetime.today().strftime("%Y-%m-%d %H:%M"), log_path:str = 'logs\\'):
        """   
        Insert into the Run table 
            Values:
                :param llm_id: LLM ID (If we will store person data this should be None)
                :param person_id: Person ID (If we will store LLM data this should be None)
                :param task_id: ID of the task we currently executing
                :param json_path: Path to the .json that stores the results
                :param successful: Was the running succesful
                :param date: The date of the running. Format YYYY-MM-DD HH:MM
                :param log_path: Path the the .log file
        Only the person_id or the llm_id should be an actual id, the other should be None
        """
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        data = (
            insert(Run)
            .values(
                llm_id=llm_id,
                person_id=person_id,
                task_id=task_id,
                json_path=json_path,
                successful=successful,
                date=date,
                log_path=log_path
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"New row was inserted into Run table with id: {self.get_latest_id()}")

    @safe_operation()
    def update(self, run_id:int, value:str, json_path:bool = False) -> None:
        """
        Updates the successful column. Value stores the new value of the successful, based on the run_id
        
        :param value: The new value for successful or json_path
        :param json_path: If it is set to True, then the value will be the new json_path, else the new successful status
        """
        
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        q = self.session.query(Run).where(Run.id == run_id).first()
        
        if json_path:
            q.json_path = value
        else:
            q.successful = value
        
        self.session.commit()

        logger.info(f"{run_id} was updated with {value}")

    @safe_operation(default_return=0)
    def get_id(self, human_id:str) -> int:
        """This is a little bit different, since it can be used the find an older run, based on the human_id"""

        q = self.session.query(Run).filter(Run.person_id == human_id).first()
        return q.person_id if q else 0

    @safe_operation()
    def get_(self, run_id: int, column: RunColumn):
        """Get a specific column value from a Run record by ID."""
        
        q = self.session.query(Run).filter(Run.id == run_id).first()

        return getattr(q, column) if q else ""
    
    @safe_operation()
    def delete_less_than(self, amount:int = 100) -> None:
        """Delete those Runs where the human has less than the amount of games_played"""

        subq = (
            self.session.query(Run.id)
            .join(Human, Human.id == Run.person_id)
            .where(Human.games_played < amount)
        )

        self.session.execute(delete(Run).where(or_(Run.id.in_(subq), Run.successful == 'False')))
        self.session.commit()


    @safe_operation()
    def delete(self, delete_id:str|list) -> None:
        """An SQL query that deletes from Run table"""
        from scripts.logger.logger import get_logger
        logger = get_logger()

        if isinstance(delete_id, str):
            delete_id = [delete_id]

        self.session.query(Run).filter(Run.id.in_(delete_id)).delete(synchronize_session='fetch')
        self.session.commit()

        for id_ in delete_id:
            logger.info(f"{id_} was deleted from Run table")