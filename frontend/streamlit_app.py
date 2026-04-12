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

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [[]]

if "current_chat" not in st.session_state:
    st.session_state.current_chat = 0

# ── CURRENT CHAT ──
messages = st.session_state.chat_sessions[st.session_state.current_chat]

# ── HEADER ──
st.markdown("""
<div style="padding:10px 0; text-align:center;">
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
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── INPUT ──
question = st.chat_input("💬 Ask anything about SGSITS...")

if question:
    with st.chat_message("user"):
        st.markdown(question)
    
    messages.append({"role": "user", "content": question})

    history_str = "\n".join(
        [f"{m['role']}: {m['content']}" for m in messages[-6:-1]] 
    )

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
                
                full_response = st.write_stream(stream_data)
            else:
                full_response = f"⚠️ Backend Error: {response.status_code}"
                st.error(full_response)
                
            session.close()

        except Exception as e:
            full_response = f"❌ Error: {str(e)}"
            st.error(full_response)

    messages.append({"role": "assistant", "content": full_response})
