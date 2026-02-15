from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete, and_
from model.database import Answer, Human, Run
from model.schemas import HumanSchema
from scripts.safe_operation import safe_operation
from logging import Logger

class HumanDAO:
    def __init__(self, session: Session, logger:Logger):
        self.session = session
        self.logger = logger

    @safe_operation(default_return=[])
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Returns all data from Human table as a list of dictionaries.
        """
        stmt = select(Human)
        results = self.session.scalars(stmt).all()

        return [HumanSchema.model_validate(r).model_dump() for r in results]

    @safe_operation(default_return=[])
    def get_all_questions(self, human_id: str) -> List[Dict[str, str]]:
        """
        Returns all questions (sourceWord, targetWord) a Human has answered
        where the chain length is > 1.
        """
        stmt = (
            select(Answer.sourceWord, Answer.targetWord)
            .join(Run, Run.id == Answer.run_id)
            .join(Human, Human.id == Run.person_id)
            .where(and_(Human.id == human_id, Answer.chain_length > 1))
        )
        
        results = self.session.execute(stmt).mappings().all()
        return [dict(r) for r in results]

    @safe_operation()
    def insert(self, human_data: HumanSchema) -> None:
        """   
        Insert into the Human table.
        Usage: dao.insert(HumanSchema(id="123", games_played=5))
        """
        stmt = insert(Human).values(**human_data.model_dump())

        self.session.execute(stmt)
        self.session.commit()

        self.logger.info(f"{human_data.id} inserted with {human_data.games_played} games")

    @safe_operation()
    def update_field(self, answer_id: int, column: str, new_value: Any) -> None:
        """
        Updates a specific field dynamically.
        Validates that 'column' is a real field in our schema before updating.
        """

        if column not in HumanSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column in AnswerSchema.")
            return

        stmt = (
            update(Human)
            .where(Human.id == answer_id)
            .values({column: new_value})
        )
        
        self.session.execute(stmt)
        self.session.commit()
        
        self.logger.info(f"ID {answer_id}: Updated '{column}' to '{new_value}'")

    @safe_operation(default_return=False)
    def already_in_db(self, human_id: str) -> bool:
        """Checks if a human exists in the database."""

        stmt = select(1).where(Human.id == human_id)
        result = self.session.scalar(stmt)
        return result is not None

    @safe_operation(default_return=False)
    def already_answered(self, human_id: str, solution: str) -> bool:
        """Checks if a human has already provided a specific solution."""
        stmt = (
            select(1)
            .join(Run, Run.person_id == Human.id)
            .join(Answer, Answer.run_id == Run.id)
            .where(and_(Human.id == human_id, Answer.chain == solution))
            .limit(1)
        )
        
        result = self.session.scalar(stmt)
        return result is not None

    @safe_operation()
    def get_column_value(self, human_id: str, column: str) -> str:
        """
        Get a specific column value. 
        Replaces get_() and removes need for 'HumanColumn' Enum.
        """

        if column not in HumanSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column in HumanSchema.")
            return ""

        target_col = getattr(Human, column)
        stmt = select(target_col).where(Human.id == human_id)
        result = self.session.scalar(stmt)

        return str(result) if result is not None else ""

    @safe_operation(default_return={})
    def delete_less_than(self, amount: int = 100) -> None:
        """Deletes humans with fewer games_played than amount."""
        stmt = delete(Human).where(Human.games_played < amount)
        self.session.execute(stmt)
        self.session.commit()

    @safe_operation()
    def delete(self, delete_ids: Union[str, List[str]]) -> None:
        """Deletes humans by ID."""
        
        if not delete_ids:
            return
        
        if isinstance(delete_ids, str):
            delete_ids = [delete_ids]

        stmt = delete(Human).where(Human.id.in_(delete_ids))
        self.session.execute(stmt)
        self.session.commit()

        for id_ in delete_ids:
            self.logger.info(f"{id_} was deleted from Human table")