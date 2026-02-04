import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import anthropic
from openai import OpenAI, RateLimitError
from google import genai
from google.genai import types
from scripts.safe_operation import safe_operation
from scripts.basic_tools import DATA_FOLDER, get_enviromental_variable
from model.schemas import BaseLLMProvider, ConversationHistory, Message, LLMSchema, RunSchema
from scripts.logger.logger import get_logger

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)

    def interact(self, history: ConversationHistory, model: str = "o1-pro", reasoning: bool = False, temperature: float = None) -> str:
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=history.to_dict(),
                    extra_body={"reasoning_effort": "medium"} if reasoning and "o1" in model else None,
                    temperature=temperature
                )
                return response.choices[0].message.content

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Rate limit exceeded after {max_retries} attempts.")
                    raise e
                
                self.logger.warning(f"Rate limit hit. Retrying in {base_delay}s...")
                time.sleep(base_delay)
                base_delay *= 2
            except Exception as e:
                self.logger.error(f"OpenAI Error: {e}")
                return ""
        return ""


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    def interact(self, history: ConversationHistory, model: str = "claude-3-opus-20240229", reasoning: bool = False, temperature: float = 1.0) -> str:
        
        thinking_param = {
            "type": "enabled",
            "budget_tokens": 1024
        } if reasoning else {"type": "disabled"}

        if reasoning:
            temperature = 1.0

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                messages=history.to_dict(),
                thinking=thinking_param if reasoning else None,
                temperature=temperature
            )

            assistant_message = ""
            for block in response.content:
                if block.type == "text":
                    assistant_message += block.text
            
            return assistant_message

        except Exception as e:
            self.logger.error(f"Anthropic Error: {e}")
            return ""


class GoogleProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = genai.Client(api_key=api_key)

    def _convert_history(self, messages: List[Message]) -> List[types.Content]:
        gemini_contents = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            gemini_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)]
                )
            )
        return gemini_contents

    def interact(self, history: ConversationHistory, model: str = "gemini-2.0-flash-thinking-exp", reasoning: bool = False, temperature: float = None) -> str:
        
        converted_messages = self._convert_history(history.messages)
        

        config_args = {}
        if temperature:
            config_args['temperature'] = temperature
            
        if reasoning:
            config_args['thinking_config'] = types.ThinkingConfig(include_thoughts=True)

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=converted_messages,
                config=types.GenerateContentConfig(**config_args)
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Google Error: {e}")
            return ""


class Chatbot:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        self.history = ConversationHistory()
        self._openai: Optional[OpenAIProvider] = None
        self._anthropic: Optional[AnthropicProvider] = None
        self._google: Optional[GoogleProvider] = None


    @property
    def openai(self) -> OpenAIProvider:
        if not self._openai:
            self._openai = OpenAIProvider(get_enviromental_variable("OPENAI_API_KEY"))
        return self._openai

    @property
    def anthropic(self) -> AnthropicProvider:
        if not self._anthropic:
            self._anthropic = AnthropicProvider(get_enviromental_variable("ANTHROPIC_API_KEY"))
        return self._anthropic

    @property
    def google(self) -> GoogleProvider:
        if not self._google:
            self._google = GoogleProvider(get_enviromental_variable("GEMINI_API_KEY"))
        return self._google

    @safe_operation(default_return="")
    def send_message(self, provider_name: str, message: str, **kwargs) -> str:
        """
        Unified method to send a message to any provider.
        
        :param provider_name: 'openai', 'anthropic', or 'google'
        :param message: The user input string
        :param kwargs: arguments passed to interact (model, reasoning, temperature)
        """

        self.history.add_user_message(message)

        provider: BaseLLMProvider
        if provider_name.lower() == "openai":
            provider = self.openai
        elif provider_name.lower() == "anthropic":
            provider = self.anthropic
        elif provider_name.lower() == "google":
            provider = self.google
        else:
            self.logger.error(f"Unknown provider: {provider_name}")
            return ""

        response_text = provider.interact(self.history, **kwargs)

        if response_text:
            self.history.add_assistant_message(response_text)
        
        return response_text

    def create_json_file(self, run_id: int) -> Path:
        """Creates a path for saving chat history."""

        from classes.db_manager import get_database 

        db = get_database()
        llm_id_str = db.run.get_column_value(run_id, RunSchema.llm_id)
        
        llm_name = "unknown_llm"
        if llm_id_str and llm_id_str != "0" and llm_id_str != "None":
            llm_name = db.llm.get_column_value(int(llm_id_str), LLMSchema.name)

        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
        filename = f"{llm_name}_chat_history_{timestamp}_{run_id}.json"

        relative_path = DATA_FOLDER / filename
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)

        return relative_path

    def save_history(self, run_id: int, return_path: bool = False) -> Optional[Path]:
        """Save the current conversation history to JSON."""
        filepath = self.create_json_file(run_id=run_id)
        
        data_to_save = {
            "meta": {"date": self.history.start_time},
            "conversation": self.history.to_dict()
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Chat history saved to {filepath}")
            
            if return_path:
                return filepath
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
            
        return None



_chatbot_instance = None

def get_chatbot() -> Chatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = Chatbot()
    return _chatbot_instance