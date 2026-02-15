from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete, update, insert
from model.database import Answer, Run
from model.schemas import ValidationStatus, AnswerSchema
from scripts.safe_operation import safe_operation
from logging import Logger


class AnswerDAO:
    def __init__(self, session: Session, logger:Logger):
        self.session = session
        self.logger = logger

    @safe_operation(default_return=[])
    def get_all(
        self, 
        run_id: int, 
        validation_filters: Optional[List[ValidationStatus]] = None
    ) -> List[AnswerSchema]:
        """
        Retrieve answers with optional filtering by validation status.
        Returns a list of dictionaries (serialized Pydantic models).
        """
        q = select(Answer).where(Answer.run_id == run_id)
        
        if validation_filters:
            q = q.where(Answer.validation.in_(validation_filters))
            
        results = self.session.scalars(q).all()
        return [AnswerSchema.model_validate(r) for r in results]

    @safe_operation(default_return={})
    def get_validation_stats(self, run_id: int) -> Dict[str, int]:
        """
        Returns a dictionary mapping validation types to their count.
        Renamed from 'get_all_error' to be more descriptive.
        """
        stmt = (
            select(Answer.validation, func.count(Answer.validation))
            .where(Answer.run_id == run_id)
            .group_by(Answer.validation)
            .order_by(func.count(Answer.validation).desc())
        )
        
        results = self.session.execute(stmt).all()
        return {validation: count for validation, count in results}

    @safe_operation()
    def insert(self, answer_data: AnswerSchema) -> None:
        """
        Insert a new answer using a Pydantic DTO.
        
        Usage: 
            dto = AnswerSchema(run_id=1, chain="a-b", ...)
            dao.insert(dto)
        """
        if not answer_data.date:
            answer_data.date = datetime.now().strftime("%Y-%m-%d %H:%M")

        stmt = insert(Answer).values(**answer_data.model_dump())

        self.session.execute(stmt)
        self.session.commit()

        self.logger.info(f"Chain '{answer_data.chain}' inserted into Answer table")

    @safe_operation()
    def delete_ownerless(self) -> None:
        """Deletes answers associated with Runs that have no person_id."""
        
        subq = (
            select(Run.id)
            .where(Run.person_id.is_(None))
        )
        stmt = delete(Answer).where(Answer.run_id.in_(subq))
        
        result = self.session.execute(stmt)
        self.session.commit()
        
        if result.rowcount > 0:
            self.logger.info(f"Deleted {result.rowcount} ownerless records from Answer table")

    @safe_operation()
    def delete(self, delete_ids: Union[str, int, List[Union[str, int]]]) -> None:
        """Deletes specific answers by ID."""

        if not delete_ids:
            return    

        if not isinstance(delete_ids, list):
            delete_ids = [delete_ids]

        stmt = delete(Answer).where(Answer.id.in_(delete_ids))
        self.session.execute(stmt)
        self.session.commit()

        for id_ in delete_ids:
            self.logger.info(f"{id_} was deleted from Answer table")

    @safe_operation()
    def get_column_value(self, answer_id: int, column: str) -> str:

        if column not in AnswerSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column.")
            return ""


        target_col = getattr(Answer, column)
        stmt = select(target_col).where(Answer.id == answer_id)
        result = self.session.scalar(stmt)
        
        return str(result) if result is not None else ""

    @safe_operation()
    def update_field(self, answer_id: int, column: str, new_value: Any) -> None:
        """
        Updates a specific field dynamically.
        Validates that 'column' is a real field in our schema before updating.
        """

        if column not in AnswerSchema.model_fields:
                self.logger.error(f"'{column}' is not a valid column in AnswerSchema.")
                return

        stmt = (
            update(Answer)
            .where(Answer.id == answer_id)
            .values({column: new_value})
        )
        
        self.session.execute(stmt)
        self.session.commit()
        
        self.logger.info(f"ID {answer_id}: Updated '{column}' to '{new_value}'")