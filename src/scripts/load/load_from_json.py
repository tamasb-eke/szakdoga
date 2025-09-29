import json
from pathlib import Path
from scripts.logger.logger import get_logger, get_log_path
from scripts.safe_operation import safe_operation
from scripts.basic_tools import ROOT
from classes.db_manager import get_database
from scripts.question_validation import semantic_validation
from dateutil import parser, tz

@safe_operation()
def load_from_initial_json_to_database() -> None:
    """
    This function is loading from the research result's 'word_navigation_game_export.json' file
    It is usefull if the database is corrupted or needs a reload
    """
    
    logger = get_logger(__name__)
    json_path = Path(ROOT/'data/game_guides/word_navigation_game_export.json')
    db = get_database()

    if not json_path.exists():
        logger.error(f"Path to word_navigation_game_export.json is invalid -> {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)['GameLogs']

        for user_id in data:
            games_played = 0

            logger.info("-------------------------------------------------------------------------")
            db.run.insert(
                person_id = user_id,
                task_id = 2,
                json_path = str(json_path),
                log_path = str(get_log_path())
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


def clear_unesecarry():
    """
    A function that deletes all unnesecarry Answers, and Humans
        if:
            - Those Run's where the given human has not played a single game (from Run table)
            - The Human games_played < 100 (from Human table)
            - The answers where the answer has no llm_id, or human_id. Basically has no owner
    
    """
    threshold = 100
    db = get_database()
    
    db.run.delete_less_than(amount=threshold)   # 1
    db.human.delete_less_than(amount=threshold) # 2
    db.answer.delete_ownerless()                # 3

@safe_operation()
def convert_date(date:str) -> str:
    """Convert timezone heavy format to database format"""
    tz_mapping = {
        "CET": tz.gettz("Europe/Paris"),
        "CEST": tz.gettz("Europe/Paris"),
        "BST": tz.gettz("Europe/London"),  
        "CDT": tz.gettz("America/Chicago"), 
        "EDT": tz.gettz("America/New_York"),
        "EST": tz.gettz("America/New_York"),
        "PDT": tz.gettz("America/Los_Angeles"),
        "PST": tz.gettz("America/Los_Angeles"),
        # add more if you encounter them
    }
    
    dt = parser.parse(date, tzinfos=tz_mapping)
    return dt.strftime("%Y-%m-%d %H:%M:%S")