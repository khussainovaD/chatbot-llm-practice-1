import streamlit as st
import ollama
import chromadb
from chromadb.config import Settings

persist_directory = "C:/Users/Acer/chromadb_storage"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory))
collection = chroma_client.get_or_create_collection(name="chat_embeddings")

st.title("Llama Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "embeddings" not in st.session_state:
    st.session_state["embeddings"] = []

def get_response(prompt):
    client = ollama.Client()
    response = client.generate(model="llama3.2:1b", prompt=prompt)
    return response["response"]

def generate_embedding(text):
    client = ollama.Client()
    response = client.embeddings(model="llama3.2:1b", prompt=text)
    return response['embedding']


st.subheader("Chat")

with st.container():
    st.markdown(
        """
        <style>
        .chat-message {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 10px;
        }
        .chat-user {
            background-color: #d1ffd6;
            text-align: left;
        }
        .chat-bot {
            background-color: #f1f1f1;
            text-align: left;
        }
        </style>
        """, unsafe_allow_html=True
    )

    for message in st.session_state["messages"]:
        if message["user"] == "You":
            st.markdown(f"<div class='chat-message chat-user'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message chat-bot'><strong>Bot:</strong> {message['content']}</div>", unsafe_allow_html=True)

with st.container():
    user_input = st.text_input("Type your message here...")

    if st.button("Send"):
        if user_input.strip():
            st.session_state["messages"].append({"user": "You", "content": user_input})
            try:
                bot_response = get_response(user_input)
                st.session_state["messages"].append({"user": "Bot", "content": bot_response})

                # Generate embeddings
                user_embedding = generate_embedding(user_input)
                st.session_state["embeddings"].append({"user": "You", "embedding": user_embedding})
                collection.add(
                    ids=[f"user_{len(st.session_state['messages'])}"],
                    embeddings=[user_embedding],
                    documents=[user_input]
                )

                bot_embedding = generate_embedding(bot_response)
                st.session_state["embeddings"].append({"user": "Bot", "embedding": bot_embedding})
                collection.add(
                    ids=[f"bot_{len(st.session_state['messages'])}"],
                    embeddings=[bot_embedding],
                    documents=[bot_response]
                )

            except Exception as e:
                st.error(f"Error: {e}")

with st.sidebar:
    st.subheader("Search History")
    search_query = st.text_input("Search messages or embeddings")

    if st.button("Search"):
        if search_query.strip():
            try:
                query_embedding = generate_embedding(search_query)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5
                )
                st.write("Search Results:")
                for document in results.get("documents", [[]])[0]:
                    st.write(f"- {document}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.subheader("Embeddings")
    for embedding in st.session_state["embeddings"]:
        with st.expander(f"{embedding['user']} embedding"):
            st.json(embedding['embedding'])
