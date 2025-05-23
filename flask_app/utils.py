import os
import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_together import ChatTogether

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.chains import LLMChain

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from dotenv import load_dotenv
from datetime import date, timedelta


load_dotenv()

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that answers questions based on web content and real-time information. Always include sources or links when relevant."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# _llm = ChatOpenAI(
#     model="gpt-3.5-turbo", 
#     temperature=0.7, 
#     openai_api_key=OPENAI_API_KEY)

_llm = ChatTogether(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.7,
    together_api_key=TOGETHER_API_KEY
)



_session_histories = {}

_chat_with_memory = RunnableWithMessageHistory(
    _prompt_template | _llm,
    lambda session_id: _session_histories.setdefault(session_id, ChatMessageHistory()),
    input_messages_key="input",
    history_messages_key="chat_history"
)




def search_articles(query, num_results=5):
    """
    Uses Google Custom Search API to get recent article links.
    Filters for news published only yesterday.
    """
    url = "https://www.googleapis.com/customsearch/v1"


    print(f"Search API Key present: {bool(SEARCH_API_KEY)}")
    if SEARCH_API_KEY:
        print(f"Search API Key starts with: {SEARCH_API_KEY[:5]}...")
    else:
        print("WARNING: Search API Key is missing!")

    print(f"Search Engine ID present: {bool(SEARCH_ENGINE_ID)}")
    if SEARCH_ENGINE_ID:
        print(f"Search Engine ID starts with: {SEARCH_ENGINE_ID[:5]}...")
    else:
        print("WARNING: Search Engine ID is missing!")

    params = {
        "key": SEARCH_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": num_results,
    }

    try:
        print(f"Sending search request to Google API for query")
        response = requests.get(url, params=params)
        print(f"Search API Response Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response from Search API: {response.text[:500]}")
            return []

        data = response.json()
        print(f"Response keys: {list(data.keys())}")

        if "items" not in data:
            print(f"No 'items' found in response. Full response: {data}")
            if "error" in data:
                print(f"API returned error: {data['error']}")
            return []

        print(f"Found {len(data['items'])} search results")

        articles = []
        for i, item in enumerate(data.get("items", [])):
            title = item.get("title", "No Title")
            link = item.get("link", "No Link")
            print(f"Result {i+1}: {title} - {link}")
            articles.append({"title": title, "link": link})

        return articles

    except Exception as e:
        print(f"Exception in search_articles: {type(e).__name__}: {str(e)}")
        return []


def fetch_article_content(url):
    """
    Scrapes the given URL and extracts headings and paragraph text.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        content = ""
        for tag in soup.find_all(["h1", "h2", "h3", "p"]):
            text = tag.get_text(strip=True)
            if text:
                content += text + "\n"

        return content.strip()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def concatenate_content(articles):
    """
    Fetches and combines content from all article URLs.
    """
    full_text = ""
    for article in articles:
        print(f"Scraping: {article['link']}")
        article_text = fetch_article_content(article["link"])
        full_text += f"\n\n### {article['title']}\n{article_text}"
    return full_text


def generate_flexible_answer(query: str, session_id: str = "default", content: str = None) -> str:
    """
    Generates an answer using:
    - memory-based chat with context injection if `content` is provided
    - otherwise, regular memory-based conversation
    """
    try:
        meta_question_keywords = ["what did i ask", "previous question", "earlier question", 
                                 "what were we discussing", "what was my question"]
        
        is_meta_question = any(keyword in query.lower() for keyword in meta_question_keywords)
        
        if content and not is_meta_question:
            max_chars = 3000
            trimmed_content = content[:max_chars]

            query = f"""Based on the following articles, answer the query clearly. 
Always include sources and links at the end if relevant.
Also remember our conversation history when responding.

---CONTENT---
{trimmed_content}

---QUESTION---
{query}"""

            print("Sending to Together API via LangChain memory-enabled pipeline with context...")

        else:
            if is_meta_question:
                print("Detected meta-question about conversation - using memory only...")
            else:
                print("Using memory-based assistant with no extra content...")

        response = _chat_with_memory.invoke(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content

    except Exception as e:
        print("Error in generate_flexible_answer:", str(e))
        return "Sorry, I encountered an error while generating the response."



