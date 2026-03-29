import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

from langchain_core.prompts import PromptTemplate
from app.rag import get_retriever_with_sources


#for local version
llm = OllamaLLM(model="phi",temperature=0.2)

retriever = get_retriever_with_sources() 

rag_prompt = PromptTemplate(
    input_variables=["context", "question", "chat_history"],
    template="""
    You are the official, helpful FAQ assistant for the college.
    Answer the user's question accurately using ONLY the context provided below.
    If the answer is not present in the context, politely state that you do not have that specific information and advise the user to contact the administration at admissions@college.edu.

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
            "answer": "I do not have that specific information. Please contact the administration at admissions@college.edu.",
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
            "answer": "I do not have that specific information. Please contact the administration at admissions@college.edu.",
            "sources": []
        }

    # 3. VALID answer → attach sources dynamically
    raw_sources = set()
    for doc in docs:
        source_name = doc.metadata.get("source")
        if not source_name:
            continue
            
        # If it's a PDF, it will have a 'page'
        if "page" in doc.metadata:
            raw_sources.add(f"{source_name} (Page {doc.metadata.get('page')})")
        # If it's a CSV, it might have a 'row'
        elif "row" in doc.metadata:
            raw_sources.add(f"{source_name} (Row {doc.metadata.get('row')})")
        # If it's a scraped website or question column, just use the name
        else:
            raw_sources.add(source_name)

    sources = sorted(list(raw_sources))

    return {
        "answer": answer_text,
        "sources": sources
    }