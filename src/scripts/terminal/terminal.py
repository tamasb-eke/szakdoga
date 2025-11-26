from scripts.question_validation import semantic_validation, find_shortest_word_path
from scripts.basic_tools import clear_console
from scripts.question_validation import *

def handle_common_commands(user_input:str) -> None:
    """
    This function handle commands that should work in every function
    """
    if user_input == 'clear':
        clear_console()
        return user_input
    elif user_input in ['e', 'exit', 'menu']:
        return None
    return user_input


def shortest_path():
    """Component that gives the shortest path between two given word"""
    while True:

        user_input = input("[shortest]: ").strip()
        
        result = handle_common_commands(user_input)
        if not result:
            return
        if user_input == 'clear':
            continue

        try:
            inputs = user_input.split()
            if len(inputs) < 2:
                print("Please provide two words separated by space.")
                continue
                
            route, length = find_shortest_word_path(word1=inputs[0].lower(), word2=inputs[1].lower())
            print(f"{'-'.join(route)}           Length: {length}")
        except Exception as e:
            print(f"Error: {e}")

def validation():
    """Component that evaluates if the user's entry is a valid word semantically"""
    while True:
        user_input = input("[validation]: ").strip()
        
        result = handle_common_commands(user_input)
        if not result:
            return
        if result == 'clear':
            continue

        message = semantic_validation(user_input)
        print(message)

def words():
    cache = None
    while True:
        user_input = input("[words]: ").strip()
        
        result = handle_common_commands(user_input)
        if not result:
            return
        if result == 'clear':
            continue
        
        words = user_input.split('-')
        for word in words:
            is_in, cache = in_3_letter_scrabble_words(word, cache)
            if not is_in:
                print(f"Word '{word}' is not in the list of three-letter Scrabble words.")
                return
        
        print("True")


def assignment_selector():
    """
    A user can choose between different tasks. The function returns a string describing the selected item.
    """
    task_mapping = {
        '1': "validation",
        '2': "shortest path",
        '3': "words",
        'e': "exit",
        'exit': "exit"
    }

    clear_console()
    while True:
        print("#### TERMINAL ####")
        print("\nPlease choose from the tasks below:")
        print("1) Validation")
        print("2) Shortest path")
        print("3) words")
        print("e) Exit")
        print("Type 'clear' to clear the console")
        print("Type 'menu' from any subfunction to return to this menu")

        user_input = input("Selected task: ").strip()
        result = handle_common_commands(user_input)
        
        if user_input.lower() in task_mapping:
            return task_mapping[user_input.lower()]
        elif user_input in ["clear", "menu"]:
            return
        else:
            clear_console()
            print("\nThe given input was not recognizable. Please choose another one.\n")

def terminal():
    """The entry point of the terminal side of the code. You can mess around here and get validation without the need to load anything to database"""
    while True:
        assignment = assignment_selector()

        if assignment == "validation":
            clear_console()
            validation()
            clear_console()

        elif assignment == "shortest path":
            clear_console()
            shortest_path()
            clear_console()

        elif assignment == "words":
            clear_console()
            words()
            clear_console()

        elif assignment == "exit":
            break
