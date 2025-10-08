from sqlalchemy.orm import Session
from sqlalchemy import insert
from model.database import Task
from scripts.safe_operation import safe_operation
from model.variables import TaskColumn

class TaskDAO:
   
    def __init__(self, session:Session):
        self.session = session

    @safe_operation(default_return={})
    def get_all(self) -> dict:
        """An SQL operation that returns all the data that is in the Task table in a list of dictionaries"""

        q = self.session.query(Task).all()

        return {
            r.id : {
                'name' : r.name,
                'description' : r.description
            } for r in q
        } if q else {}

    @safe_operation()
    def insert(self, name:str, description:str) -> None:
        """   
        Insert into the Task table 
            Values:
                Name: Name of the task
                Description: A short description for it
        """
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        data = (
            insert(Task)
            .values(
                name=name,
                description=description
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"{name} was inserted into Task table")

    @safe_operation()
    def delete(self, delete_id:str|list) -> None:
        """An SQL query that deletes from Task table"""
        from scripts.logger.logger import get_logger
        logger = get_logger()

        if isinstance(delete_id, str):
            delete_id = [delete_id]

        self.session.query(Task).filter(Task.id.in_(delete_id)).delete(synchronize_session='fetch')
        self.session.commit()

        for id_ in delete_id:
            logger.info(f"{id_} was deleted from Task table")

    @safe_operation()
    def get_(self, task_id: int, column: TaskColumn):
        """Get a specific column value from a Task record by ID."""
        
        q = self.session.query(Task).filter(Task.id == task_id).first()

        return getattr(q, column) if q else ""