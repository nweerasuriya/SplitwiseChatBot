"""
Create Flask app to authenticate with Splitwise API
"""

__date__ = "2024-10-28"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"

__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import streamlit as st

from chatbot import ChatbotWorkflow

st.title("Splitwise Chatbot")
st.markdown("Ask me questions about your Splitwise data!")
st.logo(image="src/logo.png")
st.markdown(
    """
    <style>
    img[data-testid="stLogo"] {
            height: 12rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Splitwise ID input
group_id = st.number_input("Enter your Splitwise Group ID:", value=50024800)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotWorkflow(group_id)
    # Show an initial message from the chatbot displaying all users and categories
    st.session_state.messages.append(
        {
            "role": "user",
            "content": "Show me all the possible users and categories in this group",
        }
    )
    with st.chat_message("assistant"):
        response = st.session_state.chatbot.stream(
            "Show me all the possible users and categories in this group"
        )

    st.session_state.messages.append({"role": "assistant", "content": response})


# Chat input
if prompt := st.chat_input("Write your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from chatbot
    with st.chat_message("assistant"):
        response = st.session_state.chatbot.stream(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
