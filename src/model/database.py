from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class LLM(Base):
    __tablename__ = "LLM"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)


class Human(Base):
    __tablename__ = "Human"

    id = Column(Text, primary_key=True, nullable=False)
    games_played = Column(Integer, nullable=False, default=0)


class Task(Base):
    __tablename__ = "Task"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)


class Run(Base):
    __tablename__ = "Run"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    llm_id = Column(Integer, ForeignKey("LLM.id"))
    person_id = Column(Text, ForeignKey("Human.id"))
    task_id = Column(Integer, ForeignKey("Task.id"), default=1)
    json_path = Column(Text, nullable=False, default="data/saved_conversation/")
    date = Column(Text, nullable=False, default=datetime.today().strftime("%Y-%m-%d %H:%M"))
    successful = Column(Text, nullable=False, default="False")


class Answer(Base):
    __tablename__ = "Answer"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    run_id = Column(Integer, ForeignKey("Run.id"), nullable=False, default=0)
    chain = Column(Text, nullable=False)
    chain_length = Column(Integer, nullable=False)
    date = Column(Text, default=datetime.today().strftime("%Y-%m-%d %H:%M"))
    sourceWord = Column(Text, nullable=False)
    targetWord = Column(Text, nullable=False)
    validation = Column(Text, nullable=False, default="True")
