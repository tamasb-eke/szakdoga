from scripts.safe_operation import safe_operation
from classes.db_manager import Database
from dateutil import parser, tz
from scripts.basic_tools import clear_console
from pathlib import Path
from scripts.basic_tools import print_table, load_data
from model.validation import Validation
from logging import Logger


class LoadHelper:
    def __init__(self, logger:Logger, db:Database):
        self.logger = logger
        self.db = db

    @staticmethod
    def clear_unesecarry(db:Database, threshold:int=100):
        """
        A function that deletes all unnesecarry Answers, and Humans
            if:
                - Those Run's where the given human has not played a single game (from Run table)
                - The Human games_played < threshold (from Human table)
                - The answers where the answer has no llm_id, or human_id. Basically has no owner
        """
        db.run.delete_less_than(amount=threshold)   # 1
        db.human.delete_less_than(amount=threshold) # 2
        db.answer.delete_ownerless()                # 3

    @safe_operation()
    @staticmethod
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

    @staticmethod
    def get_manually_collected_json_path(db:Database) -> Path:
        """
        Get the path to the manually collected .json
        It lists all the .json files in the 'data/saved_conversation' folder, and the user can choose between them. 
        """
        clear_console()
        folder_paths = db.run.get_values_by_column(column="json_path", unique=True)

        for i, file in enumerate(folder_paths, start=1):
            print(f"{i}) {Path(file).name}")
        print("e) Exit")
        
        while True:
            try:
                choice = input("Please choose a number: ")
                if choice == 'e':
                    return
                if 1 <= int(choice) <= len(folder_paths):
                    return Path(folder_paths[int(choice) - 1])
                else:
                    print(f"Please enter a number between 1 and {len(folder_paths)}")
            except ValueError:
                print("Please enter a valid number")

    def get_llm_id_from_user(self) -> int:
        """This function is getting a llm id from the user input"""

        llm = self.db.llm.get_all()
        datas = [[r.id, r.name, r.model, r.reasoning] for r in llm]
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
            elif self.db.llm.get_column_value(llm_id=int(llm_id), column='id') == "":
                clear_console()
                print(f"\nThe given LLM ID ({llm_id}) was not recognisable. Please choose another one.\n")
                continue
            return int(llm_id)
        
    @staticmethod
    def get_file_from_user(directory_path:Path, extension:str='.json') -> Path:
        """This function is getting a json path from the user input"""

        datas = [[i, filename.name] for i, filename in enumerate(directory_path.glob(f'*{extension}'), start=1)]

        while True:
            print(f"You can load any file that has not been yet exported and it is stored at {directory_path}")
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
                return Path(datas[int(number)-1][1])
            clear_console()
            print(f"\nThe given number ({number}) was not recognisable. Please choose another one.\n")
            continue
        
    def get_task_id_from_user(self) -> int:
        """This function is getting a task id from the user input"""

        tasks = self.db.task.get_all()
        datas = [[r.id, r.name, r.description] for r in tasks]
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
            elif self.db.task.get_column_value(task_id=int(task_id), column='id') == "":
                clear_console()
                print(f"\nThe given Task ID ({task_id}) was not recognisable. Please choose another one.\n")
                continue
            return int(task_id)
        
    @staticmethod
    def get_minimal_frequences():
        """Get the minimal frequences parameter from the user input"""
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
    def select_result(self):
        """This function helps to choose the user which older run should be evaluated"""

        datas = self.db.run.get_all_readable()
        clear_console()
        while True:
            
            print("You can evaluate any loaded data that is in the database")
            print("You can exit using 'e'")
            print("\n           Currently available in database")
            print_table(
                header_names=['Run ID', 'Date', 'LLM name', 'LLM model', 'Task name', 'Successfull'],
                datas=datas
            )

            run_id = input("\nPlease give Run ID: ")
            if run_id == 'e':
                return
            elif self.db.run.get_column_value(run_id=int(run_id), column='id') == "":
                clear_console()
                print(f"\nThe given Run ID ({run_id}) was not recognisable. Please choose another one.\n")
                continue
            else:
                return int(run_id)
        
    @safe_operation()
    def re_evaluate_validation(self, run_id:int):
        """This function get's a run_id, and then re-evaluate it's answers"""

        answers = self.db.answer.get_all(run_id=run_id)
        validator = Validation()

        for answer in answers:
            validation_message = validator.validate_chain(answer['chain'].replace(' ','-'))
            if validation_message != answer.validation:
                self.db.answer.update_field(
                    answer_id = answer.id,
                    column = 'validation',
                    new_value = validation_message
                )

