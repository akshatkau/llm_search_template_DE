import streamlit as st
import requests

#App Title
st.set_page_config(page_title="LLM-based RAG Search", page_icon="🔍")
st.title("🔍 LLM-based RAG Search")

st.markdown("""
Welcome to the **LLM-based Retrieval-Augmented Generation (RAG)** system!  
This app allows you to ask any question and get a response based on web content.""")

#Sidebar Info
with st.sidebar:
    st.header("🧠 How it Works")
    st.markdown("""
    1. Enter your question in the text box.
    2. The backend:
        - Uses Google Search API to fetch articles.
        - Scrapes and compiles relevant content.
        - Passes the content + your query to the LLM (Mistral via Together API).
    3. You get a contextual response here!

    Make sure the Flask backend is running at `http://localhost:5001`.
    """)

#Query
query = st.text_input("💬 Enter your query:")

if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a valid query.")
    else:
        st.info("Searching and generating answer...")
        try:
            response = requests.post("http://localhost:5001/query", json={"query": query})

            if response.status_code == 200:
                answer = response.json().get("answer", "⚠️ No answer received.")
                st.markdown("### 📌 Answer:")
                st.markdown(answer)
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"❌ Request failed: {e}")
