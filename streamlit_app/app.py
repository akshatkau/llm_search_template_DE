import streamlit as st
import requests

st.title("🔍 LLM-based RAG Search")

# Input for user query
query = st.text_input("Enter your query:")

if st.button("Search"):
    st.write("Searching and generating answer...")
    
    try:
        # Make POST request to Flask API
        response = requests.post(
            "http://localhost:5001/query",  # or use your server URL if deployed
            json={"query": query}
        )

        if response.status_code == 200:
            # Display the generated answer
            answer = response.json().get('answer', "No answer received.")
            st.markdown(f"**Answer:** {answer}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"Request failed: {e}")
