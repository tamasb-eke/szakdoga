from sqlalchemy.orm import Session
from sqlalchemy import insert, func
from model.database import Run, Answer
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
    def insert(self, llm_id:int, person_id:str, task_id:int, json_path:str, successful:str = False, date: str = datetime.today().strftime("%Y-%m-%d %H:%M")):
        """   
        Insert into the Run table 
            Values:
                llm_id: LLM ID (If we will store person data this should be None)
                person_id: Person ID (If we will store LLM data this should be None)
                task_id: ID of the task we currently executing
                json_path: Path to the .json that stores the results
                successful: Was the running succesful
                date: The date of the running. Format YYYY-MM-DD HH:MM
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
                date=date
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"New row was inserted into Run table")

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


    @safe_operation(default_return="")
    def get_(self, run_id: int, column: RunColumn) -> str:
        """Get a specific column value from a Run record by ID."""
        

        q = self.session.query(Run).filter(Run.id == run_id).first()

        return getattr(q, column) if q else ""