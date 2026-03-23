import json
import re
from pathlib import Path
from datetime import datetime
from scripts.logger.logger import get_logger
from scripts.safe_operation import safe_operation
from scripts.basic_tools import ROOT, clear_console, SAVED_CONVERSATION_PATH
from classes.db_manager import get_database
from scripts.load.load_helper import LoadHelper
from scripts.visualize.graph import visualizer
from .export import Exporter
from model.schemas import GameLogsExport, RunSchema, AnswerSchema, HumanSchema, ConversationHistory
from model.validation import Validation

class LoadToDatabase:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.saved_conversation_path = SAVED_CONVERSATION_PATH
        self.validator = Validation()
        self.helper = LoadHelper(self.logger, self.db)
        self.export = Exporter(self.logger, self.db)

    @safe_operation()
    def llm_messages_loader(
            self,
            llm_messages:ConversationHistory, 
            run_id:int = None, 
            date:str = datetime.now().strftime('%Y%m%d_%H%M%S')
        ):
        """
        This function basically get the llm_messages and the it load to db. It can be used after a chatbot conversation ended and
        you want to save the results to database.
        
        :param llm_meesages: The variable that stores the conversation between the LLM and the user
        :param run_id: The run_id that you want to save to it. If no one is given then the default is the latest run.
        :param date: The date of the exportation to database. (By default is the current date)
        """

        if not run_id:
            run_id = self.db.run.get_latest_id()

        for content in (item.content for item in llm_messages.messages if item.role == "assistant"):
            validation_message = self.validator.validate_chain(content)

            if validation_message == self.validator.statuses.SYNTAXERROR:
                self.logger.warning(f"Incorrect syntactic for wordchain: {content}") #can happen because llm gives not just answers
                continue

            self.db.answer.insert(
                AnswerSchema(
                    run_id=run_id,
                    chain=content,
                    chain_length=len(content.split('-')),
                    sourceWord=content.split('-')[0],
                    targetWord=content.split('-')[-1],
                    date=date,
                    validation=validation_message
                )
            )

    def evaluate_results(self):
        """This function print out validation to output"""

        run_id = self.helper.select_result()
        if not run_id:
            return
        
        self.db.evaluation(run_id=run_id)
        print("\n\nDo you want to save the results to a .CSV? (y) Yes (n) No")
        export = input("Y/N: ").lower()
        if export in ['y', 'yes']:
            self.export.export_to_csv(run_id=int(run_id))

        print("\n\nDo you want to save the results to a .GML? (y) Yes (n) No")
        export = input("Y/N: ").lower()
        if export in ['y', 'yes']:
            self.export.export_to_gml(run_id=int(run_id))
        
        print("\n\nDo you want to visualize the results? (y) Yes (n) No")
        visualize = input("Y/N: ").lower()
        if visualize in ['y', 'yes']:
            visualizer(run_id=int(run_id))

    def re_evaluate_results(self):
        """This function re evaluate results for a given run and then print out validation to output"""
        run_id = self.helper.select_result()
        self.helper.re_evaluate_validation(run_id=run_id)
        self.db.evaluation(run_id=run_id)


