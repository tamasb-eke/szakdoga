from scripts.safe_operation import safe_operation
from classes.db_manager import get_database
from scripts.basic_tools import print_table, clear_console

@safe_operation()
def select_result():
    """"""

    db = get_database()
    data = db.run.get_all_(readable=True)
    clear_console()

    while True:
        
        print("You can evaluate any loaded data that is in the database")
        print("\n           Currently available in database")
        print_table(
            header_names=['Run ID','Date', 'LLM name', 'LLM model', 'LLM reasoning', 'Task name', 'Task description', 'Json path', 'Successfull'],
            datas=data
        )

        run_id = int(input("\nPlease give Run ID: "))
        if db.run.get_(run_id=run_id, column='id') == "":
            clear_console()
            print(f"\nThe given Run ID ({run_id}) was not recognisable. Please choose another one.\n")
            continue

        else:
            break
    
    clear_console()
    
    db.evaluation(run_id=run_id)
