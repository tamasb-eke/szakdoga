from scripts.safe_operation import safe_operation
from classes.db_manager import get_database
from dateutil import parser, tz
from scripts.basic_tools import ROOT, clear_console
from pathlib import Path

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
    }
    
    dt = parser.parse(date, tzinfos=tz_mapping)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_manually_collected_json_path() -> Path:
    """
    Get the path to the manually collected .json
    It lists all the .json files in the 'data/saved_conversation' folder, and the user can choose between them. 
    """
    
    db = get_database()
    folder_paths = db.run.get_all_(column="json_path", unique=True)
    clear_console()

    for i, file in enumerate(folder_paths, start=1):
        print(f"{i}) {Path(file).name}")
    print("e) Exit")
    
    while True:
        try:
            choice = input("Please choose a number: ")
            if choice == 'e':
                return 
            
            if 1 <= int(choice) <= len(folder_paths):
                return Path(folder_paths[choice - 1])
            else:
                print(f"Please enter a number between 1 and {len(folder_paths)}")
        except ValueError:
            print("Please enter a valid number")