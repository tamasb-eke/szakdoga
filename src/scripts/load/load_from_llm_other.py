from scripts.safe_operation import safe_operation
from classes.db_manager import get_database
from datetime import datetime
from scripts.question_validation import semantic_validation, syntactic_validation
from scripts.logger.logger import get_logger

@safe_operation()
def llm_messages_loader(llm_messages:list[dict], run_id:int, date:str = datetime.now().strftime('%Y%m%d_%H%M%S')):
    """"""
    logger = get_logger()
    db = get_database()

    for content in (item["content"] for item in llm_messages if item["role"] == "assistant"):

        if not syntactic_validation(content):
            logger.error(f"Incorrect syntactic for wordchain: {content}") #can happen because llm gives not just answers
            continue

        validation_message = semantic_validation(content)

        db.answer.insert(
            run_id = run_id,
            chain = content,
            chain_length = len(content.split('-')),
            sourceword = content.split('-')[0],
            targetword = content.split('-')[-1],
            date = date,
            validation = validation_message
        )