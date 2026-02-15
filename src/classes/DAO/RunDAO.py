from typing import List, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete, func, or_
from model.database import Run, Answer, Human, LLM, Task
from model.schemas import RunSchema, ReadableRunSchema
from scripts.safe_operation import safe_operation
from logging import Logger

class RunDAO:
    def __init__(self, session: Session, logger:Logger):
        self.session = session
        self.logger = logger

    @safe_operation(default_return=[])
    def get_all(self) -> List[RunSchema]:
        """
        Returns all Run records as a list of dictionaries.
        """
        stmt = select(Run)
        results = self.session.scalars(stmt).all()
        return [RunSchema.model_validate(r) for r in results]

    @safe_operation(default_return=[])
    def get_all_readable(self) -> List[Dict[str, Any]]:
        """
        Returns a 'readable' view of runs, joined with LLM and Task names.
        Replaces the old 'readable=True' flag.
        """
        stmt = (
            select(
                Run.id, 
                Run.date, 
                LLM.name, 
                LLM.model, 
                Task.name.label("task_name"), 
                Run.successful
            )
            .select_from(Run)
            .outerjoin(LLM, LLM.id == Run.llm_id)
            .outerjoin(Task, Task.id == Run.task_id)
        )
        
        results = self.session.execute(stmt).mappings().all()
        return [ReadableRunSchema.model_validate(r).model_dump() for r in results]

    @safe_operation(default_return=[])
    def get_values_by_column(self, column: str, unique: bool = False) -> List[Any]:
        """
        Returns a list of values from a specific column.
        """
        if column not in RunSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column in RunSchema.")
            return []

        target_col = getattr(Run, column)
        stmt = select(target_col)

        if unique:
            stmt = stmt.distinct()

        results = self.session.scalars(stmt).all()
        return list(results)

    @safe_operation()
    def get_latest_id(self) -> int:
        """Return the ID of the most recent run."""
        stmt = select(Run.id).order_by(Run.id.desc()).limit(1)
        result = self.session.scalar(stmt)
        
        if result is None:
            raise ValueError("Cannot find latest run_id from database")
        return result

    @safe_operation(default_return=0)
    def get_number_of_questions(self, run_id: int) -> int:
        """Return the count of answers for a given run."""
        stmt = (
            select(func.count(Answer.id))
            .where(Answer.run_id == run_id)
        )
        return self.session.scalar(stmt) or 0

    @safe_operation()
    def insert(self, run_data: RunSchema) -> None:
        """   
        Insert into the Run table.
        Usage: dao.insert(RunSchema(llm_id=1, ...))
        """
        if not run_data.date:
            run_data.date = datetime.now().strftime("%Y-%m-%d %H:%M")

        stmt = insert(Run).values(**run_data.model_dump())
        
        self.session.execute(stmt)
        self.session.commit()
        
        self.logger.info(f"New row inserted into Run table")

    @safe_operation()
    def update_field(self, run_id: int, column: str, new_value: Any) -> None:
        """
        Updates a specific field dynamically.
        Replaces the old update(json_path=...) method.
        """
        if column not in RunSchema.model_fields:
            self.logger.error(f"Invalid column '{column}' for update.")
            return

        stmt = (
            update(Run)
            .where(Run.id == run_id)
            .values({column: new_value})
        )
        
        self.session.execute(stmt)
        self.session.commit()
        
        self.logger.info(f"Run {run_id}: Updated '{column}' to '{new_value}'")

    @safe_operation(default_return=0)
    def get_person_id_by_run(self, human_id: str) -> str:
        """
        Finds the person_id associated with a run.
        (Renamed from get_id() because that name was confusing—it took a human_id and returned a person_id?)
        """
        stmt = select(Run.person_id).where(Run.person_id == human_id).limit(1)
        result = self.session.scalar(stmt)
        return result if result else "0"

    @safe_operation()
    def get_column_value(self, run_id: int, column: str) -> str:
        """Get a specific column value dynamically."""
        if column not in RunSchema.model_fields:
            self.logger.error(f"'{column}' is not a valid column.")
            return ""

        target_col = getattr(Run, column)
        stmt = select(target_col).where(Run.id == run_id)
        result = self.session.scalar(stmt)

        return str(result) if result is not None else ""

    @safe_operation()
    def delete_less_than(self, amount: int = 100) -> None:
        """
        Delete Runs where the associated human has played fewer than 'amount' games,
        OR where the run was not successful.
        """
        subq = (
            select(Run.id)
            .join(Human, Human.id == Run.person_id)
            .where(Human.games_played < amount)
        )

        stmt = delete(Run).where(
            or_(
                Run.id.in_(subq), 
                Run.successful == 'False'
            )
        )
        
        self.session.execute(stmt)
        self.session.commit()

    @safe_operation()
    def delete(self, delete_ids: Union[str, int, List[Union[str, int]]]) -> None:
        """Deletes runs by ID."""
        
        if not delete_ids:
            return

        if not isinstance(delete_ids, list):
            delete_ids = [delete_ids]

        stmt = delete(Run).where(Run.id.in_(delete_ids))
        self.session.execute(stmt)
        self.session.commit()

        for id_ in delete_ids:
            self.logger.info(f"{id_} was deleted from Run table")