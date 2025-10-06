from scripts.question_validation import semantic_validation, find_shortest_word_path
import os
import sys
from pathlib import Path


def in_3_letter_scrabble_words(word_chain:str) -> bool:
    filename = "data/three_letter_scrabble_words.txt"
    words = word_chain.split('-')

    try:
        with open(filename, 'r') as file:
            txt_words = [line.strip().lower() for line in file]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return False

    for word in words:
        word = word.lower()
        if word not in txt_words:
            print(f"Word '{word}' is not in the list of three-letter Scrabble words.")
    
    print("True")

def text_answer_distribution(file_path: str | Path, save_to_file: bool = False, output_file: str | Path = None) -> None:
    """
    Analyze and display distribution of validation results from a text file.
    
    Args:
        file_path: Path to the input text file
        save_to_file: Whether to save the output to a file
        output_file: Path to the output file (if save_to_file is True)
    """
    repeating = 0
    neighbours = 0
    invalid = 0
    true = 0
    all = 0
    
    # Store all output lines for display and potential saving
    output_lines = []
    
    # Calculate the maximum length of any line for proper alignment
    max_line_length = 0
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            max_line_length = max(max_line_length, len(line))
    
    # Add some padding for better visual separation
    column_width = max_line_length + 4
    
    # Process the file and collect results
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            validation_message = semantic_validation(line)
            all += 1

            formatted_line = f"{line:{column_width}}{validation_message}"
            output_lines.append(formatted_line)
            
            if validation_message == "Repeting words":
                repeating += 1
            elif validation_message == "Not neighbours":
                neighbours += 1
            elif validation_message == "Not in the acceptable .txt list":
                invalid += 1
            elif validation_message == "True":
                true += 1
    
    # Create summary statistics
    summary_lines = [
        "\n\n",
        f"True:               {true:2}          ({(true/all)*100:5.1f}%)",
        f"repeating:          {repeating:2}          ({(repeating/all)*100:5.1f}%)",
        f"neighbours:         {neighbours:2}          ({(neighbours/all)*100:5.1f}%)",
        f"invalid word:       {invalid:2}          ({(invalid/all)*100:5.1f}%)",
        f"All:                {all:2}"
    ]
    
    # Always print to console 
    for line in output_lines:
        print(line)
    
    for line in summary_lines:
        print(line)
    
    # Save to file if requested
    if save_to_file and output_file:
        try:
            with open(output_file, 'w') as f:
                for line in output_lines:
                    f.write(line + '\n')
                
                # Add summary to the file
                for line in summary_lines:
                    f.write(line + '\n')
                    
            print(f"\nResults saved to {output_file}")
        except Exception as e:
            print(f"\nError saving to file: {e}")
    
    # Return the collected data for reuse
    return {
        "output_lines": output_lines,
        "summary_lines": summary_lines,
        "stats": {
            "true": true,
            "repeating": repeating,
            "neighbours": neighbours,
            "invalid": invalid,
            "all": all
        }
    }

