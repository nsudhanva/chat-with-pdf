from langchain.chat_models import ChatOpenAI
from app.chat.models import ChatArgs


def build_llm(chat_args: ChatArgs):
    return ChatOpenAI()
