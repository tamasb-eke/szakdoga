from sqlalchemy.orm import Session
from sqlalchemy import insert, func, delete
from model.database import Answer, Run
from scripts.safe_operation import safe_operation
from datetime import datetime
from model.variables import AnswerColumn
from typing import Optional

class AnswerDAO:
   
    def __init__(self, session:Session):
        self.session = session

    @safe_operation(default_return=[])
    def get_all(
            self, 
            run_id:int, 
            only_correct:Optional[bool] = False, 
            repeting:Optional[bool] = False, 
            invalid_word:Optional[bool] = False, 
            not_adjacency:Optional[bool] = False,
            too_short:Optional[bool] = False, 
            all_invalid:Optional[bool] = False
        ) -> list[dict]:
        """
        Return with all the answers based on a run_id in a list of dictionary
        
        :param run_id: the id of the run that you are interested in. Can be found in the Run table
        :param only_correct: If it is set to True, then only return the ones that are valid
        :param repeting: If it is set to True, then only return the ones that have the repeting word error
        :param invalid_word: If it is set to True, then only return the ones that have the invalid_word error
        :param not_adjacency: If it is set to True, then only return the ones that have not adjenctive word pair
        :param all_invalid: If it is set to True, then return all the results that are not correct
        """
        error_types = [
            "Repeting words",
            "Not in the acceptable .txt list",
            "Not neighbours",
            "Too short chain length"
        ]

        q = (
            self.session.query(Answer)
            .filter(Answer.run_id == run_id)
        )

        if only_correct:
            q = q.filter(Answer.validation == "True")
        if all_invalid:
            q = q.filter(Answer.validation.in_(error_types))
        elif repeting:
            q = q.filter(Answer.validation == error_types[0])
        elif invalid_word:
            q = q.filter(Answer.validation == error_types[1])
        elif not_adjacency:
            q = q.filter(Answer.validation == error_types[2])
        elif too_short:
            q = q.filter(Answer.validation == error_types[3])
        

        q = q.all()
        return [
            {
                'id' : r.id,
                'chain': r.chain,
                'chain_length': r.chain_length,
                'sourceWord': r.sourceWord,
                'targetWord': r.targetWord,
                'validation' : r.validation
            } for r in q
        ] if q else []
    

    @safe_operation(default_return={})
    def get_all_error(self, run_id:int) -> dict:
        "Return with a dictionary that stores which type has how many error"
        results = (
            self.session.query(Answer.validation, func.count())
            .filter(Answer.run_id == run_id)
            .group_by(Answer.validation)
            .order_by(func.count().desc())
            .all()
        )

        return {validation: count for validation, count in results} if results else {}

    @safe_operation()
    def insert(self, run_id:int, chain: str, chain_length: int, sourceword: str, targetword:str, validation_message: str, date: str = datetime.today().strftime("%Y-%m-%d %H:%M")) -> None:
        """   
        Insert into the Answer table 

        :param run_id: distinct id about the run
        :param chain: The chain of the words
        :param chain_length: Lenght of the chain
        :param sourceword: The first word in the chain
        :param targetword: The last word in the chain
        :param date: By default it is the current. Format of YYYY-MM-DD HH:MM
        :param validation: the validation message
        """
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        data = (
            insert(Answer)
            .values(
                run_id = run_id,
                chain = chain,
                chain_length = chain_length,
                date = date,
                sourceWord = sourceword,
                targetWord = targetword,
                validation = validation_message
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"{chain} was inserted into Answers table")

    @safe_operation()
    def delete_ownerless(self) -> None:
        """Deletes those that has no llm_id or Human_id to it."""

        subq = (
            self.session.query(Answer.id)
            .outerjoin(Run, Run.id == Answer.run_id)
            .where(Run.person_id == None)  # use `is_()` if you want strict SQLAlchemy style
        )

        self.session.execute(delete(Answer).where(Answer.id.in_(subq)))
        self.session.commit()


    @safe_operation()
    def delete(self, delete_id:str|list) -> None:
        """An SQL query that deletes from Answer table"""
        from scripts.logger.logger import get_logger
        logger = get_logger()

        if isinstance(delete_id, str):
            delete_id = [delete_id]

        self.session.query(Answer).filter(Answer.id.in_(delete_id)).delete(synchronize_session='fetch')
        self.session.commit()

        for id_ in delete_id:
            logger.info(f"{id_} was deleted from Answer table")

    @safe_operation()
    def get_(self, answer_id:int, column:AnswerColumn) -> str:
        """Get a specific column value from a Answer record by ID."""
        
        q = self.session.query(Answer).filter(Answer.id == answer_id).first()

        return getattr(q, column) if q else ""
    
    @safe_operation()
    def update(self, answer_id, column:AnswerColumn, new_value:str) -> None:
        """This function is updates a field in answers based on it's ID"""
        from scripts.logger.logger import get_logger
        logger = get_logger()

        q = self.session.query(Answer).filter(Answer.id == answer_id).first()

        if column == 'validation':
            q.validation = new_value

        self.session.commit()
        logger.info(f"With the ID {answer_id} in Answers table, the {column} column was updated with: {new_value}")