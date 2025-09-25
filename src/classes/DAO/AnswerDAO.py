from sqlalchemy.orm import Session
from sqlalchemy import insert, func
from model.database import Answer
from scripts.safe_operation import safe_operation
from datetime import datetime

class AnswerDAO:
   
    def __init__(self, session:Session):
        self.session = session

    @safe_operation(default_return=[])
    def get_all(self, run_id:int, only_correct:bool = False, repeting:bool = False, invalid_word:bool = False, not_adjacency:bool = False, all_invalid:bool = False) -> list[dict]:
        """
        Return with all the answers based on a run_id in a list of dictionary
        
        :param run_id: the id of the run that you are interested in. Can be found in the Run table
        :param correct: If it is set to True, then only return the ones that are valid
        """
        error_types = [
            "Repeting words",
            "Not in the acceptable .txt list",
            "Not neighbours"
        ]

        q = (
            self.session.query(Answer)
            .filter(Answer.run_id == run_id)
        )

        if only_correct:
            q = q.filter(Answer.validation == "True")
        elif repeting:
            q = q.filter(Answer.validation == error_types[0]).all()
        elif invalid_word:
            q = q.filter(Answer.validation == error_types[1]).all()
        elif not_adjacency:
            q = q.filter(Answer.validation == error_types[2]).all()
        elif all_invalid:
            q = q.filter(Answer.validation.in_(error_types)).all()


        return [
            {
                'chain': r.chain,
                'chain_length': r.chain_length,
                'sourceWord': r.sourceWord,
                'targetWord': r.targetWord,
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
            Values:
                run_id: distinct id about the run
                chain: The chain of the words
                chain_length: Lenght of the chain
                sourceword: The first word in the chain
                targetword: The last word in the chain
                date: By default it is the current. Format of YYYY-MM-DD HH:MM
                validation: the validation message
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

        logger.info(f"{chain} was inserted into Answers table   |    Validation:{validation_message}")