from scripts.safe_operation import safe_operation
from classes.db_manager import get_database
from dateutil import parser, tz
from scripts.basic_tools import ROOT, clear_console
from pathlib import Path
from scripts.basic_tools import print_table
from scripts.visualize.viz import visualizer

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

def get_llm_id_from_user() -> int:
    """This function is getting a llm id from the user input"""

    db = get_database()
    llm = db.llm.get_all_()
    datas = [[r[0],r[1]['name'], r[1]['model'], r[1]['reasoning']] for r in llm.items()]
    while True:
        print(f"\nPlease also give a LLM ID")
        print("You can exit using 'e'")
        print("\n           Currently in the database")
        print_table(
            header_names=['ID', 'Name', 'Model', 'Reasoning'],
            datas=datas
        )

        llm_id = input("\nPlease choose a LLM ID: ")
        if llm_id == 'e':
            return
        elif db.llm.get_(llm_id=int(llm_id), column='id') == "":
            clear_console()
            print(f"\nThe given LLM ID ({llm_id}) was not recognisable. Please choose another one.\n")
            continue

        return llm_id
    

def get_json_file_from_user(directory_path:Path) -> Path:
    """This function is getting a json path from the user input"""

    datas = [[i, filename.name] for i, filename in enumerate(directory_path.glob('*.json'), start=1)]

    while True:
        print(f"You can load any .json that has not been yet exported and it is stored at {directory_path}")
        print("You can exit using 'e'")
        print("\n           Currently in the folder")
        print_table(
            header_names=['Number', 'Filename'],
            datas=datas
        )

        number = input("\nPlease give the corresponding number for the file: ")
        if number == 'e':
            return 'None'
        
        elif int(number) <= len(datas):
            clear_console()
            print(f"\nThe given number ({number}) was not recognisable. Please choose another one.\n")
            continue
        
        return Path(datas[number][1])
    
def get_task_id_from_user() -> int:
    """This function is getting a task id from the user input"""

    db = get_database()
    llm = db.task.get_all()
    datas = [[r[0],r[1]['name'], r[1]['description']] for r in llm.items()]
    while True:
        print(f"\nPlease give a Task ID")
        print("You can exit using 'e'")
        print("\n           Currently in the database")
        print_table(
            header_names=['ID', 'Name', 'Description'],
            datas=datas
        )

        task_id = input("\nPlease choose a Task ID: ")
        if task_id == 'e':
            return
        elif db.task.get_(task_id=int(task_id), column='id') == "":
            clear_console()
            print(f"\nThe given Task ID ({task_id}) was not recognisable. Please choose another one.\n")
            continue

        return task_id
    
def get_minimal_frequences():
    """"""
    while True:
        print(f"\nPlease provide a number for minimal frequences.")
        print("You can exit using 'e'")

        frequences = input("\nMinimal frequences: ")
        if frequences == 'e':
            return
        elif frequences.isdigit():
            return int(frequences)
        else:
            clear_console()
            print(f"The given parameter ({frequences}) is not a positive number. Please try again")


@safe_operation()
def select_result():
    """This function helps to choose the user which older run should be evaluated"""

    db = get_database()
    datas = db.run.get_all_(readable=True)
    clear_console()

    while True:
        
        print("You can evaluate any loaded data that is in the database")
        print("You can exit using 'e'")
        print("\n           Currently available in database")
        print_table(
            header_names=['Run ID','Date', 'LLM name', 'LLM model', 'LLM reasoning', 'Task name', 'Task description', 'Json path', 'Successfull'],
            datas=datas
        )

        run_id = input("\nPlease give Run ID: ")
        if run_id == 'e':
            return
        elif db.run.get_(run_id=int(run_id), column='id') == "":
            clear_console()
            print(f"\nThe given Run ID ({run_id}) was not recognisable. Please choose another one.\n")
            continue

        else:
            break
    
    clear_console()
    
    db.evaluation(run_id=run_id)

    print("\n\nDo you want to visualize the results? (y) Yes (n) No")
    visualize = input("Y\N: ").lower()
    if visualize in ['y', 'yes']:
        clear_console()
        visualizer(run_id=run_id)