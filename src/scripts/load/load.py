import json
import re
from pathlib import Path
from datetime import datetime
from scripts.question_validation import syntactic_validation, semantic_validation
from scripts.logger.logger import get_logger
from scripts.safe_operation import safe_operation
from scripts.basic_tools import ROOT, load_data, clear_console, SAVED_CONVERSATION_PATH
from classes.db_manager import get_database
from scripts.load.load_helper import (
    convert_date, 
    clear_unesecarry, 
    get_manually_collected_json_path,
    get_file_from_user, 
    get_llm_id_from_user, 
    get_task_id_from_user
)


def extract_word_chain(string: str) -> str | None:
    """
    Extracts the wordchain. It is usefull for .txt loading
    Returns the first match found, or None if no such pattern exists.
    """

    pattern = r'\b(?:[A-Za-z]+-)+[A-Za-z]+\b'
    
    match = re.search(pattern, string)
    return match.group(0) if match else None


@safe_operation()
def load_json_to_db(file_path:Path, run_id:int, date:str) -> None:
    """
    This is just a very small function that can be used as a modul, where around it you can create any kind of 
    file_path processing, run_id creation, or date customization.

    :param file_path: Path to the .json that holds the datas
    :param run_id: The ID of the run you want to insert
    :param date: The date of the file
    """
    data = load_data(file_path)
    llm_messages_loader(
        llm_messages=data,
        run_id=run_id,
        date=date
    )

@safe_operation()
def to_db_from_txt(file_path:Path, run_id:int) -> None:
    """This function loads the datas into the database from a .txt"""
    
    logger = get_logger()
    db = get_database()
    inserted = 0

    with open(file_path, 'r') as f:
        for line in f:
            word_chain = extract_word_chain(line.strip())
            if word_chain:
                db.answer.insert(
                    run_id=run_id,
                    chain=word_chain,
                    chain_length=len(word_chain.split('-')),
                    sourceword=word_chain.split('-')[0],
                    targetword=word_chain.split('-')[-1],
                    validation_message=semantic_validation(word_chain),
                )
                inserted += 1

        logger.info(f"Loaded {inserted} line of words from {file_path}")

@safe_operation()
def llm_messages_loader(llm_messages:list[dict], run_id:int = None, date:str = datetime.now().strftime('%Y%m%d_%H%M%S')):
    """
    This function basically get the llm_messages and the it load to db. It can be used after a chatbot conversation ended and
    you want to save the results to database.
    
    :param llm_meesages: The variable that stores the conversation between the LLM and the user
    :param run_id: The run_id that you want to save to it. If no one is given then the default is the latest run.
    :param date: The date of the exportation to database. (By default is the current date)
    """

    logger = get_logger()
    db = get_database()

    if not run_id:
        run_id = db.run.get_latest_id()

    for content in (item["say"] for item in llm_messages if item["role"] == "Response"):

        if not syntactic_validation(content):
            logger.warning(f"Incorrect syntactic for wordchain: {content}") #can happen because llm gives not just answers
            continue

        validation_message = semantic_validation(content)

        db.answer.insert(
            run_id = run_id,
            chain = content,
            chain_length = len(content.split('-')),
            sourceword = content.split('-')[0],
            targetword = content.split('-')[-1],
            date = date,
            validation = validation_message
        )

