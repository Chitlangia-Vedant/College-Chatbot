import os
import streamlit as st
import requests
from dotenv import load_dotenv
from pathlib import Path 

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_BASE = "http://127.0.0.1:8000"
ADMIN_PASSWORD = "sgsits@admin123"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
HEADERS = {"X-API-Key": ADMIN_API_KEY}

st.set_page_config(
    page_title="SGSITS Admin Panel",
    page_icon="🔒",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: #0A0F1A; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; max-width: 100% !important; }

    .hero-header {
        background: linear-gradient(135deg, #0A1020 0%, #0D1830 50%, #111E3A 100%);
        padding: 0 48px; min-height: 110px;
        display: flex; align-items: center; justify-content: space-between;
        position: relative; overflow: hidden;
    }
    .hero-header::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(90deg, transparent, transparent 80px,
            rgba(200,149,42,0.03) 80px, rgba(200,149,42,0.03) 81px);
        pointer-events: none;
    }
    .hero-header::after {
        content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, transparent 0%, #8B1A1A 20%, #C8952A 50%, #8B1A1A 80%, transparent 100%);
    }
    .hero-left { display: flex; align-items: center; gap: 22px; z-index: 1; }
    .hero-emblem {
        width: 76px; height: 76px;
        background: linear-gradient(145deg, #6B1A1A, #A0322A, #8B1A1A);
        border-radius: 18px; display: flex; align-items: center; justify-content: center;
        font-size: 2.4rem; flex-shrink: 0;
        box-shadow: 0 6px 24px rgba(139,26,26,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
        position: relative;
    }
    .hero-emblem::after {
        content: ''; position: absolute; inset: 3px;
        border-radius: 15px; border: 1px solid rgba(255,255,255,0.08); pointer-events: none;
    }
    .hero-institute-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.6rem; font-weight: 600; color: #FFFFFF; line-height: 1.2; margin-bottom: 5px;
    }
    .hero-tagline {
        font-size: 0.7rem; color: #C8952A;
        letter-spacing: 3.5px; text-transform: uppercase; font-weight: 500;
    }
    .hero-right { display: flex; align-items: center; gap: 10px; z-index: 1; }
    .admin-badge {
        background: rgba(139,26,26,0.2); border: 1px solid rgba(200,80,80,0.3);
        border-radius: 20px; padding: 7px 16px; font-size: 0.7rem;
        color: #FF9090; letter-spacing: 2px; text-transform: uppercase; font-weight: 600;
    }
    .api-ok {
        background: rgba(76,175,80,0.15); border: 1px solid rgba(76,175,80,0.3);
        border-radius: 20px; padding: 7px 16px; font-size: 0.7rem;
        color: #4CAF50; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600;
        display: flex; align-items: center; gap: 6px;
    }
    .api-fail {
        background: rgba(244,67,54,0.15); border: 1px solid rgba(244,67,54,0.3);
        border-radius: 20px; padding: 7px 16px; font-size: 0.7rem;
        color: #F44336; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600;
        display: flex; align-items: center; gap: 6px;
    }
    .api-dot-green { width: 7px; height: 7px; background: #4CAF50; border-radius: 50%; box-shadow: 0 0 6px #4CAF50; }
    .api-dot-red   { width: 7px; height: 7px; background: #F44336; border-radius: 50%; box-shadow: 0 0 6px #F44336; }

    .login-outer { display: flex; justify-content: center; padding-top: 80px; }
    .login-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(200,149,42,0.2);
        border-top: 3px solid #C8952A; border-radius: 20px; padding: 52px 48px;
        width: 100%; max-width: 420px; backdrop-filter: blur(10px); text-align: center;
    }
    .login-icon { font-size: 3rem; margin-bottom: 20px; display: block; }
    .login-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.9rem; color: #FFFFFF; margin-bottom: 8px; font-weight: 600;
    }
    .login-subtitle { font-size: 0.85rem; color: #445566; margin-bottom: 32px; line-height: 1.6; }

    .stats-row { display: flex; gap: 16px; margin: 32px 0; }
    .stat-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(200,149,42,0.15);
        border-top: 3px solid #C8952A; border-radius: 14px; padding: 22px 24px;
        flex: 1; position: relative; overflow: hidden;
    }
    .stat-number {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem; color: #E8B84B; font-weight: 600; line-height: 1; margin-bottom: 8px;
    }
    .stat-label { font-size: 0.72rem; color: #445566; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 500; }

    .section-hdr {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem; color: #C8B88A; font-weight: 600;
        margin: 36px 0 16px 0; padding-bottom: 10px;
        border-bottom: 1px solid rgba(200,149,42,0.2);
        display: flex; align-items: center; gap: 10px; position: relative;
    }
    .section-hdr::after {
        content: ''; position: absolute; bottom: -1px; left: 0;
        width: 60px; height: 2px; background: #C8952A;
    }

    .doc-row {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(200,149,42,0.12);
        border-left: 3px solid #C8952A; border-radius: 12px; padding: 14px 20px;
        margin-bottom: 10px; display: flex; align-items: center;
        justify-content: space-between; transition: all 0.2s;
    }
    .doc-row:hover { background: rgba(200,149,42,0.05); border-color: rgba(200,149,42,0.25); }
    .doc-name { font-weight: 500; font-size: 0.9rem; color: #C8D0DC; }
    .doc-meta { font-size: 0.78rem; color: #445566; margin-top: 3px; }
    .doc-badge-pdf  { background: rgba(200,149,42,0.1); border: 1px solid rgba(200,149,42,0.25); border-radius: 20px; padding: 5px 14px; font-size: 0.72rem; color: #C8952A; font-weight: 500; }
    .doc-badge-csv  { background: rgba(76,175,80,0.1);  border: 1px solid rgba(76,175,80,0.25);  border-radius: 20px; padding: 5px 14px; font-size: 0.72rem; color: #4CAF50; font-weight: 500; }
    .doc-badge-url  { background: rgba(33,150,243,0.1); border: 1px solid rgba(33,150,243,0.25); border-radius: 20px; padding: 5px 14px; font-size: 0.72rem; color: #2196F3; font-weight: 500; }

    .stButton > button {
        background: linear-gradient(135deg, #C8952A, #E8B84B) !important;
        color: #0A1020 !important; border: none !important;
        border-radius: 10px !important; font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important; padding: 11px 24px !important;
        font-size: 0.88rem !important;
        box-shadow: 0 4px 14px rgba(200,149,42,0.3) !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(200,149,42,0.5) !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stSidebar"] { background: #080D18 !important; border-right: 1px solid rgba(200,149,42,0.1) !important; }
    [data-testid="stSidebar"] > div { padding-top: 28px !important; }
    [data-testid="stSidebar"] .stButton > button { width: 100% !important; }
    [data-testid="stSidebar"] h4 { color: #C8B88A !important; font-family: 'Cormorant Garamond', serif !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] small { color: #445566 !important; }

    .content-area { max-width: 920px; margin: 0 auto; padding: 0 28px 60px 28px; }

    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1.5px dashed rgba(200,149,42,0.25) !important;
        border-radius: 12px !important;
    }
    .stAlert { border-radius: 12px !important; }
    
    .api-status-panel {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(200,149,42,0.15);
        border-radius: 14px; padding: 20px 24px; margin-bottom: 20px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .api-status-info { display: flex; align-items: center; gap: 14px; }
    .api-status-text-label { font-size: 0.7rem; color: #445566; letter-spacing: 1.5px; text-transform: uppercase; }
    .api-status-text-val { font-size: 0.95rem; color: #C8D0DC; font-weight: 500; margin-top: 2px; }
    .pulse-green {
        width: 14px; height: 14px; background: #4CAF50; border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(76,175,80,0.4);
        animation: pulse-green 2s infinite;
    }
    .pulse-red { width: 14px; height: 14px; background: #F44336; border-radius: 50%; }
    @keyframes pulse-green {
        0%   { box-shadow: 0 0 0 0 rgba(76,175,80,0.5); }
        70%  { box-shadow: 0 0 0 10px rgba(76,175,80,0); }
        100% { box-shadow: 0 0 0 0 rgba(76,175,80,0); }
    }
</style>
""", unsafe_allow_html=True)

# ── Session State (REDUCED) ──
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "api_status" not in st.session_state:
    st.session_state.api_status = None


def verify_api():
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


if st.session_state.api_status is None:
    st.session_state.api_status = verify_api()

api_ok = st.session_state.api_status

if api_ok:
    api_badge = '<div class="api-ok"><div class="api-dot-green"></div>API Online</div>'
else:
    api_badge = '<div class="api-fail"><div class="api-dot-red"></div>API Offline</div>'

st.markdown(f"""
<div class="hero-header">
    <div class="hero-left">
        <div class="hero-emblem">🔒</div>
        <div>
            <div class="hero-institute-name">Shri Govindram Seksaria Institute of Technology and Science</div>
            <div class="hero-tagline">Document Management System &nbsp;·&nbsp; Restricted Access</div>
        </div>
    </div>
    <div class="hero-right">
        {api_badge}
        <div class="admin-badge">Admin Panel</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════
if not st.session_state.admin_logged_in:
    st.markdown('<div class="login-outer">', unsafe_allow_html=True)
    st.markdown("""
<div class="login-card">
    <span class="login-icon">🔐</span>
    <div class="login-title">Admin Login</div>
    <div class="login-subtitle">This panel is restricted to authorized<br>college staff only.</div>
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        password = st.text_input("Password", type="password", placeholder="Enter admin password", label_visibility="collapsed")
        if st.button("Login →", use_container_width=True):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password. Access denied.")

# ══════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════
else:
    with st.sidebar:
        st.markdown("#### 🔒 Admin Panel")
        st.caption("Logged in as Administrator")
        st.markdown("---")

        if api_ok:
            st.success("✅ Backend API is online")
        else:
            st.error("❌ Backend API is offline")
            st.caption(f"Trying: {API_BASE}")

        st.markdown("---")

        if st.button("🔄 Refresh API Status"):
            st.session_state.api_status = verify_api()
            st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.session_state.api_status = None
            st.rerun()

        st.markdown("---")
        st.caption("Upload official SGSITS documents (PDF, CSV) or add website URLs.")

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    dot_class  = "pulse-green" if api_ok else "pulse-red"
    status_val = f"Connected · {API_BASE}" if api_ok else f"Unreachable · {API_BASE}"
    status_col = "#4CAF50" if api_ok else "#F44336"
    st.markdown(f"""
<div class="api-status-panel">
    <div class="api-status-info">
        <div class="{dot_class}"></div>
        <div>
            <div class="api-status-text-label">Backend API Status</div>
            <div class="api-status-text-val" style="color:{status_col};">{status_val}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    if not api_ok:
        st.warning("⚠️ Backend API is not reachable. Document ingestion will not work until the backend server is running.")

    # --- DYNAMICALLY FETCH DATA FROM BACKEND ---
    current_documents = []
    if api_ok:
        try:
            res = requests.get(f"{API_BASE}/list-sources", timeout=5)
            if res.status_code == 200:
                sources = res.json().get("sources", [])
                for src in sources:
                    if src.startswith("http"):
                        current_documents.append({"name": src, "type": "URL", "icon": "🌐", "source": src, "meta": "Active in ChromaDB"})
                    elif src.endswith(".csv"):
                        current_documents.append({"name": src, "type": "CSV", "icon": "📊", "source": src, "meta": "Active in ChromaDB"})
                    else:
                        current_documents.append({"name": src, "type": "PDF", "icon": "📄", "source": src, "meta": "Active in ChromaDB"})
        except Exception as e:
            st.error("Could not load sources from database.")
    # -------------------------------------------

    total_docs   = len(current_documents)
    total_pdfs   = sum(1 for d in current_documents if d.get("type") == "PDF")
    total_csvs   = sum(1 for d in current_documents if d.get("type") == "CSV")
    total_urls   = sum(1 for d in current_documents if d.get("type") == "URL")

    # The 4-column stat layout automatically spaces beautifully
    st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">{total_docs}</div>
        <div class="stat-label">Total Sources</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_pdfs}</div>
        <div class="stat-label">PDFs Ingested</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_csvs}</div>
        <div class="stat-label">CSVs Ingested</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_urls}</div>
        <div class="stat-label">URLs Ingested</div>
    </div>
</div>
""", unsafe_allow_html=True)

    # ════════════════════════════════════════
    # SECTION 1: Upload PDF
    # ════════════════════════════════════════
    st.markdown('<div class="section-hdr">📄 Upload PDF Documents</div>', unsafe_allow_html=True)
    st.caption("Upload official PDFs — syllabus, notices, fee structure, regulations, circulars, etc.")

    uploaded_pdfs = st.file_uploader(
        "Choose PDF files", type=["pdf"],
        accept_multiple_files=True, label_visibility="collapsed", key="pdf_uploader"
    )

    if uploaded_pdfs and st.button("📥 Ingest PDFs into Knowledge Base"):
        with st.spinner("Ingesting PDFs..."):
            success_count = 0
            for file in uploaded_pdfs:
                try:
                    response = requests.post(
                        f"{API_BASE}/upload-pdf",
                        files={"file": (file.name, file, "application/pdf")},
                        headers=HEADERS
                    )
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        st.error(f"Failed to ingest: {file.name} (Status {response.status_code})")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend server.")
                    break
        if success_count > 0:
            st.success(f"✅ Successfully ingested {success_count} PDF(s)!")
            st.rerun() # This will refresh the page and auto-fetch the new docs from backend!

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    # SECTION 2: Upload CSV
    # ════════════════════════════════════════
    st.markdown('<div class="section-hdr">📊 Upload CSV Data</div>', unsafe_allow_html=True)
    st.caption("Upload CSV files with 'Question' and 'Answer' columns.")

    uploaded_csvs = st.file_uploader(
        "Choose CSV files", type=["csv"],
        accept_multiple_files=True, label_visibility="collapsed", key="csv_uploader"
    )

    if uploaded_csvs and st.button("📥 Ingest CSVs into Knowledge Base"):
        with st.spinner("Ingesting CSVs..."):
            success_count = 0
            for file in uploaded_csvs:
                try:
                    response = requests.post(
                        f"{API_BASE}/upload-csv",
                        files={"file": (file.name, file, "text/csv")},
                        headers=HEADERS 
                    )
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        # Extract error detail if possible
                        err_msg = response.json().get("detail", f"Status {response.status_code}")
                        st.error(f"Failed to ingest {file.name}: {err_msg}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend server.")
                    break
        if success_count > 0:
            st.success(f"✅ Successfully ingested {success_count} CSV(s)!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    # SECTION 3: Add Website URL
    # ════════════════════════════════════════
    st.markdown('<div class="section-hdr">🌐 Add Website URL</div>', unsafe_allow_html=True)
    st.caption("Scrape and ingest content from official SGSITS web pages.")

    url_input = st.text_input(
        "Website URL",
        placeholder="https://sgsits.ac.in/...",
        label_visibility="collapsed",
        key="url_input"
    )

    if st.button("🌐 Ingest URL into Knowledge Base"):
        if not url_input.strip():
            st.warning("Please enter a URL.")
        else:
            with st.spinner(f"Scraping and ingesting {url_input.strip()}..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/upload-url",
                        json={"url": url_input.strip()},
                        headers=HEADERS,  
                        timeout=120
                    )
                    if res.status_code == 200:
                        st.success("✅ URL ingested successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to ingest URL. (Status {res.status_code})")
                except requests.exceptions.ConnectionError:
                    st.error("📡 Cannot connect to backend server.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    # SECTION 4: Document List with Delete & Update
    # ════════════════════════════════════════
    st.markdown('<div class="section-hdr">🗂️ Ingested Knowledge Sources</div>', unsafe_allow_html=True)
    st.caption("View, re-ingest (URLs), or remove sources from the knowledge base.")

    if not current_documents:
        st.info("No documents found in the database. Upload PDFs, CSVs, or add URLs above.")
    else:
        for i, doc in enumerate(current_documents):
            doc_type = doc.get("type", "PDF")

            if doc_type == "PDF":
                badge_html = '<span class="doc-badge-pdf">PDF · Ingested</span>'
            elif doc_type == "CSV":
                badge_html = '<span class="doc-badge-csv">CSV · Ingested</span>'
            else:
                badge_html = '<span class="doc-badge-url">URL · Ingested</span>'

            st.markdown(f"""
<div class="doc-row">
    <div>
        <div class="doc-name">{doc['icon']} {doc['name']}</div>
        <div class="doc-meta">{doc['meta']}</div>
    </div>
    {badge_html}
</div>
""", unsafe_allow_html=True)

            # Creating columns for the action buttons
            if doc_type == "URL":
                btn_col1, btn_col2, btn_col3 = st.columns([0.65, 0.2, 0.15])
            else:
                btn_col1, btn_col3 = st.columns([0.85, 0.15])

            if doc_type == "URL":
                with btn_col2:
                    if st.button("🔄 Update", key=f"update_{i}", use_container_width=True):
                        with st.spinner(f"Re-ingesting {doc['name']}..."):
                            try:
                                res = requests.post(
                                    f"{API_BASE}/update-url",
                                    json={"url": doc["source"]},
                                    headers=HEADERS,
                                    timeout=120
                                )
                                if res.status_code == 200:
                                    st.success(f"✅ {doc['name']} re-ingested successfully!")
                                else:
                                    st.error("❌ Re-ingest failed.")
                            except Exception:
                                st.error("📡 Connection error during re-ingest.")

            with btn_col3:
                if st.button("🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                    with st.spinner("Deleting..."):
                        try:
                            res = requests.post(
                                f"{API_BASE}/delete-source",
                                json={"source": doc["source"]},
                                headers=HEADERS,
                                timeout=10
                            )
                            if res.status_code == 200:
                                st.toast("🗑️ Document removed from knowledge base.")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete.")
                        except Exception:
                            st.error("📡 Connection error during deletion.")

        st.markdown("---")
        st.caption(f"Total sources: **{total_docs}** &nbsp;·&nbsp; "
                   f"PDFs: **{total_pdfs}** &nbsp;·&nbsp; "
                   f"CSVs: **{total_csvs}** &nbsp;·&nbsp; "
                   f"URLs: **{total_urls}**")

    st.markdown('</div>', unsafe_allow_html=True)