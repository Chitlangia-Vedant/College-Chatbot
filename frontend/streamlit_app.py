import os
import streamlit as st
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SGSITS Assistant",
    page_icon="🎓",
    layout="wide"
)

# ── THEME STATE ──
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [[]]

if "current_chat" not in st.session_state:
    st.session_state.current_chat = 0

# ── THEME CSS ──
def get_css():
    if st.session_state.theme == "dark":
        return """
        <style>
        body {background: #0F172A; color: white;}

        .chat-user {
            background:#1E3A8A; 
            color:white;
            display:inline-block;
            width:fit-content;
            max-width:65%;
            word-wrap:break-word;
            margin-left:auto;
        }

        .chat-bot {
            background:#1F2937; 
            color:#E5E7EB;
            display:inline-block;
            width:fit-content;
            max-width:65%;
            word-wrap:break-word;
        }
        </style>
        """
    else:
        return """
        <style>
        body {background: #F9FAFB; color:black;}

        .chat-user {
            background:#2563EB; 
            color:white;
            display:inline-block;
            width:fit-content;
            max-width:65%;
            word-wrap:break-word;
            margin-left:auto;
        }

        .chat-bot {
            background:#E5E7EB; 
            color:black;
            display:inline-block;
            width:fit-content;
            max-width:65%;
            word-wrap:break-word;
        }
        </style>
        """

st.markdown(get_css(), unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🎓 SGSITS Assistant")

    if st.button("➕ New Chat"):
        st.session_state.chat_sessions.append([])
        st.session_state.current_chat = len(st.session_state.chat_sessions) - 1
        st.rerun()

    st.markdown("---")

    for i, chat in enumerate(st.session_state.chat_sessions):
        label = f"Chat {i+1}"
        if st.button(label, key=f"chat_{i}"):
            st.session_state.current_chat = i
            st.rerun()

    st.markdown("---")

    if st.button("🧹 Clear Current Chat"):
        st.session_state.chat_sessions[st.session_state.current_chat] = []
        st.rerun()

    st.markdown("---")

    if st.button("🌙 Toggle Theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ── CURRENT CHAT ──
messages = st.session_state.chat_sessions[st.session_state.current_chat]

# ── HEADER ──
st.markdown("""
<div style="padding:10px 0;">
<h2>🎓 SGSITS Academic Assistant</h2>
<p style="opacity:0.7;">Ask anything about SGSITS</p>
</div>
""", unsafe_allow_html=True)

# ── EMPTY STATE ──
if not messages:
    st.markdown("""
    <div style="text-align:center; margin-top:80px;">
        <h3>👋 Welcome!</h3>
        <p>Ask about admissions, syllabus, fees, placements.</p>
        <p style="font-size:0.8rem;">Example: "What is SGSITS fee structure?"</p>
    </div>
    """, unsafe_allow_html=True)

# ── CHAT DISPLAY ──
# Use native Streamlit chat messages (this fully supports Markdown!)
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── INPUT ──
question = st.chat_input("💬 Ask anything about SGSITS...")

if question:
    # 1. Display user's question immediately
    with st.chat_message("user"):
        st.markdown(question)
    
    # 2. Add user message to history
    messages.append({"role": "user", "content": question})

    # 3. Create chat history string (EXCLUDING the current question)
    # Using messages[:-1] prevents sending the question twice to the backend
    history_str = "\n".join(
        [f"{m['role']}: {m['content']}" for m in messages[-6:-1]] 
    )

    # 4. Stream response from backend
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            session = requests.Session()
            response = session.post(
                f"{API_BASE}/ask-pdf",
                json={"question": question, "chat_history": history_str},
                stream=True,
                timeout=None
            )

            if response.status_code == 200:
                def stream_data():
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
                
                # Streamlit writes the stream and handles all Markdown naturally
                full_response = st.write_stream(stream_data)
            else:
                full_response = f"⚠️ Backend Error: {response.status_code}"
                st.error(full_response)
                
            session.close()

        except Exception as e:
            full_response = f"❌ Error: {str(e)}"
            st.error(full_response)

    # 5. Save assistant response to state
    messages.append({"role": "assistant", "content": full_response})