from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from model.database import LLM
from model.schemas import LLMSchema
from scripts.safe_operation import safe_operation
from scripts.logger.logger import get_logger

class LLMDAO:
    def __init__(self, session: Session):
        self.session = session
        self.logger = get_logger(__name__)

    @safe_operation(default_return=[])
    def get_all(self) -> List[LLMSchema]:
        """
        Returns all LLM records as a list of dictionaries.
        """
        stmt = select(LLM)
        results = self.session.scalars(stmt).all()
        
        return [LLMSchema.model_validate(r) for r in results]

    @safe_operation(default_return=[])
    def get_(self, column: str, unique: bool = False) -> List[Any]|str:
        """
        Returns a list of values from a specific column (e.g. get all model names).
        """
        if column not in LLMSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column in LLMSchema.")
            return []

        target_col = getattr(LLM, column)
        stmt = select(target_col)

        if unique:
            stmt = stmt.distinct()

        results = self.session.scalars(stmt).all()
        return list(results) if len(list(results)) > 0 else results[0]

    @safe_operation(default_return=False)
    def is_reasoning(self, llm_id: int) -> bool:
        """
        Checks if the LLM is reasoning capable. 
        Handles the string "True"/"False" conversion robustly.
        """
        stmt = select(LLM.reasoning).where(LLM.id == llm_id)
        result = self.session.scalar(stmt)
        
        return str(result).lower() == "true"

    @safe_operation()
    def insert(self, llm_data: LLMSchema) -> None:
        """
        Insert into the LLM table using a DTO.
        """
        stmt = insert(LLM).values(**llm_data.model_dump())
        
        self.session.execute(stmt)
        self.session.commit()

        self.logger.info(
            f"Inserted LLM '{llm_data.name}' | Model: {llm_data.model} | Reasoning: {llm_data.reasoning}"
        )

    @safe_operation()
    def delete(self, delete_ids: Union[str, int, List[Union[str, int]]]) -> None:
        """Deletes LLMs by ID."""
        
        if not delete_ids:
            return
        
        if not isinstance(delete_ids, list):
            delete_ids = [delete_ids]

        stmt = delete(LLM).where(LLM.id.in_(delete_ids))
        self.session.execute(stmt)
        self.session.commit()

        for id_ in delete_ids:
            self.logger.info(f"{id_} was deleted from LLM table")

    @safe_operation()
    def get_column_value(self, llm_id: int, column: str) -> str:
        """
        Get a specific column value dynamically.
        Replaces get_, get_name, and get_model.
        """

        if column not in LLMSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column.")
            return ""

        target_col = getattr(LLM, column)
        stmt = select(target_col).where(LLM.id == llm_id)
        result = self.session.scalar(stmt)

        return str(result) if result is not None else ""