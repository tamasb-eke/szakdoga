import anthropic, json, time
from openai import OpenAI, RateLimitError
from google import genai
from google.genai import types
from pathlib import Path
from datetime import datetime
from scripts.safe_operation import safe_operation
from scripts.basic_tools import DATA_FOLDER



_chatbot_instance = None
llm_messages = [
    {"date": datetime.now().strftime('%Y-%m-%d-%H-%M-%S')},
    {"messages": []}
]


class Chatbot:

    def __init__(self):
        from scripts.basic_tools import get_enviromental_variable
        
        self.chatgpt = Openai(api_key=get_enviromental_variable("OPENAI_API_KEY"))
        self.claude = Anthropic(api_key=get_enviromental_variable("ANTHROPIC_API_KEY"))
        self.gemini = Google(api_key=get_enviromental_variable("GEMINI_API_KEY"))

    def create_json_file(self, run_id: int) -> Path:
        """Creates a path for a .json that will store the results of the llm conversation
            
        Filename Pattern:
            'llm_name'_chat_history_'YYYY-MM-DD-HH-MM-SS'_'run_id'.json
            Example: gpt4_chat_history_2025-05-05-20-30_123.json 
        """
        from classes.db_manager import get_database

        db = get_database()
        llm_name = db.llm.get_name(db.run.get_(run_id, "llm_id"))

        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
        filename = f"{llm_name}_chat_history_{timestamp}_{run_id}.json"

        relative_path = DATA_FOLDER / filename
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)

        return relative_path

    def save_json(self, run_id:int, data:list[dict] = llm_messages, return_path:bool=False) -> None|Path:
        """Save a Python object to a JSON file."""
        from scripts.logger.logger import get_logger

        logger = get_logger()
        filepath = self.create_json_file(run_id=run_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"llm_messages was saved successfully to {filepath}")

        if return_path:
            return filepath
        return None


class Openai:
    def __init__(self, api_key:str):
        self.client = OpenAI(api_key=api_key)
        self.base_url = "https://api.openai.com/v1"
        self.api_key = api_key
        
    @safe_operation(default_return="")


    def interact(self, message: str, model: str = "o1-pro", reasoning: bool = False, temperature: float = None) -> str:
        """A function that makes the call, handles rate limits, and gets the answer from the LLM"""

        llm_messages[1]["messages"].append({"role": "user", "content": message})
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=llm_messages[1]["messages"],
                    extra_body={"reasoning": reasoning} if reasoning else None,
                    temperature=temperature if temperature is not None else None
                )
                
                reply = response.choices[0].message.content
                llm_messages[1]["messages"].append({"role": "assistant", "content": reply})
                return reply

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Rate limit hit. Waiting {base_delay} seconds before retry...")
                time.sleep(base_delay)
                base_delay *= 2 
                
        return ""
    

class Anthropic:

    def __init__(self, api_key:str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "claude-3-opus-20240229", reasoning: bool = False, temperature: float = 1.0) -> str:
        """A function that makes the callig, and getting the answer from the LLM"""
        
        llm_messages[1]["messages"].append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=llm_messages[1]["messages"],
            thinking={
                "type": "enabled",
                "budget_tokens": 1000
            } if reasoning else {"type": "disabled"},
            temperature=temperature if temperature != 1.0 else 1.0
        )

        assistant_message = ""
        for block in response.content:
            if block.type == "text":
                assistant_message += block.text
        
        llm_messages[1]["messages"].append({"role": "assistant", "content": assistant_message})

        return assistant_message
    

class Google:

    def __init__(self, api_key:str):
        self.client = genai.Client(api_key=api_key)
        self.api_key = api_key

            
    def convert_dictionary_to_contect(self, messages:list) -> list:

        gemini_contents = []

        for msg in messages:

            gemini_contents.append(
                types.Content(
                    role = "model" if msg["role"] == "assistant" else "user",
                    parts = [
                        types.Part.from_text(text=msg["content"])
                    ]
                )
            )

        return gemini_contents

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "gemini-2.5-flash", reasoning: bool = False, temperature:float = None) -> str:
        """A function that makes the callig, and getting the answer from the LLM"""

        llm_messages[1]["messages"].append({"role": "user", "content": message})
        thinking_budget = 1024 if reasoning else 0
        converted_messages = self.convert_dictionary_to_contect(llm_messages[1]["messages"])

        response = self.client.models.generate_content(
            model=model, 
            contents=converted_messages,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                temperature=temperature if temperature else None
            ),
        )

        llm_messages[1]["messages"].append({"role": "assistant", "content": response.text})

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