def save_results(output_lines, summary_lines, output_file):
    """Save analysis results to a file without printing them again."""
    try:
        with open(output_file, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')
            
            # Add summary to the file
            for line in summary_lines:
                f.write(line + '\n')
                
        print(f"\nResults saved to {output_file}")
        return True
    except Exception as e:
        print(f"\nError saving to file: {e}")
        return False



def clear_console():
    """Clear the console screen based on the operating system."""
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def handle_common_commands(user_input):
    """Handle commands that should work in every function.
    Returns True if a command was handled, False otherwise."""
    if user_input.lower() in ["exit", "e"]:
        return "exit"
    elif user_input.lower() == "clear":
        clear_console()
        return "clear"
    elif user_input.lower() == "menu":
        return "menu"
    return None  # No common command was used

def shortest_path():
    while True:
        # Taking input from user
        user_input = input("[shortest]: ").strip()
        
        # Check for common commands
        result = handle_common_commands(user_input)
        if result == "exit":
            return  # Exit this function and return to caller
        elif result == "clear":
            continue  # Skip the rest of the loop and prompt again
        elif result == "menu":
            return "menu"  # Special return value to go back to menu
        
        # If we get here, no common command was used
        try:
            inputs = user_input.split()
            if len(inputs) < 2:
                print("Please provide two words separated by space.")
                continue
                
            gmpl_path = "/mnt/c/Users/beket/Documents/Egyetem/6.felev/onlab/kodok/word_morph_network.gml"
            path, length = find_shortest_word_path(gml_path=gmpl_path, word1=inputs[0], word2=inputs[1])
            print(f"{'-'.join(path)}           Length: {length}")
        except Exception as e:
            print(f"Error: {e}")

def validation():
    while True:
        user_input = input("[validation]: ").strip()
        
        # Check for common commands
        result = handle_common_commands(user_input)
        if result == "exit":
            return  # Exit this function and return to caller
        elif result == "clear":
            continue  # Skip the rest of the loop and prompt again
        elif result == "menu":
            return "menu"  # Special return value to go back to menu
        
        # If we get here, no common command was used
        message = semantic_validation(user_input)
        print(message)

def words():
    while True:
        user_input = input("[words]: ").strip()
        
        # Check for common commands
        result = handle_common_commands(user_input)
        if result == "exit":
            return  # Exit this function and return to caller
        elif result == "clear":
            continue  # Skip the rest of the loop and prompt again
        elif result == "menu":
            return "menu"  # Special return value to go back to menu
        
        # If we get here, no common command was used
        in_3_letter_scrabble_words(user_input)

def text_evaluation():
    while True:
        user_input = input("[.txt]: ").strip()
        
        # Check for common commands
        result = handle_common_commands(user_input)
        if result == "exit":
            return  # Exit this function and return to caller
        elif result == "clear":
            continue  # Skip the rest of the loop and prompt again
        elif result == "menu":
            return "menu"  # Special return value to go back to menu
        
        # Check if the command is to save results
        if user_input.lower().startswith("save "):
            # Format should be "save input.txt output.txt"
            parts = user_input.split(maxsplit=2)
            if len(parts) != 3:
                print("Usage: save <input_file> <output_file>")
                continue
                
            _, input_file, output_file = parts
            input_path = Path(input_file)
            
            # Validate input file
            if not input_path.exists() or not input_path.is_file():
                print(f"Input file not found: {input_file}")
                continue
                
            try:
                text_answer_distribution(input_path, save_to_file=True, output_file=output_file)
            except Exception as e:
                print(f"Error: {e}")
            continue
            
        # If we get here, no common command was used
        try:
            file_path = Path(user_input)
            
            # Improved file validation
            if not file_path.exists():
                print("File not found. Please provide a valid file path.")
                continue
            elif not file_path.is_file():
                print("The path exists but is not a file. Please provide a valid file path.")
                continue
            
            # Process the file and get results
            results = text_answer_distribution(file_path)
            
            # Ask if user wants to save results (without reprinting)
            save_choice = input("Save results to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                output_file = input("Enter output filename: ").strip()
                if output_file:
                    save_results(results["output_lines"], results["summary_lines"], output_file)
            
        except PermissionError:
            print("Permission denied. Cannot access the file.")
        except Exception as e:
            print(f"Error: {e}")


def assignment_selector():
    """
    A user can choose between different tasks. The function returns a string describing the selected item.
    """
    task_mapping = {
        '1': "validation",
        '2': "shortest path",
        '3': "words",
        '4': "text evaluation",
        'e': "exit",
        'exit': "exit"
    }

    while True:
        print("#### TERMINAL ####")
        print("\nPlease choose from the tasks below:")
        print("1) Validation")
        print("2) Shortest path")
        print("3) words")
        print("4) text evaluation")
        print("e) Exit")
        print("Type 'clear' to clear the console")
        print("Type 'menu' from any subfunction to return to this menu")

        user_input = input("Selected task: ").strip()
        
        # Check for common commands like clear
        result = handle_common_commands(user_input)
        if result == "clear":
            continue
        
        # Check if it's a valid task selection
        if user_input.lower() in task_mapping:
            return task_mapping[user_input.lower()]
        else:
            print("\nThe given input was not recognizable. Please choose another one.\n")

def terminal():
    while True:
        assignment = assignment_selector()

        if assignment == "exit":
            print("Exiting program. Goodbye!")
            break
        elif assignment == "validation":
            result = validation()
            if result == "menu":
                continue
        elif assignment == "shortest path":
            result = shortest_path()
            if result == "menu":
                continue

        elif assignment == "words":
            result = words()
            if result == "menu":
                continue

        elif assignment == "text evaluation":
            result = text_evaluation()
            if result == "menu":
                continue