@safe_operation()
def study_results_to_db() -> None:
    """
    This function is loading from the research result's 'word_navigation_game_export.json' file
    It is usefull if the database is corrupted or needs a reload
    """
    
    logger = get_logger(__name__)
    json_path = Path(ROOT/'data/other_data_files/word_navigation_game_export.json')
    db = get_database()

    if not json_path.exists():
        raise FileNotFoundError(f"Path to word_navigation_game_export.json. It should have a path: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)['GameLogs']

        for user_id in data:
            games_played = 0

            logger.info("-------------------------------------------------------------------------")
            db.run.insert(
                person_id = user_id,
                task_id = 2,
                json_path = str(json_path),
            )
            run_id = db.run.get_latest_id()
            
            for id_, game in data[user_id].items():
                if game['chain_length'] < 2:
                    continue

                if db.human.already_answered(human_id=user_id, solution=game['chain']):
                    logger.info(f"{user_id} already answered {game['chain']}")
                    continue

                if db.human.already_in_db(human_id=user_id): #in case if we ran into the same person again later in the file
                    run_id = db.run.get_id(user_id)
                    games_played = db.human.get_(human_id=user_id, column="games_played")

                games_played += 1
                validation = semantic_validation(game['chain'].replace(' ', '-'))
                formatted_date = convert_date(game['date'])

                db.answer.insert(
                    run_id = run_id,
                    chain = game['chain'],
                    chain_length = game['chain_length'],
                    sourceword = game['sourceWord'],
                    targetword = game['targetWord'],
                    date = formatted_date,
                    validation_message = validation
                )

            if games_played > 0:
                db.human.insert(
                    human_id = user_id,
                    games_played = games_played
                )

                db.run.update(run_id = run_id, value = 'True')

    clear_unesecarry()

@safe_operation()
def older_results_to_db(result_path:Path|str) -> None:
    """"
    Load the answers from an earlier chatbot results. The results are stored in data/chatbor_result folder
    
    :param result_path: Path to the saved chatbot conversation. Their place is at: data/chatbor_result folder

    IMPORTANT: It is usefull for chatbot conversation. If you want to save manually collected results, please use: manually_collected_to_db()
    """
    if not result_path:
        return

    db = get_database()

    if isinstance(result_path, str):
        result_path = Path(result_path)

    if not result_path.exists():    
        raise FileNotFoundError(f"The given path: {result_path} was ")

    filename = result_path.name
    run_id = filename.split('_')[-1]
    date = filename.split('_')[-2]
    llm_id = db.run.get_(run_id, "llm_id")
    task_id = db.run.get_(run_id, "task_id")

    db.run.insert(
        llm_id = llm_id,
        person_id = None,
        task_id = task_id,
        json_path = result_path,
    )

    run_id = db.run.get_latest_id()

    load_json_to_db(file_path=result_path, run_id=run_id, date=date)

    db.run.update(run_id=run_id, value='True')

@safe_operation()
def load_manual_datas_json():
    """
    This function helps the user decide which .json should be saved. The saved json's are in 'data/saved_conversation'. 
    Also the .json filename has to be a structure like this:

    Filename Pattern:
        'llm_name'_chat_history_'YYYY-MM-DD-HH-MM'_'run_id'.json
        Example: gpt4_chat_history_2025-05-05-20-30_123.json 

    Run_id will be generated automatically, and the file will be renamed according to it
    """
    db = get_database()
    directory = Path(SAVED_CONVERSATION_PATH)
    if not directory.exists():
        raise NotADirectoryError(f"The {SAVED_CONVERSATION_PATH} folder does not exists!")

    clear_console()
    filepath = directory / get_file_from_user(directory)
    if not filepath.exists():
        return
    llm_id = get_llm_id_from_user()
    if not llm_id:
        return
    task_id = get_task_id_from_user()
    if not task_id:
        return

    db.run.insert(
        llm_id=llm_id,
        task_id=task_id,
        json_path=str(filepath)
    )
    run_id = db.run.get_latest_id()

    date = datetime.now().strftime("%Y-%m-%d-%H-%M")

    load_json_to_db(
        file_path=filepath,
        run_id=run_id,
        date=date
    )

    new_filename = f"{db.llm.get_(llm_id=llm_id, column='name')}_chat_history_{date}_{run_id}.json"
    filepath.rename(SAVED_CONVERSATION_PATH / new_filename)
    db.run.update(run_id=run_id, value=(SAVED_CONVERSATION_PATH / new_filename), json_path=True)

    db.run.update(run_id=run_id, value='True')


def reload_older():
    """A function that calls the human result loader or the older result loader"""

    choosable_tasks = {'1', '2', 'e'}
    

    while True:
        clear_console()
        print("There is two kind of reload you can do. First is reload the results of the human study from .json. " \
        "The Second one is reloading already saved (.json) results\n")
        print("1) Reload human study result")
        print("2) Reload saved game results")
        print("e) Exit")
        
        
        task = input("Please choose: ")
        if not task in choosable_tasks:
            print("\nThe given number was not recognisable. Please choose another one.\n")
        else:
            match task:
                case '1':
                    study_results_to_db()
                case '2':
                    older_results_to_db(result_path=get_manually_collected_json_path())
                case 'e':
                    break


@safe_operation()
def load_manual_datas_txt():
    """
    This function helps the user decide which .txt should be saved. The saved txt's are in 'data/saved_conversation'. 
    Also the .txt filename has to be a structure like this:

    Filename Pattern:
        'llm_name'_chat_history_'YYYY-MM-DD-HH-MM'_'run_id'.json
        Example: gpt4_chat_history_2025-05-05-20-30_123.json 

    Run_id will be generated automatically, and the file will be renamed according to it
    """
    db = get_database()
    directory = Path(SAVED_CONVERSATION_PATH)
    if not directory.exists():
        raise NotADirectoryError(f"The {SAVED_CONVERSATION_PATH} folder does not exists!")

    clear_console()
    filepath = directory / get_file_from_user(directory, extension='.txt')
    if not filepath.exists():
        return
    llm_id = get_llm_id_from_user()
    if not llm_id:
        return
    task_id = get_task_id_from_user()
    if not task_id:
        return

    db.run.insert(
        llm_id=llm_id,
        task_id=task_id,
        json_path=str(filepath)
    )
    run_id = db.run.get_latest_id()

    to_db_from_txt(
        file_path=filepath,
        run_id=run_id,
    )

    date = datetime.now().strftime("%Y-%m-%d-%H-%M")
    new_filename = f"{db.llm.get_(llm_id=llm_id, column='name')}_chat_history_{date}_{run_id}.txt"
    filepath.rename(SAVED_CONVERSATION_PATH / new_filename)
    db.run.update(run_id=run_id, value=(SAVED_CONVERSATION_PATH / new_filename), json_path=True)

    db.run.update(run_id=run_id, value='True')