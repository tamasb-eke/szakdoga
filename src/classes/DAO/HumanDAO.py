from sqlalchemy.orm import Session
from sqlalchemy import insert, func, and_
from model.database import Answer, Human, Run
from scripts.safe_operation import safe_operation

class HumanDAO:
   
    def __init__(self, session:Session):
        self.session = session

    @safe_operation(default_return=[])
    def get_all(self) -> list:
        """An SQL operation that return all the data from Human table in a list that contains dictionaries"""
        q = self.session.query(Human).all()

        return {
            r.id : {
                "games_played" : r.games_played
            } for r in q
        } if q else []

    @safe_operation()
    def get_all_questions(self, human_id: str) -> list[dict]:
        """
        An SQL query that returns with all question that a given Human have answered in a list of dictionaries
        And only those where the chain_lenght is longer than 1
        
        :param human_id: The ID of the human you want to get it's questions
        """
        q = (
            self.session.query(Answer)
            .join(Run, Run.id == Answer.run_id)
            .join(Human, Human.id == Run.person_id)
            .where(and_(Human.id == human_id, Answer.chain_length > 1))
        ).all()

        return [
            {
                "sourceWord" : r.sourceWord,
                "targetWord" : r.targetWord
            } for r in q
        ]

    @safe_operation()
    def insert(self, human_id:str, games_played:int = 0) -> None:
        """   
        Insert into the Human table 
            Values:
                ID: The ID of the Human
        """
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        data = (
            insert(Human)
            .values(
                id=human_id,
                games_played = games_played
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"{human_id} was inserted into human table with {games_played} played games")

    @safe_operation()
    def update_games_played(self, human_id:str, played:int) -> None:
        """Updates the games_played column. Played stores the new value of the number of games she/he has played"""

        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        q = self.session.query(Human).where(Human.id == human_id).first()
        q.games_played = played
        self.session.commit()

        logger.info(f"{human_id}'s games played was updated to {played}")

    @safe_operation(default_return=False)
    def already_in_db(self, human_id:str) -> bool:
        """Returns with a bool value based on if a human is already in the database or not"""

        q = self.session.query(Human.id).where(Human.id == human_id).first()

        if q:
            return True
        return False