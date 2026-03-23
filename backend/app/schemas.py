from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    chat_history: str