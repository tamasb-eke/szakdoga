import pandas as pd
import networkx as nx
from classes.db_manager import Database
from scripts.basic_tools import EXPORT_PATH
from scripts.safe_operation import safe_operation
from scripts.load_enviroment import APP_ENV
from logging import Logger
from model.validation import Validation

class Exporter:
    def __init__(self, logger:Logger, db:Database):
        self.app_env = APP_ENV
        self.save_path = EXPORT_PATH
        self.logger = logger
        self.db = db

    @safe_operation()
    def export_to_csv(self, run_id:int) -> None:
        """A simple function that export to a csv the following:
            - Source and Targetword
            - Length of chainword
            - Chainword
            - Shortest chainword based on the Source and Targetword
            - Length of the shortest chainword for the Source and Targetword
        """
        validator = Validation()
        answers = self.db.answer.get_all(run_id=run_id)
        llm_name = self.db.llm.get_column_value(
            llm_id=self.db.run.get_column_value(run_id=run_id, column="llm_id"), 
            column="name"
        )
        outputfilepath = self.save_path / f"{run_id}_{llm_name}_{self.app_env}_output.csv"
        print(f"Exporting to {outputfilepath} ....")
        
        if outputfilepath.exists():
            self.logger.warning(f"Can not export {run_id}, it was already exported at: {outputfilepath}")
            return
        
        exported_data = []
        for answer in answers:
            try:
                path, length = validator.semantic.find_shortest_path(answer.sourceWord, answer.targetWord)
                shortest = "-".join(path) if length > 1 else path

                if length > answer.chain_length:
                    raise ValueError(f"Shorter chain length than possible shortest... AnswerID: {answer.id}")
                
                data = {
                    'source_word': answer.sourceWord.lower(),
                    'target_word': answer.targetWord.lower(),
                    'validation': answer.validation,
                    'chain': answer.chain.lower(),
                    'chain_length': answer.chain_length,
                    'shortest_path': shortest,
                    'shortest_length': length
                }
                exported_data.append(data)    
            except Exception as e:
                self.logger.warning(f"Handling: {e}")
                data = {
                    'source_word': answer.sourceWord.lower(),
                    'target_word': answer.targetWord.lower(),
                    'validation': 'Too short chain length' if e == 'Shorter chain length than possible shortest...' else "Not in the acceptable .txt list",
                    'chain': answer.chain.lower(),
                    'chain_length': answer.chain_length,
                    'shortest_path': shortest if e == 'Shorter chain length than possible shortest...' else '[]',
                    'shortest_length': length if e == 'Shorter chain length than possible shortest...' else 0
                }
                exported_data.append(data)

        df = pd.DataFrame(exported_data)
        df.to_csv(outputfilepath, index=False)
        self.logger.info(f"run_id: {run_id} was exported to {outputfilepath} successfully")


    def export_to_gml(self, run_id:int) -> None:
        """
        Fetches answers for a given run_id from the database and exports 
        the word chains into a .gml file as a graph.
        """
        results = self.db.answer.get_all(run_id=run_id)
        if len(results) == 0:
            self.logger.warning(f"No results found for run_id {run_id}...")
            return

        llm_model = self.db.llm.get_column_value(
            llm_id=self.db.run.get_column_value(run_id=run_id, column="llm_id"), 
            column="model"
        )

        outputfilepath = self.save_path / f"{run_id}_{llm_model}.gml"
        print(f"Exporting to {outputfilepath} ....")

        if outputfilepath.exists():
            self.logger.warning(f"Can not export {run_id}, it was already exported at: {outputfilepath}")
            return
        
        G = nx.Graph() 
        G.graph['results_used'] = len(results)
        G.graph['run_id'] = run_id
        G.graph['llm_model'] = llm_model
        
        for answer in results:
            if not answer.chain:
                continue
                
            words = answer.chain.replace('-', ' ').split(' ')
            for i in range(len(words) - 1):
                w1 = words[i].lower()
                w2 = words[i+1].lower()
            
                if G.has_edge(w1, w2):
                    G[w1][w2]['count'] += 1
                else:
                    G.add_edge(w1, w2, count=1)
                    
        nx.write_gml(G, outputfilepath)
        print(f"Successfully exported Run {run_id} ({len(results)} chains) to {outputfilepath}")