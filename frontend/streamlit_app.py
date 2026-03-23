import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="📄",
    layout="wide"
)

# -------------------------------
# Session State Init
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = 1

# -------------------------------
# Sidebar (Documents & Controls)
# -------------------------------
with st.sidebar:
    st.title("📄 RAG Chatbot")
    st.caption("Local Phi • Ollama • Chroma")

    st.divider()
    st.subheader("📂 Upload Documents")

    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("📥 Ingest PDFs"):
        with st.spinner("Ingesting documents..."):
            for file in uploaded_files:
                files = {
                    "file": (file.name, file, "application/pdf")
                }
                response = requests.post(
                    f"{API_BASE}/upload-pdf",
                    files=files
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.documents.append({
                        "name": file.name,
                        "pages": data.get("pages",0),
                        "chunks": data.get("chunks", 0)
                    })
                else:
                    st.error(f"Failed to ingest {file.name}")

        st.success("Documents ingested successfully")

    # -------------------------------
    # Document Summary
    # -------------------------------
    if st.session_state.documents:
        st.divider()
        st.subheader("📊 Document Overview")

        for doc in st.session_state.documents:
            st.markdown(
                f"""
        **{doc['name']}**
        - Pages: `{doc['pages']}`
        - Chunks indexed: `{doc['chunks']}`
        """
            )

    st.divider()

    # -------------------------------
    # New Chat
    # -------------------------------
    if st.button("🧹 New Chat"):
        st.session_state.messages = []
        st.session_state.chat_id += 1
        st.rerun()

# -------------------------------
# Main Chat Area
# -------------------------------
st.header("💬 Ask Questions from Your Documents")

if not st.session_state.documents:
    st.info("Upload and ingest PDFs from the sidebar to begin.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask something about the uploaded documents...")

    if question:

        with st.spinner("Searching documents..."):

            def build_chat_history(messages, max_turns=6):
                history = []
                for msg in messages[-max_turns * 2:]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    history.append(f"{role}: {msg['content']}")
                return "\n".join(history)
            
            chat_history = build_chat_history(st.session_state.messages)

            st.session_state.messages.append(
            {"role": "user", "content": question}
        )

            response = requests.post(
                f"{API_BASE}/ask-pdf",
                json={"question": question, "chat_history": chat_history}
            )

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
        else:
            answer = "Error retrieving answer."
            sources = []


        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )

        if sources and not answer.lower().startswith("i don't know"):
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "📌 **Sources:**\n" + "\n".join(f"- {s}" for s in sources)
                }
            )


        st.rerun()