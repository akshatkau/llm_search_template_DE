# 🔍 LLM-based RAG Search System

This project is a **Retrieval-Augmented Generation (RAG)** application powered by **Large Language Models (LLMs)**. It combines real-time web search, article scraping, and LLM-based contextual answer generation into a simple, interactive interface using **Flask (backend)** and **Streamlit (frontend)**.

---

## 🚀 Features

- 🔎 Search the web for recent articles related to a query
- 🧠 Uses scraped article content to answer contextually
- 🗣️ Maintains conversation history (memory) using LangChain
- 🔄 Supports **Together API** (Mistral) for LLM responses
- 🖥️ Simple, clean UI with Streamlit

---

## 📁 Project Structure

llm_search_template/
│
├── flask_app/ # Backend Flask app
│ ├── app.py # Flask server
│ └── utils.py # Core logic: search, scrape, answer generation
│
├── streamlit_app/ # Streamlit frontend
│ └── app.py # User interface
│
├── .env.example # Example environment config (no secrets)
├── requirements.txt # Dependencies
└── README.md # You are here


---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/llm_search_template.git
cd llm_search_template
```

### 2️⃣ Create Virtual Environment
With venv
``` bash
python -m venv env
source env/bin/activate      # Windows: env\Scripts\activate
```

Or with conda
``` bash
conda create --name llm_rag python=3.8
conda activate llm_rag
```

### 3️⃣ Install Requirements
``` bash
pip install -r requirements.txt
```

## 🔐 Environment Variables
Create a .env file in the root directory with the following:
``` bash
SEARCH_API_KEY=google_cse_api_key
SEARCH_ENGINE_ID=google_search_engine_id
TOGETHER_API_KEY=together_api_key
# Optional for future use:
# OPENAI_API_KEY=openai_api_key
```

## ▶️ Running the App
Start Backend (Flask)
``` bash
cd flask_app
python app.py
```

Start Frontend (Streamlit)
In a new terminal:
``` bash
cd streamlit_app
streamlit run app.py
```

##💡 How It Works
-User enters a query in Streamlit UI

-Flask API receives it and performs:

-Google Search (CSE API)

-Scraping relevant articles (via BeautifulSoup)

-Compiling context and calling Together API (Mistral model)

-Answer is generated and sent back to frontend

-Optionally uses LangChain Memory to hold session history


## 📦 Requirements
-Python 3.8+

-Flask

-Streamlit

-requests, BeautifulSoup

-langchain, langchain-openai, langchain-together

-python-dotenv


## 🛡️ Disclaimer
-This app does not have real-time awareness — it generates responses based on scraped article content and model predictions.

