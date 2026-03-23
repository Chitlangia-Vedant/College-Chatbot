import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from app.rag import get_retriever_with_sources


#for local version
llm = OllamaLLM(model="phi",temperature=0.2)

retriever = get_retriever_with_sources() 

# Prompt (from langchain-core)
prompt = PromptTemplate(
    input_variables=["chat_history", "question"],
    template="""
You are a helpful assistant.

Conversation so far:
{chat_history}

User question:
{question}

Answer clearly and concisely:
"""
)


rag_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Answer the question ONLY using the context below.
If the answer is not present, say "I don't know".

Conversation so far:
{chat_history}

Context:
{context}

Question:
{question}

Answer:
"""
)

def rag_answer(question: str, chat_history: str):
    docs = retriever.invoke(question)

    # 1. If retriever confidence is weak → no answer
    if not docs or len(docs) < 2:
        return {
            "answer": "I don't know. This is not mentioned in the document.",
            "sources": []
        }

    context = "\n\n".join(d.page_content for d in docs)

    answer = llm.invoke(
        rag_prompt.format(
            context=context,
            question=question,
            chat_history=chat_history
        )
    )

    answer_text = answer.strip() if isinstance(answer, str) else str(answer).strip()
    normalized = answer_text.lower()

    # 2. If answer is empty or generic → reject
    if (
        not answer_text
        or "i don't know" in normalized
        or "not mentioned" in normalized
        or "cannot find" in normalized
        or "I'm sorry" in normalized
    ):
        return {
            "answer": "I don't know. This is not mentioned in the document.",
            "sources": []
        }

    # 3. VALID answer → attach sources
    sources = sorted({
        f"{doc.metadata.get('source')} (page {doc.metadata.get('page')})"
        for doc in docs
        if doc.metadata.get("source") is not None
    })

    return {
        "answer": answer_text,
        "sources": sources
    }



rag_chain = (
    {
        "context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
        "question": RunnablePassthrough()
    }
    | rag_prompt
    | llm
)

# Base chain (RunnableSequence)
base_chain = prompt | llm

# Simple in-memory message store
_store = {}

def get_session_history(session_id: str):
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]

# Chain with memory
chat_chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)