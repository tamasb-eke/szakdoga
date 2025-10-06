import json
from pathlib import Path
from datetime import datetime
from scripts.question_validation import syntactic_validation, semantic_validation
from scripts.logger.logger import get_logger
from scripts.safe_operation import safe_operation
from scripts.basic_tools import ROOT, load_data, clear_console
from classes.db_manager import get_database
from scripts.load.load_helper import convert_date, clear_unesecarry, get_manually_collected_json_path


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
            logger.error(f"Incorrect syntactic for wordchain: {content}") #can happen because llm gives not just answers
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

                db.run.update(
                    run_id = run_id,
                    value = 'True'
                )

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


    data = load_data(result_path)
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

    llm_messages_loader(
        llm_messages=data,
        run_id=run_id,
        date=date
    )


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