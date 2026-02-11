from classes.db_manager import get_database
from pathlib import Path
from model.schemas import LLMSchema, TaskSchema, AnswerSchema
from typing import List
from scripts.basic_tools import clear_console
from scripts import safe_operation
from classes.api import Chatbot, get_chatbot
from scripts.question_validation import syntactic_validation, semantic_validation
from scripts.logger.logger import get_logger

class ChatbotCommunication():

    def __init__(self):
        self.llm:LLMSchema = None
        self.task:TaskSchema = None
        self.number_of_questions = None
        self.db = get_database()

    def _map_db_name_to_provider(self) -> str:
        """Maps database LLM names to Chatbot provider keys."""
        name = self.llm.name.lower()
        if "gpt" in name or "openai" in name:
            return "openai"
        elif "claude" in name or "anthropic" in name:
            return "anthropic"
        elif "gemini" in name or "google" in name:
            return "google"
        return "unknown"

    def get_user_configuration(self) -> None:
            """
            Get all available llm, and task
            """

            llms: List[LLMSchema] = self.db.llm.get_all()
            tasks: List[TaskSchema] = self.db.task.get_all()
            llm_map = {llm.id: llm for llm in llms}
            task_map = {task.id: task for task in tasks}

            while True:
                clear_console() 
                print("--- ChatBot Configuration Setup ---")

                llm_input = input("Enter LLM ID: ").strip()
                if not llm_input.isdigit() or int(llm_input) not in llm_map:
                    print(f"Invalid LLM ID: {llm_input}. Press Enter to retry.")
                    input()
                    continue
                
                task_input = input("Enter Task ID: ").strip()
                if not task_input.isdigit() or int(task_input) not in task_map:
                    print(f"Invalid Task ID: {task_input}. Press Enter to retry.")
                    input()
                    continue

                count_input = input("Enter number of questions (default 100): ").strip()
                if not count_input:
                    count_input = 100
                elif not count_input.isdigit():
                    print(f"Invalid number: {count_input}. Press Enter to retry.")
                    input()
                    continue

                self.llm = llm_map[int(llm_input)]
                self.task_id = task_map[int(task_input)]
                self.number_of_questions = int(count_input)
                break




@safe_operation()
def manual_game_conversation(chatbot: Chatbot, provider: str, model: str, reasoning: bool) -> None:
    """
    Loops until the Chatbot confirms it understands the game rules.
    """
    bot_response = ""
    success_phrases = ["I understand the game", "I understand the game."]

    while bot_response.strip() not in success_phrases:
        user_input = input("\n[USER]: ").strip()

        if Path(user_input).is_file(): 
            with open(Path(user_input), 'r', encoding='utf-8') as f:
                user_input = f.read()

        bot_response = chatbot.send_message(
            provider_name=provider,
            message=user_input,
            model=model,
            reasoning=reasoning
        )
        
        print(f"[Chatbot]: {bot_response}")

        if bot_response.strip() in success_phrases:
            return

@safe_operation()
def run_chat_session(
        run_id: int, 
        chatbot: Chatbot,
        provider: str, 
        model: str, 
        reasoning: bool, 
        number_of_questions: int
    ) -> None:
    """
    Orchestrates the actual questioning loop.
    """
    db = get_database()
    logger = get_logger(__name__)
    print('\n--- Game Rule Initialization ---')
    print("Please provide the game description (or path to a .txt file).")
    manual_game_conversation(chatbot, provider, model, reasoning)


    print(f"\n--- Starting {number_of_questions} Questions ---")
    questions = db.create_questions(amount=number_of_questions)

    for i, question in enumerate(questions, 1):
        prompt = f"sourceWord: {question['sourceWord']}, targetWord: {question['targetWord']}."
        
        answer = chatbot.send_message(
            provider_name=provider,
            message=prompt,
            model=model,
            reasoning=reasoning
        )
        
        if syntactic_validation(answer):
            validation_message = semantic_validation(answer)
            
            db.answer.insert(
                AnswerSchema(
                    run_id=run_id,
                    chain=answer,
                    chain_length=len(answer.split('-')),
                    sourceword=question['sourceWord'],
                    targetword=question['targetWord'],
                    validation_message=validation_message
                )
            )
            print(f"({i}/{number_of_questions}) {question['sourceWord']} -> {question['targetWord']} | Result: {validation_message}")
        
        else:
            manual_game_conversation(chatbot, provider, model, reasoning)


    print('\n--- Conversation Finished ---')
    json_path = chatbot.save_history(run_id=run_id, return_path=True)
    
    if json_path:
        db.run.update_field(run_id=run_id, column='json_path', new_value=str(json_path))
        db.run.update_field(run_id=run_id, column='successful', new_value='True')
        db.evaluation(run_id=run_id)
    else:
        logger.error("Failed to save conversation history JSON.")

def start_conversation() -> None:
    """
    Main entry point: Setup -> Database -> Chat Loop
    """
    
    conversation: ChatbotCommunication = ChatbotCommunication()
    conversation.get_user_configuration()
    
    db = get_database()

    db.run.insert(
        llm_id=conversation.llm.id,
        task_id=conversation.task.id,
    )
    current_run_id = db.run.get_latest_id()
    chatbot = get_chatbot()
    
    run_chat_session(
        run_id=current_run_id,
        chatbot=chatbot,
        provider=conversation._map_db_name_to_provider(),
        model=conversation.llm.model,
        reasoning=conversation.llm.reasoning,
        number_of_questions=conversation.number_of_questions
    )

    input("\nSession complete. Press any key to return to main menu...")