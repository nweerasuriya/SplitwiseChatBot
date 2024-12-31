"""
Create Flask app to authenticate with Splitwise API
"""

__date__ = "2024-10-28"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import streamlit as st

from src.chatbot import chatbot, set_up_chatbot_workflow

st.title("Splitwise Chatbot")
st.logo(image="src/logo.png")
st.markdown(
    """
    <style>
    img[data-testid="stLogo"] {
            height: 3.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.messages = []
    st.session_state.initialized = False

# Splitwise ID input
group_id = st.number_input("Enter your Splitwise Group ID:", min_value=1)

if st.button("Initialize Chat") and not st.session_state.initialized:
    set_up_chatbot_workflow(group_id=group_id)
    st.session_state.initialized = True

if st.session_state.initialized:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your Splitwise expenses"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = chatbot(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
