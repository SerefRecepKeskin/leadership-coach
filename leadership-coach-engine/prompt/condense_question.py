# pylint: skip-file
# flake8: noqa
from llama_index.core.prompts import PromptTemplate

CONDENSE_QUESTION_PROMPT = PromptTemplate("""
    Given the conversation history and a new question, rephrase the question in a self-contained and concise manner.
    Retain the original meaning and include relevant context when needed.
    ALWAYS provide the rephrased question in Turkish, regardless of the input language.

    Chat History:
    {chat_history}

    New Question:
    {question}

    Rephrased Question (in Turkish):
    """
)
