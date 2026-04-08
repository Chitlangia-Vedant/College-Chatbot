import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from app.rag import get_retriever_with_sources
import time
from app.logger import setup_logger
import urllib3
from langchain_core.globals import set_llm_cache, get_llm_cache
from langchain_community.cache import SQLiteCache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Enable caching. This saves exact prompt matches to a local database.
# If someone asks the exact same question, it answers instantly without hitting Ollama.
set_llm_cache(SQLiteCache(database_path=".langchain.db"))
llm = ChatOllama(model="llama3.2", temperature=0.0)
retriever = get_retriever_with_sources() 
logger = setup_logger("llm_engine")

# --- The Reformulation Prompt ---
rephrase_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a strict query reformulator for SGSITS College. Your job is to rewrite the user's question to be standalone and optimized for a database search.\n"
        "CRITICAL RULES:\n"
        "1. Expand common college acronyms (e.g., 'CSE' -> 'Computer Science Engineering', 'IT' -> 'Information Technology', 'ECE' -> 'Electronics and Communication').\n"
        "2. DO NOT answer the question. ONLY output the rewritten query.\n"
        "3. If no context is needed and no acronyms exist, output the user's text exactly as-is."
    ),
    HumanMessagePromptTemplate.from_template(
        "Chat History:\n{chat_history}\n\nFollow Up Input: {question}\n\nStandalone question:"
    )
])

# --- The Main FAQ Prompt ---
rag_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a professional academic assistant for SGSITS college. \n"
        "RULES:\n"
        "1. Answer the question using ONLY the context provided below.\n"
        "2. If the context does not contain the answer, reply exactly with: 'I do not have that specific information. Please contact admissions@sgsits.ac.in.'\n"
        "3. FORMATTING: Always use bullet points, bold text for key terms, and short paragraphs.\n"
        "4. SMALL TALK: If the user just says hello or thank you, respond warmly. \n"
        "5. NO CONVERSATIONAL FILLER: When answering factual questions based on context, DO NOT ask follow-up questions like 'How can I assist you today?'. Just provide the facts and STOP.\n"
        "6. CRITICAL: DO NOT invent, guess, or assume any information.\n"
    ),
    HumanMessagePromptTemplate.from_template(
        # "Chat History (for context):\n{chat_history}\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{question}\n\n"
        "Answer:"
    )
])

def rag_answer_stream(question: str, chat_history: str):
    # --- Step 1. Reformulate the question ---
    standalone_question = question
    
    if chat_history.strip(): 
        response_msg = llm.invoke(
            rephrase_prompt.format(chat_history=chat_history, question=question)
        )
        # Handle AIMessage object correctly
        standalone_question = response_msg.content.strip() if hasattr(response_msg, 'content') else str(response_msg).strip()
        logger.info(f"Action=Reformulate | Original='{question}' | New='{standalone_question}'")

    # --- Step 2. Search using the REFORMULATED question ---
    docs = retriever.invoke(standalone_question)
    
    # [FIXED] Do not short-circuit here. If docs are empty, provide an empty context string.
    context = "\n\n".join(d.page_content for d in docs) if docs else "No documents found."
    
    prompt = rag_prompt.format(context=context, question=standalone_question)

    # 2. Stream from Ollama with Health Check
    logger.info("Action=LLM_Generate | Status=Started")
    start_llm = time.time()
    first_token_received = False
    
    # We will accumulate the text to check if it's just small talk
    full_generated_text = ""
    
    try:
        for chunk in llm.stream(prompt):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_generated_text += content
            
            if not first_token_received:
                ttft = time.time() - start_llm
                logger.info(f"Action=LLM_Generate | Status=First_Token_Streaming | TTFT={ttft:.4f}s")
                first_token_received = True
            yield content
    except Exception as e:
        err_str = str(e)
        if "ConnectionRefusedError" in err_str or "11434" in err_str or "connection error" in err_str.lower():
            logger.critical("Action=LLM_Generate | Status=Ollama_Offline | Error=Cannot connect to Ollama service on port 11434.")
            yield "⚠️ **Internal Error:** The AI service (Ollama) is currently offline. Please ensure the backend service is running."
        else:
            logger.error(f"Action=LLM_Generate | Status=Error | Detail={err_str}")
            yield "I encountered an error while generating the answer."
        return
    
    is_small_talk = "how can i assist you" in full_generated_text.lower() or "how can i help you" in full_generated_text.lower()
    
    is_fallback = "i do not have that specific information" in full_generated_text.lower()

    # 3. Yield Sources
    if not is_small_talk and not is_fallback:
        raw_sources = set()
        for d in docs:
            source = d.metadata.get('source')
            if not source:
                continue
            if "page" in d.metadata:
                raw_sources.add(f"{source} (Page {d.metadata.get('page')})")
            elif "row" in d.metadata:
                raw_sources.add(f"{source} (Row {d.metadata.get('row')})")
            else:
                raw_sources.add(source)

        if raw_sources:
            yield "\n\n📌 **Sources:**\n" + "\n".join(f"- {s}" for s in sorted(list(raw_sources)))

# Not used-kept as a legacy code(Do Not Delete)        
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

def clear_llm_cache():
    """Wipes the SQLite cache to ensure fresh answers after a knowledge base update."""
    cache = get_llm_cache()
    if cache:
        cache.clear()
        logger.info("Action=Clear_Cache | Status=Success | Detail=LLM Cache wiped.")