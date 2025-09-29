from sqlalchemy.orm import Session
from sqlalchemy import insert
from model.database import LLM
from scripts.safe_operation import safe_operation


class LLMDAO:

    def __init__(self, session:Session):
        self.session = session

    @safe_operation(default_return={})
    def get_all(self) -> dict:
        """SQL funtion that return all data from LLM table in a dictionary"""

        q = self.session.query(LLM).all()

        return {
            r.id : {
                'name' : r.name,
                'model' : r.model,
                'reasoning' : r.reasoning
            } for r in q
        } if q else {}
    
    @safe_operation()
    def get_name(self, llm_id:int) -> str | None:
        """SQL query that return's with tha name of a LLM base on it's ID"""
        q = self.session.query(LLM.name).where(LLM.id == llm_id)

        return q.first()[0] if q else None 

    @safe_operation()
    def get_model(self, llm_id:int) -> str|None:
        """Return the model name, that can be used in the API call"""

        q = self.session.query(LLM).where(LLM.id == llm_id).first()

        return q.model if q else None 


    @safe_operation(default_return=False)
    def is_reasoning(self, llm_id:int) -> bool:
        """Return with a bool value. Is it the LLM reasoning capable? True|False"""

        q = self.session.query(LLM).where(LLM.id == llm_id).first()

        if q and q.reasoning == "True":
            return True
        return False
    
    @safe_operation()
    def insert(self, name:str, model:str, reasoning:str = "false"):
        """
        Insert into the LLM table
        
        :param name: Name of the LLM
        :param model: The model of the LLM
        :param reasoning: If it is capable of the reasoning
        """
    
        from scripts.logger.logger import get_logger
        logger = get_logger(__name__)

        data = (
            insert(LLM)
            .values(
                name = name,
                model = model,
                reasoning = reasoning
            )
        )

        self.session.execute(data)
        self.session.commit()

        logger.info(f"{name} was inserted into LLM table with the following parameter: model={model} | resoning={reasoning}")

    @safe_operation()
    def delete(self, delete_id:str|list) -> None:
        """An SQL query that deletes from LLM table"""
        from scripts.logger.logger import get_logger
        logger = get_logger()

        if isinstance(delete_id, str):
            delete_id = [delete_id]

        self.session.query(LLM).filter(LLM.id.in_(delete_id)).delete(synchronize_session='fetch')
        self.session.commit()

        for id_ in delete_id:
            logger.info(f"{id_} was deleted from LLM table")