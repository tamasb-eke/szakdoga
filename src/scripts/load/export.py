import pandas as pd
from classes.db_manager import get_database
from scripts.basic_tools import SAVE_CSV_PATH
from scripts.logger.logger import get_logger
from scripts.question_validation import find_shortest_word_path
from scripts.safe_operation import safe_operation

@safe_operation()
def export_to_scv(run_id:int) -> None:
    """A simple function that export to a csv the following:
        - Source and Targetword
        - Length of chainword
        - Chainword
        - Shortest chainword based on the Source and Targetword
        - Length of the shortest chainword for the Source and Targetword
    """

    logger = get_logger()
    db = get_database()
    answers = db.answer.get_all(run_id=run_id, only_correct=True)
    print(f"Exporting to {run_id}.csv ....")

    outputfilepath = SAVE_CSV_PATH / f"{run_id}_output.csv"
    if outputfilepath.exists():
        logger.warning(f"Can not export {run_id}, it was already exported at: {outputfilepath}")
        return
    
    exported_data = []
    for r in answers:
        try:
            data = {
                'source_word': r['sourceWord'].lower(),
                'target_word': r['targetWord'].lower(),
                'chain': r['chain'].lower(),
                'chain_length': r['chain_length'],
                'shortest_path': (shortest := find_shortest_word_path(r['sourceWord'].lower(), r['targetWord'].lower()))[0],
                'shortest_length': shortest[1]
            }
            exported_data.append(data)
        except Exception as e:
            logger.error(e)

    df = pd.DataFrame(exported_data)
    df.to_csv(outputfilepath, index=False)
    logger.info(f"run_id: {run_id} was exported to {outputfilepath} successfully")