class JsonLoader(LoadToDatabase):
    def __init__(self):
        super().__init__()
        self.json_path = Path(ROOT/'data/other_data_files/word_navigation_game_export.json')

    @safe_operation()
    def study_results_to_db(self) -> None:
        """
        This function is loading from the research result's 'word_navigation_game_export.json' file
        It is usefull if the database is corrupted or needs a reload
        """

        if not self.json_path.exists():
            raise FileNotFoundError(f"Path to word_navigation_game_export.json. It should have a path: {self.json_path}")
        
        with open(self.json_path, 'r', encoding='utf-8') as file:
            raw_data = json.load(file)
            export_data = GameLogsExport.model_validate(raw_data)

        for player_id, games_dict in export_data.GameLogs.items():
            games_played = 0
            self.logger.info("-------------------------------------------------------------------------")
            
            self.db.run.insert(
                RunSchema(
                    person_id=player_id,
                    task_id=2
                )
            )
            run_id = self.db.run.get_latest_id()
            if self.db.human.already_in_db(human_id=player_id): #in case if we ran into the same person again later in the file
                run_id = self.db.run.get_person_id_by_run(player_id)
                games_played = self.db.human.get_column_value(human_id=player_id, column="games_played")

            for game_id, game_data in games_dict.items():
                if game_data.chain_length < 2:
                    continue

                if self.db.human.already_answered(human_id=player_id, solution=game_data.chain):
                    self.logger.info(f"{player_id} already answered {game_data.chain}")
                    continue

                games_played += 1
                validation = self.validator.validate_chain(game_data.chain)
                formatted_date = self.helper.convert_date(game_data.raw_date)

                self.db.answer.insert(
                    AnswerSchema(
                        run_id=run_id,
                        chain=game_data.chain.replace(' ', '-'),
                        chain_length=game_data.chain_length,
                        targetWord=game_data.target_word,
                        sourceWord=game_data.source_word,
                        validation=validation,
                        date=formatted_date
                    )
                )

            if games_played > 0:
                self.db.human.insert(
                    HumanSchema(
                        id=player_id,
                        games_played=games_played
                    )
                )

                self.db.run.update_field(run_id=run_id, column='successful', value=True)

        self.helper.clear_unesecarry(self.db)

    @safe_operation()
    def older_results_to_db(self, result_path:Path|str) -> None:
        """"
        Load the answers from an earlier chatbot results. The results are stored in data/chatbor_result folder
        IMPORTANT: It is usefull for chatbot conversation. If you want to save manually collected results, please use: manually_collected_to_db()

        :param result_path: Path to the saved chatbot conversation. Their place is at: data/chatbor_result folder
        """
        if not result_path:
            return

        if isinstance(result_path, str):
            result_path = Path(result_path)
        if not result_path.exists():    
            raise FileNotFoundError(f"File not found: {result_path}")

        filename = result_path.name
        run_id = filename.split('_')[-1]
        date = filename.split('_')[-2]
        llm_id = self.db.run.get_column_value(run_id=run_id, column="llm_id")
        task_id = self.db.run.get_column_value(run_id=run_id, column="task_id")

        self.db.run.insert(
            RunSchema(
                llm_id=llm_id,
                task_id=task_id,
                json_path=result_path
            )
        )
        run_id = self.db.run.get_latest_id()

        with open(result_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            if "messages" not in raw_data:
                raise ValueError("Invalid JSON structure: missing 'messages' key.")

        self.llm_messages_loader(
            llm_messages=ConversationHistory(**raw_data),
            run_id=run_id,
            date=date
        )

        self.db.run.update_field(run_id=run_id, column='successful', value=True)


    @safe_operation()
    def load_manual_datas_json(self):
        """
        This function helps the user decide which .json should be saved. The saved json's are in 'data/saved_conversation'. 
        Also the .json filename has to be a structure like this:

        Filename Pattern:
            'llm_name'_chat_history_'YYYY-MM-DD-HH-MM'_'run_id'.json
            Example: gpt4_chat_history_2025-05-05-20-30_123.json 

        Run_id will be generated automatically, and the file will be renamed according to it
        """
        
        if not self.saved_directory.exists():
            raise NotADirectoryError(f"The {SAVED_CONVERSATION_PATH} folder does not exists!")

        clear_console()
        filepath = self.saved_directory / self.helper.get_file_from_user(self.saved_directory)
        if not filepath.exists():
            raise FileExistsError(f"Filepath not exists: {filepath}")
        llm_id = self.helper.get_llm_id_from_user()
        if not llm_id:
            return
        task_id = self.helper.get_task_id_from_user()
        if not task_id:
            return

        self.db.run.insert(
            RunSchema(
                llm_id=llm_id,
                task_id=task_id,
                json_path=str(filepath)
            )
        )
        run_id = self.db.run.get_latest_id()
        date = datetime.now().strftime("%Y-%m-%d-%H-%M")

        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            if "messages" not in raw_data:
                raise ValueError("Invalid JSON structure: missing 'messages' key.")

        self.llm_messages_loader(
            llm_messages=ConversationHistory(**raw_data),
            run_id=run_id,
            date=date
        )

        new_filename = f"{self.db.llm.get_(llm_id=llm_id, column='name')}_chat_history_{date}_{run_id}.json"
        new_file_path = self.saved_directory / new_filename
        filepath.rename(new_file_path)
        self.db.run.update_field(run_id=run_id, column='json_path', new_value=str(new_file_path))
        self.db.run.update_field(run_id=run_id, column='successful', new_value=True)

    def reload_older(self):
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
                        self.study_results_to_db()
                    case '2':
                        self.older_results_to_db(result_path=self.helper.get_manually_collected_json_path())
                    case 'e':
                        break

class TxtLoader(LoadToDatabase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def extract_word_chain(string: str) -> str | None:
        """
        Extracts the wordchain. It is usefull for .txt loading
        Returns the first match found, or None if no such pattern exists.
        """
        pattern = r'\b(?:[A-Za-z]+-)+[A-Za-z]+\b'
        match = re.search(pattern, string)
        return match.group(0) if match else None


    @safe_operation()
    def to_db_from_txt(self, file_path:Path, run_id:int) -> None:
        """This function loads the datas into the database from a .txt"""
        
        inserted = 0
        with open(file_path, 'r') as f:
            data = f.read()

        for line in data.split('\n'):
            validation = self.validator.validate_chain(line)
            if validation != self.validator.statuses.SYNTAXERROR:
                self.db.answer.insert(
                    AnswerSchema(
                        run_id=run_id,
                        chain=line,
                        chain_length=len(line.split('-')),
                        sourceword=line.split('-')[0],
                        targetword=line.split('-')[-1],
                        validation_message=self.validator.validate_chain(line),
                    )
                )
                inserted += 1
            self.logger.info(f"Loaded {inserted} line of words from {file_path}")

    @safe_operation()
    def load_manual_datas_txt(self):
        """
        This function helps the user decide which .txt should be saved. The saved txt's are in 'data/saved_conversation'. 
        Also the .txt filename has to be a structure like this:

        Filename Pattern:
            'llm_name'_chat_history_'YYYY-MM-DD-HH-MM'_'run_id'.json
            Example: gpt4_chat_history_2025-05-05-20-30_123.json 

        Run_id will be generated automatically, and the file will be renamed according to it
        """

        if not self.saved_directory.exists():
            raise NotADirectoryError(f"The {SAVED_CONVERSATION_PATH} folder does not exists!")

        clear_console()
        filepath = self.saved_directory / self.helper.get_file_from_user(self.saved_directory, extension='.txt')
        if not filepath.exists():
            raise FileExistsError(f"File not exists: {filepath}")
        llm_id = self.helper.get_llm_id_from_user()
        if not llm_id:
            return
        task_id = self.helper.get_task_id_from_user()
        if not task_id:
            return

        self.db.run.insert(
            RunSchema(
                llm_id=llm_id,
                task_id=task_id,
                json_path=str(filepath)
            )
        )
        run_id = self.db.run.get_latest_id()
        self.to_db_from_txt(
            file_path=filepath,
            run_id=run_id,
        )

        date = datetime.now().strftime("%Y-%m-%d-%H-%M")
        new_filename = f"{self.db.llm.get_(llm_id=llm_id, column='name')}_chat_history_{date}_{run_id}.txt"
        new_file_path = self.saved_directory / new_filename
        filepath.rename(new_file_path)
        self.db.run.update_field(run_id=run_id, column='json_path', new_value=str(new_file_path))
        self.db.run.update_field(run_id=run_id, column='successful', new_value=True)

