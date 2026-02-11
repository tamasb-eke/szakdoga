from typing import Optional, List, Dict, Literal, Any
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from scripts.logger.logger import get_logger



class ValidationStatus(str, Enum):
    VALID = 'True'
    TOO_SHORT = 'Too short chain length'
    REPEATING_WORDS = 'Repeating words'
    NOT_NEIGHBORS = 'Not neighbors'
    INVALID_WORD = 'Not in acceptable txt list'
    UNKNOWN = 'Unknown'
    SYNTAXERROR = 'SyntaxError'

    @classmethod
    def errors(cls) -> List['ValidationStatus']:
        """Returns all error statuses (everything except VALID)."""
        return [member for member in cls if member != cls.VALID]

class AnswerSchema(BaseModel):
    id: int
    run_id: int
    chain: str
    chain_length: int
    sourceWord: str
    targetWord: str
    validation: ValidationStatus 
    date: Optional[str] = None 

    class Config:
        from_attributes = True


class HumanSchema(BaseModel):
    id: str
    games_played: int = 0 
    
    class Config:
        from_attributes = True


class LLMSchema(BaseModel):
    id: int
    name: str
    model: str
    reasoning: bool = False

    class Config:
        from_attributes = True


class RunSchema(BaseModel):
    id: int
    llm_id: Optional[int] = None
    person_id: Optional[str] = None
    task_id: int = 1
    json_path: str = 'data/saved_conversation'
    successful: bool = False
    date: Optional[str] = None 
    
    class Config:
        from_attributes = True


class ReadableRunSchema(BaseModel):
    id: int
    date: str
    llm_name: Optional[str] = Field(alias="name")
    llm_model: Optional[str] = Field(alias="model")
    task_name: Optional[str] = Field(alias="task_name")
    successful: bool = False

    class Config:
        from_attributes = True


class TaskSchema(BaseModel):
    id: int
    name: str
    description: str
    
    class Config:
        from_attributes = True


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    class Config:
        extra = "forbid" 

    @model_validator(mode='before')
    @classmethod
    def normalize_legacy_data(cls, data: Any) -> Any:
        """
        Intercepts raw data to normalize keys ('say' -> 'content') 
        and values ('Prompt' -> 'user').
        """
        if not isinstance(data, dict):
            return data
        
        if 'say' in data:
            data['content'] = data.pop('say')
        
        role_mapping = {
            "Prompt": "user",
            "Response": "assistant",
            "user": "user",
            "assistant": "assistant"
        }
        
        if 'role' in data and data['role'] in role_mapping:
            data['role'] = role_mapping[data['role']]
            
        return data

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


class GameEntry(BaseModel):
    """Represents the innermost game data"""
    chain: str
    chain_length: int
    raw_date: str = Field(alias="date") 
    language: str
    source_word: str = Field(alias="sourceWord") 
    target_word: str = Field(alias="targetWord")
    time_in_sec: int
    wordlength: int


class GameLogsExport(BaseModel):
    """
    Represents the entire JSON structure.
    Structure: GameLogs -> PlayerID (str) -> GameID (str) -> GameEntry
    """
    GameLogs: Dict[str, Dict[str, GameEntry]]