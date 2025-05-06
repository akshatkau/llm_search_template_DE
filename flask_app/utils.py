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

#_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=OPENAI_API_KEY)

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


def get_yesterday_query(original_query: str) -> str:
    """
    Appends a date filter to the original query to only get articles from yesterday.
    """
    yesterday = date.today() - timedelta(days=1)
    return f"{original_query} after:{yesterday.isoformat()} before:{(yesterday + timedelta(days=1)).isoformat()}"

def search_articles(query, num_results=5):
    """
    Uses Google Custom Search API to get recent article links.
    Filters for news published only yesterday.
    """
    url = "https://www.googleapis.com/customsearch/v1"

    # Apply date filter to query
    query_with_date = get_yesterday_query(query)

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
        "q": query_with_date,
        "num": num_results,
    }

    try:
        print(f"Sending search request to Google API for query: '{query_with_date}'")
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
    Generates an answer using either:
    - memory-based chat if `content` is None
    - context-aware (scraped content) generation if `content` is provided
    """
    try:
        if content:
            prompt = f"""You are a helpful assistant. Based on the information below, answer the question clearly.You can share the news if asked for it.
Always include the source of your information by citing the article titles at the end of your response. Add links to the articles if possible.

---CONTENT---
{content}

---QUESTION---
{query}
"""
            headers = {
                "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }

            print("Sending static OpenAI API request...")
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        else:
            print("Using memory-based assistant with RunnableWithMessageHistory...")
            response = _chat_with_memory.invoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            )
            return response.content

    except Exception as e:
        print("Error in generate_flexible_answer:", str(e))
        return "Sorry, I encountered an error while generating the response."
