from typing import Literal

RunColumn = Literal["id","llm_id", "person_id", "task_id", "json_path", "date", "successful"]
AnswerColumn = Literal["id", "run_id", "chain", "chain_length", "date", "sourceWord", "targetWord", "validation"]
HumanColumn = Literal["id", "games_played"]
LLMColumn = Literal["id", "name", "model", "reasoning"]
TaskColumn = Literal["id", "name", "description"]



