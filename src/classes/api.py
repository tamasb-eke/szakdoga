from openai import OpenAI
from google import genai
from google.genai import types
import anthropic
from scripts.basic_tools import llm_messages
from scripts.safe_operation import safe_operation

_chatbot_instance = None

class Chatbot:

    def __init__(self):
        from scripts.basic_tools import get_enviromental_variable
        
        self.chatgpt = Openai(api_key=get_enviromental_variable("OPENAI_API_KEY"))
        self.claude = Anthropic(api_key=get_enviromental_variable("ANTHROPIC_API_KEY"))
        self.gemini = Google(api_key=get_enviromental_variable("GEMINI_API_KEY"))



class Openai:
    def __init__(self, api_key:str):
        self.client = OpenAI(api_key=api_key)
        self.base_url = "https://api.openai.com/v1"
        self.api_key = api_key
        
    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "o1-pro", reasoning: bool = False) -> str:
        """A function that """

        llm_messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=model,
            messages=llm_messages,
            extra_body={"reasoning": reasoning} if reasoning else None
        )

        reply = response.choices[0].message["content"]
        llm_messages.append({"role": "assistant", "content": reply})

        return reply

class Anthropic:

    def __init__(self, api_key:str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "claude-3-opus-20240229", reasoning: bool = False) -> str:

        llm_messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=llm_messages,
            thinking={
                "type": "enabled",
                "budget_tokens": 1000
            } if reasoning else None,
        )

        llm_messages.append({"role": "assistant", "content": response.content})

        return response.content

class Google:

    def __init__(self, api_key:str):
        self.client = genai.Client(api_key=api_key)
        self.api_key = api_key

    @safe_operation(default_return="")
    def interact(self, message: str, model: str = "gemini-2.5-flash", reasoning: bool = False) -> str:
        

        llm_messages.append({"role": "user", "content": message})
        thinking_budget = 1024 if reasoning else 0

        response = self.client.models.generate_content(
            model=model, 
            contents=llm_messages,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
            ),
        )

        llm_messages.append({"role": "assistant", "content": response.text})

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