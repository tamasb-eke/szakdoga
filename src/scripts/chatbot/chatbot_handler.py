from classes.api import get_chatbot, Google, Anthropic, Openai
from scripts.safe_operation import safe_operation
from classes.db_manager import get_database
from scripts.basic_tools import print_table, clear_console
from scripts.question_validation import syntactic_validation, semantic_validation
from itertools import zip_longest
from typing import Union


def initialize_chatbot_communication():
    """"""

    db = get_database()

    llms = db.llm.get_all_()
    tasks = db.task.get_all()

    llm = [[r[0],r[1]['name'], r[1]['model'], r[1]['reasoning']] for r in llms.items()]    
    task = [[r[0],r[1]['name'], r[1]['description']] for r in tasks.items()]

    combined = [
        l + t 
        for l, t in zip_longest(llm, task, fillvalue=[None, None, None])
    ]
    clear_console()


    while True:
        
        print("Please give the following parameters:")
        print("1. Which LLM dou you want to use")
        print("2. Which task do you currently doing")
        print("3. How many question do you want to make? (default is 100)")
        print("Please only give the LLM and Task ID")
        print("\n           Currently available in database")
        
        print_table(
            header_names=['LLM ID','LLM name', 'LLM model', 'LLM reasoning', 'Task ID', 'Task name', 'Task description'],
            datas=combined
        )

        llm_id = int(input("\nPlease give LLM ID: "))
        if not llm_id in llms:
            clear_console()
            print(f"\nThe given llm_id ({llm_id}) was not recognisable. Please choose another one.\n")
            continue
        task_id = int(input("Please give Task ID: "))
        if not task_id in tasks:
            clear_console()
            print(f"\nThe given task_id ({task_id}) was not recognisable. Please choose another one.\n")
            continue
        number_of_questions = input("Enter a number: ")
        if not number_of_questions.isdigit():
            clear_console()
            print(f"\nThe given number of question ({number_of_questions}) was not a number. Please Try again.\n")
            continue

        else:
            return llm_id, task_id, int(number_of_questions)
    

@safe_operation()
def chat_llm_api(run_id:int, chatbot:Union[Openai, Anthropic, Google], model:str, reasoning:bool = False, number_of_questions: int = 100) -> None:
    """
    A function that handles the chatbot conversation
    """

    db = get_database()

    # First conversation about the game rules
    while answer != "I understand the game" and answer != "I understand the game.":
        game_description = input("[USER]: ")

        answer = chatbot.interact(
            message=game_description,
            model=model,
            reasoning=reasoning
        )

        print(f"[Chatbot]: {answer}")
        
    #Automatic conversation
    questions = db.create_questions(amount=number_of_questions)
    i = 1
    for question in questions:
        
    
        answer = chatbot.interact(
            message=f"sourceWord: {question['sourceWord']}, targetWord: {question['targetWord']}. ",
            model=model,
            reasoning=reasoning
        )
                
        if syntactic_validation(answer):
            validation_message = semantic_validation(answer)
            
            db.answer.insert(
                run_id=run_id,
                chain=answer,
                chain_length= len(answer.split('-')),
                sourceword=question['sourceWord'],
                targetword=question['targetWord'],
                validation_message=validation_message
            )

            print(f"{i}/{number_of_questions}) source word: {question['sourceWord']}, target word: {question['targetWord']}, validation {validation_message}")


        else:
            while answer != "I understand the game" and answer != "I understand the game.":
                print(f"[Chatbot]: {answer}")
                game_description = input("[USER]: ")
                answer = chatbot.interact(
                    model=model,
                    message=game_description, 
                    reasoning=reasoning
                )
                print(f"[Chatbot]: {answer}")
            

    chat = get_chatbot()
    json_path = chat.save_json(run_id=run_id, return_path=True)
    db.run.update(run_id=run_id, value=json_path, json_path=True)
    db.evaluation(run_id=run_id)


def start_conversation() -> None:
    """First it initialize the running parameters for the conversation, then makes an LLM conversation interface"""

    llm_id, task_id, number_of_questions = initialize_chatbot_communication()
    db = get_database()
    
    chat_instance = db.llm.get_(llm_id=llm_id, column="name")

    if chat_instance == "chatGPT":
        chatbot = get_chatbot()
        ch = chatbot.chatgpt
    elif chat_instance == "claude":
        chatbot = get_chatbot()
        ch = chatbot.claude
    elif chat_instance == "gemini":
        chatbot = get_chatbot()
        ch = chatbot.gemini

    db.run.insert(
        llm_id = llm_id,
        task_id = task_id,
    )

    chat_llm_api(
        run_id=db.run.get_latest_id(),
        chatbot = ch,
        model = db.llm.get_(llm_id=llm_id, column="model"),
        reasoning = db.llm.get_(llm_id=llm_id, column="reasoning"),
        number_of_questions=number_of_questions
    )

    input("\nPlease press any key to return to main menu")