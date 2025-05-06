from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from utils import search_articles, concatenate_content, generate_flexible_answer

load_dotenv()
app = Flask(__name__)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    user_query = data.get("query")
    session_id = data.get("session_id", "default")  # unique per user/session

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    print("Received query:", user_query)

    # Step 1: Search articles
    articles = search_articles(user_query)
    print(f"Found {len(articles)} articles:")
    for article in articles:
        print(f"- {article['title']}: {article['link']}")

    # Step 2: Concatenate content
    content = concatenate_content(articles)
    print(f"First 200 chars of scraped content: {content[:200]}...")

    # Step 3: Generate answer with memory
    answer = generate_flexible_answer(user_query, session_id=session_id)
    return jsonify({"answer": str(answer)})


if __name__ == '__main__':
    app.run(host='localhost', port=5001)
