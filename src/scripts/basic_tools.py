from pathlib import Path
import os
from scripts.safe_operation import safe_operation
from dotenv import load_dotenv
import json
from prettytable import PrettyTable
from typing import List, Any


ROOT = Path(__file__).resolve().parents[2]

load_dotenv(ROOT/'config/.env')

@safe_operation(exceptions=(OSError,ValueError))
def get_enviromental_variable(key:str) -> str:
    """Returns with the enviromental variable. If the variable is not exists, raises an Error"""
        
    env = os.getenv(key)
    if env is None:
        raise OSError(f"Missing required environment variable: {key} ")
    return env

def clear_console():
    os.system('clear')

@safe_operation(exceptions=FileExistsError)
def load_data(path:Path):
    """Load to json data"""

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def print_table(header_names: List[str], datas: List[List[Any]]) -> None:
    """A simple function that pretty print the tables

    :param header_names: The names that are goint to be the headers
    :param datas: A List of list that contains the data
    """
    
    table = PrettyTable()
    table.field_names = header_names
    
    for row in datas:
        table.add_row(["" if val is None else val for val in row])

    table.junction_char = '+'
    table.horizontal_char = '-'
    table.vertical_char = '|'
    table.header = True
    table.border = False
    table.preserve_internal_border = True

    print(table)