# 🎓 College Chatbot — Teammate Setup Guide
---

## 📚 Table of Contents

1. [What is this project?](#what-is-this-project)
2. [What you need to install](#what-you-need-to-install)
3. [Step 1 — Install Git](#step-1--install-git)
4. [Step 2 — Install Python](#step-2--install-python)
5. [Step 3 — Install VS Code](#step-3--install-vs-code)
6. [Step 4 — Install Ollama and pull the AI model](#step-4--install-ollama-and-pull-the-ai-model)
7. [Step 5 — Get the project on your computer](#step-5--get-the-project-on-your-computer)
8. [Step 6 — Set up your Python environment](#step-6--set-up-your-python-environment)
9. [Step 7 — Run the project](#step-7--run-the-project)
10. [How to work with Git daily](#how-to-work-with-git-daily)
11. [Project structure explained](#project-structure-explained)
12. [Common problems and fixes](#common-problems-and-fixes)

---

## What is this project?

This is a **College Chatbot** built using a RAG (Retrieval-Augmented Generation) architecture.  
It lets you upload college documents (PDFs) and ask questions about them — the AI answers using only the content of those documents.

**Tech stack:**
- **FastAPI** — backend server that handles API requests
- **Ollama + Phi model** — runs the AI locally on your computer, no internet or API key needed
- **LangChain** — connects the AI model with the document retrieval system
- **ChromaDB** — stores document content so the chatbot can search through it
- **Streamlit** — the chat interface you interact with in the browser

---

## What you need to install

| Tool | Purpose | Download |
|------|---------|----------|
| Git | Share and sync code with teammates | https://git-scm.com/download/win |
| Python 3.13 | Run the project | https://www.python.org/downloads/ |
| VS Code | Code editor | https://code.visualstudio.com/ |
| Ollama | Run the AI model locally | https://ollama.com/download |

---

## Step 1 — Install Git

Git is a tool that lets multiple people work on the same code without overwriting each other's work.

1. Go to https://git-scm.com/download/win
2. Download and run the installer
3. Keep clicking **Next** with default options — the defaults are fine
4. Click **Finish**

**Verify it worked** — open PowerShell and type:
```powershell
git --version
```
You should see something like `git version 2.x.x`

---

## Step 2 — Install Python

1. Go to https://www.python.org/downloads/
2. Download **Python 3.13**
3. Run the installer
4. ⚠️ **IMPORTANT:** On the first screen, check **"Add Python to PATH"** before clicking Install Now

**Verify it worked:**
```powershell
python --version
```
You should see `Python 3.13.x`

---

## Step 3 — Install VS Code

1. Go to https://code.visualstudio.com/
2. Download and install it
3. Open VS Code and install the **Python extension**:
   - Click the Extensions icon on the left sidebar (looks like 4 squares)
   - Search for `Python`
   - Click **Install** on the one made by Microsoft

---

## Step 4 — Install Ollama and pull the AI model

Ollama runs the AI model locally on your machine — no internet connection or API key required.

1. Go to https://ollama.com/download
2. Download and install the **Windows** version
3. **Restart your computer** after installation
**Verify it worked:**
```powershell
ollama --version
```
4. Open PowerShell and download the AI model the project uses:
```powershell
ollama pull phi
```
> ⏳ This downloads the Phi model — it may take several minutes depending on your internet speed.

**Test Phi Locally**

Run:
```powershell
ollama run phi
```
Ask something simple:

What is FastAPI?

If you get a response → model works locally.

5. For embeddings (important for RAG):
Run:
```powershell
ollama pull nomic-embed-text
```
> ⚠️ If `ollama` is not recognized inside VS Code terminal after installing, fully close and reopen VS Code.

---

## Step 5 — Get the project on your computer

**Cloning** means downloading the project from GitHub to your computer.

1. Open **VS Code**
2. Press **Ctrl + `** (backtick key, top-left of keyboard) to open the terminal
3. Navigate to where you want to save the project. We recommend a simple path like:
```powershell
cd C:\Users\YourName\Documents
```
4. Clone the repository:
```powershell
git clone https://github.com/Chitlangia-Vedant/College-Chatbot.git
```
5. Open the project folder in VS Code:
```powershell
cd College-Chatbot
code .
```

You should now see all project files in the VS Code file explorer on the left.

---

## Step 6 — Set up your Python environment

A **virtual environment** is an isolated space where we install the project's packages without affecting the rest of your computer.

**One-time setup — allow scripts to run in PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Press **Y** then **Enter** when asked.

**Go one level above the project folder** — the virtual environment should sit next to the project, not inside it:
```powershell
cd C:\Users\YourName\Documents
```

**Create the virtual environment:**
```powershell
python -m venv My_Env
```
**[Your project structure should be like this](#project-structure-explained)**

**Activate it:**
```powershell
.\My_Env\Scripts\Activate.ps1
```
✅ You will know it is activated when you see `(My_Env)` at the start of your terminal line.(IMP)

**Go into the backend folder:**
```powershell
cd College-Chatbot\backend
```

**Install all dependencies:**
```powershell
python -m pip install -r requirements.txt
```
> ⏳ This installs all required packages. It may take a few minutes.

**Create your `.env` file:**
```powershell
New-Item .env
```
Keep `.env` empty
### Important: .gitignore

The repository already ignores sensitive files like:

.env  
My_Env/  
vectorstore/

Never commit these files to GitHub.

---

## Step 7 — Run the project

You need **two terminals** open at the same time — one for the backend, one for the frontend.

> ⚠️ Every time you open a new terminal, you must activate the virtual environment first with:
> ```powershell
> C:\Users\YourName\Documents\My_Env\Scripts\Activate.ps1
> ```

### Terminal 1 — Start the Backend

Make sure `(My_Env)` is visible in your terminal, then navigate to the backend folder:

```powershell
cd C:\Users\YourName\Documents\College-Chatbot\backend
python -m uvicorn app.main:app --reload --port 8000
```

✅ You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

You can test the backend by opening your browser at:
```
http://127.0.0.1:8000/docs
```
This shows interactive API documentation where you can test all endpoints.

### Terminal 2 — Start the Frontend

Open a **new terminal** in VS Code with **Ctrl + Shift + `**, activate the venv, then:
```powershell
C:\Users\YourName\Documents\My_Env\Scripts\Activate.ps1
cd C:\Users\YourName\Documents\College-Chatbot\frontend
streamlit run streamlit_app.py
```

✅ Your browser will automatically open the chatbot at:
```
http://localhost:8501
```

### How to use the chatbot:
1. Upload a college PDF document using the upload button
2. Wait for it to say "PDF ingested successfully"
3. Type your question in the chat box
4. The chatbot will answer using only the content from the uploaded document

---

## How to work with Git daily

### Before you start working —
#### 1. Always pull the latest code first:
```powershell
cd C:\Users\YourName\Documents\College-Chatbot
git pull origin main
```
> This downloads any changes your teammates made. **Always do this before starting work.**
#### 2.Always create a new branch before working:
```powershell
git checkout -b your-branch-name (first time) 
# OR 
git checkout your-branch-name (if branch already exists)

git branch (Confirms the branch you are working on)
```
### After making changes — save and share your work:

```powershell
# Step 1 - See what files you changed
git status

# Step 2 - Stage all your changes
git add .

# Step 3 - Save a snapshot with a description
git commit -m "what you changed"

# Step 4 - Share with the team
git push origin your-branch-name
```

**Example commit messages:**
- `git commit -m "Added college FAQ PDF support"`
- `git commit -m "Fixed chat history bug"`
- `git commit -m "Updated frontend UI"`

### The daily workflow in short:
```
git pull                                   → get latest from teammates
git checkout -b your-branch-name           → create a new branch
... do your work ...
git add .                                  → stage changes
git commit -m "explain"                    → save snapshot
git push origin your-branch-name           → share with team
```

---

## Project structure explained

```
Documents/
│
├── My_Env/                     ← Virtual environment (never touch this folder)
│
└── College-Chatbot/            ← The actual project (cloned from GitHub)
    │
    ├── backend/                ← FastAPI server (the brain)
    │   ├── app/
    │   │   ├── __init__.py     ← Makes app a Python package
    │   │   ├── main.py         ← API routes (/ask, /upload-pdf, /ask-pdf)
    │   │   ├── llm.py          ← AI model setup and RAG logic
    │   │   ├── rag.py          ← PDF ingestion and vector search
    │   │   └── schemas.py      ← Data models for API requests
    │   │
    │   ├── vectorstore/        ← ChromaDB stores document embeddings here
    │   │                         (Deleting this folder resets the chatbot's knowledge)
    │   │
    │   ├── .env                ← Your local config (never shared on GitHub)
    │   └── requirements.txt    ← All Python dependencies
    │
    └── frontend/
        └── streamlit_app.py    ← The chatbot UI in the browser
```

### API Endpoints (what the backend can do):
| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/` | GET | Check if backend is running |
| `/ask` | POST | Ask the AI a general question |
| `/upload-pdf` | POST | Upload and process a PDF document |
| `/ask-pdf` | POST | Ask a question about the uploaded PDF |

---

## Common problems and fixes

### ❌ "running scripts is disabled on this system"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ "ollama is not recognized" in VS Code terminal
Fully close VS Code and reopen it. If still not working, restart your computer.

### ❌ "No module named uvicorn" or any missing module
Make sure `(My_Env)` is showing in your terminal, then run:
```powershell
python -m pip install -r requirements.txt
```

### ❌ "git push rejected"
Someone else pushed changes before you. Run:
```powershell
git pull
git push
```

### ❌ Virtual environment not activating
Make sure you are pointing to the correct path:
```powershell
C:\Users\YourName\Documents\My_Env\Scripts\Activate.ps1
```

### ❌ Chatbot gives wrong or empty answers
- Make sure Ollama is running — open a new terminal and type `ollama serve`
- Make sure you uploaded a PDF before asking questions
- Try deleting the `vectorstore` folder and re-uploading your PDF

### ❌ Merge conflict after git pull

If Git shows a conflict:

1. Open the conflicting file
2. Look for:
```
<<<<<<< HEAD
your code
=======
teammate code
>>>>>>> branch
```

3. Choose the correct code
4. Save the file

Then run:
```powershell
git add .
git commit -m "Resolved merge conflict"
```

