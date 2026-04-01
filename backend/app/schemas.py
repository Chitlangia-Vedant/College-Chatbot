from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    chat_history: str
class URLRequest(BaseModel):
    url: str
class DeleteRequest(BaseModel):
    source: str