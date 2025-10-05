from openai import OpenAI
from google import genai
from google.genai import types
import anthropic
from scripts.safe_operation import safe_operation
from pathlib import Path
import json
from datetime import datetime

_chatbot_instance = None
llm_messages = [
    {"date": datetime.now().strftime('%Y-%m-%d-%H-%M-%S')},
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}]}
]
data_folder = Path("data/chatbot_results")

class Chatbot:

    def __init__(self):
        from scripts.basic_tools import get_enviromental_variable
        
        self.chatgpt = Openai(api_key=get_enviromental_variable("OPENAI_API_KEY"))
        self.claude = Anthropic(api_key=get_enviromental_variable("ANTHROPIC_API_KEY"))
        self.gemini = Google(api_key=get_enviromental_variable("GEMINI_API_KEY"))

    def create_json_file(self, run_id: int) -> Path:
        """Creates a path for a .json that will store the results of the llm conversation
            
        Filename Pattern:
            <llm_name>_chat_history_<YYYY-MM-DD-HH-MM-SS>_<run_id>.json
            Example: gpt4_chat_history_2025-05-05-20-30-00_123.json 
        """
        from classes.db_manager import get_database

        db = get_database()
        llm_name = db.llm.get_name(db.run.get_(run_id, "llm_id"))

        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        filename = f"{llm_name}_chat_history_{timestamp}_{run_id}.json"

        relative_path = data_folder / filename
        data_folder.mkdir(parents=True, exist_ok=True)

        return relative_path


    def save_json(self, data:list[dict], run_id:int):
        """Save a Python object to a JSON file."""
        from scripts.logger.logger import get_logger

        logger = get_logger()
        filepath = self.create_json_file(run_id=run_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"llm_messages was saved successfully to {filepath}")



class Openai:
    def __init__(self, api_key:str):
        self.client = OpenAI(api_key=api_key)
        self.base_url = "https://api.openai.com/v1"
        self.api_key = api_key
        
    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "o1-pro", reasoning: bool = False) -> str:
        """A function that """

        llm_messages[1]["messages"].append({"role": "Promt", "say": message})

        response = self.client.chat.completions.create(
            model=model,
            messages=llm_messages,
            extra_body={"reasoning": reasoning} if reasoning else None
        )

        reply = response.choices[0].message["content"]
        llm_messages[1]["messages"].append({"role": "Response", "say": reply})

        return reply

class Anthropic:

    def __init__(self, api_key:str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "claude-3-opus-20240229", reasoning: bool = False) -> str:

        llm_messages[1]["messages"].append({"role": "Prompt", "say": message})

        response = self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=llm_messages,
            thinking={
                "type": "enabled",
                "budget_tokens": 1000
            } if reasoning else None,
        )

        llm_messages[1]["messages"].append({"role": "Response", "say": response.content})

        return response.content

class Google:

    def __init__(self, api_key:str):
        self.client = genai.Client(api_key=api_key)
        self.api_key = api_key

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "gemini-2.5-flash", reasoning: bool = False) -> str:
        

        llm_messages[1]["messages"].append({"role": "Prompt", "say": message})
        thinking_budget = 1024 if reasoning else 0

        response = self.client.models.generate_content(
            model=model, 
            contents=llm_messages,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
            ),
        )

        llm_messages[1]["messages"].append({"role": "Response", "say": response.text})

        return response.text


def get_chatbot() -> Chatbot:
    """
    Get the global database instance.
    Creates it if it doesn't exist yet.
    """
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = Chatbot()
    return _chatbot_instance