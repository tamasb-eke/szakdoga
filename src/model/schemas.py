from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime
from scripts.logger.logger import get_logger



class ValidationTypes(str, Enum):
    TRUE = 'True'
    TOO_SHORT_CHAIN_LENGTH = 'Too short chain length'
    REPEATING_WORDS = 'Repeating words'
    NOT_NEIGHBORS = 'Not neighbors'
    NOT_IN_ACCAPTABLE_TXT_LIST = 'Not in accaptable txt list'
    UNKNOWN = 'Unknown'

    @classmethod
    def all_errors(cls):
        """Returns a list of all members except TRUE"""
        return [member for member in cls if member != cls.TRUE]


class AnswerSchema(BaseModel):
    id: int
    run_id: int
    chain: str
    chain_length: int
    sourceWord: str
    targetWord: str
    validation: ValidationTypes
    date: Optional[str] = None 

    class Config:
        from_attributes = True

class HumanSchema(BaseModel):
    id: int
    games_played: str = 0
    class Config:
        from_attributes = True


class LLMSchema(BaseModel):
    id: int
    name: str
    model: str
    reasoning: str = 'False'


class RunSchema(BaseModel):
    id: int
    llm_id: Optional[int] = None
    person_id: Optional[str] = None
    task_id: int = 1
    json_path: str = 'data/saved_conversation'
    successful: str = 'False'
    date: Optional[str] = None 


class ReadableRunSchema(BaseModel):
    id: int
    date: str
    llm_name: Optional[str] = Field(alias="name") # Maps LLM.name
    llm_model: Optional[str] = Field(alias="model") # Maps LLM.model
    task_name: Optional[str] = Field(alias="task_name") # Maps Task.name
    successful: str

    class Config:
        from_attributes = True


class TaskSchema(BaseModel):
    id: int
    name: str
    description: str
    
    class Config:
        from_attributes = True

class Message(BaseModel):
    role: str
    content: str

class ConversationHistory(BaseModel):
    start_time: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    messages: List[Message] = []

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str):
        self.messages.append(Message(role="assistant", content=content))
    
    def to_dict(self) -> List[Dict]:
        return [msg.model_dump() for msg in self.messages]


class BaseLLMProvider(ABC):
    """Interface that all LLM providers must implement."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def interact(self, history: ConversationHistory, model: str, reasoning: bool, temperature: Optional[float]) -> str:
        pass