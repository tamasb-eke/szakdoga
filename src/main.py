from scripts.load.load import reload_older
from classes.db_manager import get_database
from scripts.load_enviroment import AUTHOR
from classes.api import Chatbot
from scripts.basic_tools import clear_console

db = get_database()
chatbot = Chatbot()


def assignment_selector() -> str:
    """
    A user can choose between different tasks. The function returns with the number of the selected item
    """

    choosable_tasks = {'1', '2', '3', '4','e'}
    clear_console()
    while True:
        print("\nPlease choose from the tasks below:")
        print("1) Reload older results to database")
        print("2) Play with chatbot")
        print("3) Get results")
        print("4) Load older datas to database")
        print("e) Exit")
        task = input("Selected task: ")

        if task in choosable_tasks:
            return task
        else:
            print("\nThe given number was not recognisable. Please choose another one.\n")


def main():
    """Just the main function of the code that call's the assignment's function"""
    db = get_database()
    while True:
        task = assignment_selector()
        
        match task:
            case '1':
                reload_older()
            case '2':
                ()
            case '3':
                ()
            case '4':
                ()
            case '5':
                ()
            case 'e':
                print("Exiting...")
                db.close()
                break



if __name__ == '__main__':
    main()