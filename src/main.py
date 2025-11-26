from scripts.load_enviroment import AUTHOR
from scripts.logger.logger import get_logger
from scripts.load.load import reload_older, load_manual_datas_json, load_manual_datas_txt, evaluate_results, re_evaluate_results
from classes.db_manager import get_database
from scripts.basic_tools import clear_console
from scripts.terminal.terminal import terminal
from scripts.chatbot.chatbot_handler import start_conversation


def assignment_selector() -> str:
    """
    A user can choose between different tasks. The function returns with the number of the selected item
    """

    choosable_tasks = {'1', '2', '3', '4', '5', '6', '7', 'e'}
    clear_console()
    while True:
        print("\nPlease choose from the tasks below:")
        print("1) Reload older results to database")
        print("2) Play with chatbot")
        print("3) Get results")
        print("4) Re evaluate older results")
        print("5) Load manually collected data to database (.json)")
        print("6) Load manually collected data to database (.txt)")
        print("7) Terminal")
        print("e) Exit")
        task = input("Selected task: ")

        if task in choosable_tasks:
            return task
        else:
            clear_console()
            print("\nThe given number was not recognisable. Please choose another one.\n")


def main():
    """Just the main function of the code that call's the assignment's function"""
    db = get_database()
    while True:
        task = assignment_selector()
        
        match task:
            case '1':
                reload_older()
                input("\nPress any key to continue")
                clear_console()
            case '2':
                start_conversation()
                clear_console()
            case '3':
                evaluate_results()
                input("\nPress any key to continue")
                clear_console()
            case '4':
                re_evaluate_results()
                input("\nPress any key to continue")
                clear_console()
            case '5':
                load_manual_datas_json()
                input("\nPress any key to continue")
                clear_console()
            case '6':
                load_manual_datas_txt()
                input("\nPress any key to continue")
                clear_console()
            case '7':
                clear_console()
                terminal()
                clear_console()
            case 'e':
                db.close()
                break


if __name__ == '__main__':
    main()