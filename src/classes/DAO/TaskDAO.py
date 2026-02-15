from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from model.database import Task
from model.schemas import TaskSchema 
from scripts.safe_operation import safe_operation
from logging import Logger

class TaskDAO:
    def __init__(self, session: Session, logger:Logger):
        self.session = session
        self.logger = logger

    @safe_operation(default_return=[])
    def get_all(self) -> List[TaskSchema]:
        """
        Returns all Task records as a list of dictionaries.
        """
        stmt = select(Task)
        results = self.session.scalars(stmt).all()
        return [TaskSchema.model_validate(r) for r in results]

    @safe_operation()
    def insert(self, task_data: TaskSchema) -> None:
        """   
        Insert into the Task table using a Pydantic DTO.
        Usage: dao.insert(TaskCreateDTO(name="New Task", description="..."))
        """
        stmt = insert(Task).values(**task_data.model_dump())

        self.session.execute(stmt)
        self.session.commit()

        self.logger.info(f"Task '{task_data.name}' was inserted into Task table")

    @safe_operation()
    def delete(self, delete_ids: Union[str, int, List[Union[str, int]]]) -> None:
        """Deletes tasks by ID."""
        
        if not delete_ids:
            return
        
        if not isinstance(delete_ids, list):
            delete_ids = [delete_ids]

        stmt = delete(Task).where(Task.id.in_(delete_ids))
        self.session.execute(stmt)
        self.session.commit()

        for id_ in delete_ids:
            self.logger.info(f"{id_} was deleted from Task table")

    @safe_operation()
    def get_column_value(self, task_id: int, column: str) -> str:
        """
        Get a specific column value dynamically.
        Replaces 'get_' and removes need for 'TaskColumn'.
        """

        if column not in TaskSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column in TaskSchema.")
            return ""

        target_col = getattr(Task, column)
        stmt = select(target_col).where(Task.id == task_id)
        result = self.session.scalar(stmt)

        return str(result) if result is not None else ""