# SHL Assessment Recommender – AI-Powered Assessment Selection

An automated conversational agent and API designed to act as an expert advisor for selecting SHL assessments. The system seamlessly guides users through a multi-turn conversation, extracting their hiring needs, enforcing business constraints, and querying a comprehensive catalog to recommend the perfect tests for any job role.

This project is built with strict performance and reliability requirements, focusing on sub-second latency, deterministic state extraction, and graceful adherence to conversation limits.

---

## 🚀 Key Features

*   **Ultra-Fast State Extraction**
    Utilizes highly-optimized deterministic heuristics and keyword matching instead of heavy asynchronous LLM calls, reliably keeping system latency under 1 second per turn while accurately parsing user intent.

*   **Hybrid Recommendation Engine**
    Combines semantic catalog search with hard-coded business rules to ensure accurate, hallucination-free assessment recommendations curated strictly from the official SHL catalog.

*   **Strict Policy Guardrails**
    *   **Turn Capping:** Automatically finalizes conversations and enforces recommendations at a strict 8-turn limit.
    *   **Off-Topic Deflection:** Instantly identifies and deflects legal, regulatory, and non-hiring related questions.
    *   **Vague Query Handling:** Refuses to recommend on Turn 1 if the initial input is too vague or conversational.

*   **Production-Ready Backend & UI**
    *   **RESTful API:** Built on **FastAPI** offering structured `/chat` and `/health` endpoints.
    *   **Interactive Tester:** Includes a lightweight HTML/JS frontend (`test.html`) to instantly chat with the agent locally.

---

## 🧠 System Architecture

1.  **State Machine Layer (`state_machine.py`)**
    Extracts structured conversation state (role, skills, intent, inclusions/exclusions) from the chat history purely through blazing-fast heuristics.

2.  **Agent & Constraint Layer (`agent.py`)**
    Acts as the brain, enforcing hard policies (turn limits, off-topic filtering) and deciding whether to ask clarifying questions or proceed to recommendations.

3.  **Retrieval Engine (`retrieval.py` & `catalog.py`)**
    Ingests the local `catalog.json` and performs hybrid search logic, filtering out disqualified items and enforcing exact URL matches.

4.  **Generative Layer (`llm.py`)**
    When triggered, connects to the OpenAI/OpenRouter API to format a grounded, natural-language response incorporating the retrieved recommendations.

---

## 📁 Project Structure

```
SHL Assessment Recommender/
├── .venv/                  # Virtual environment
├── app/                    # Application source code
│   ├── __init__.py
│   ├── agent.py            # Hard policies and decision logic
│   ├── catalog.py          # Data loading logic
│   ├── llm.py              # Generative/Template formatting
│   ├── main.py             # FastAPI entrypoint
│   ├── retrieval.py        # Search and filtering logic
│   ├── schemas.py          # Pydantic data models
│   └── state_machine.py    # Sub-second state extraction
├── data/
│   └── catalog.json        # Assessment catalog database
├── test.html               # Lightweight Chat UI
├── Procfile                # Deployment configuration
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version definition
└── README.md               # Project documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd "SHL Assessment Recommender"
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python -m venv .venv
```

**Windows**

```bash
.\.venv\Scripts\Activate.ps1
```

**Mac / Linux**

```bash
source .venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory and add your LLM API keys:

```env
LLM_PROVIDER=openai  # or openrouter
OPENAI_API_KEY=your_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

---

## ▶️ Usage

### 🔹 Run the Backend API

To start the FastAPI server:

```bash
uvicorn app.main:app --reload
```
*The API will start running on `http://127.0.0.1:8000`.*

### 🔹 Use the Chat UI
Simply open `test.html` in your web browser. Type your queries directly into the chat interface to simulate the multi-turn grading harness.

---

## 🛠 Tech Stack

*   **Language:** Python 3.13
*   **Web Framework:** FastAPI & Uvicorn
*   **Data Validation:** Pydantic
*   **LLM Provider:** OpenAI / OpenRouter
*   **Deployment config:** Procfile & requirements.txt
