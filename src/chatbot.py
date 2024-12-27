"""
Chatbot for Splitwise

Use langchain to create a chatbot that can answer questions about Splitwise data
using Anthropics API
"""

__date__ = "2024-12-26"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import json

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.splitwise_retriever import SplitwiseRetriever

with open("config.json") as f:
    config = json.load(f)


# Step 1
def query_or_respond(state: MessagesState):
    """
    Generate tool call for retrieval or respond
    """
    llm_with_tools = splitwise_retriever.llm.bind_tools([retrieve_relevant_docs])
    response = llm_with_tools.invoke(state["messages"])
    # MessagesState appends messages to state instead of overwriting
    return {"messages": [response]}


@tool
def retrieve_relevant_docs(query: str):
    """
    Retrieve documents from the vector store
    """
    retriever = splitwise_retriever.get_retriever()
    retrieved_docs = retriever.invoke(query)
    # metadata_filters = get_metadata_filters_from_query(query)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# Step 2: Execute the retrieval.
tools = ToolNode([retrieve_relevant_docs])


# Step 3: Generate responses based on the retrieved documents.
def generate(state: MessagesState):
    """
    Generate Answer
    """
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_prompt = config["prompts"]["system"] + docs_content

    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_prompt)] + conversation_messages

    # Run
    response = splitwise_retriever.llm.invoke(prompt)
    return {"messages": [response]}


def generate_graph(memory):
    """
    Generate the graph for the chatbot
    """
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(query_or_respond)
    graph_builder.add_node(tools)
    graph_builder.add_node(generate)
    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)
    graph = graph_builder.compile(checkpointer=memory)
    return graph


def set_up_chatbot_workflow(group_id: int):
    # create global retriever
    global splitwise_retriever
    splitwise_retriever = SplitwiseRetriever(group_id)
    graph = generate_graph(splitwise_retriever.memory)
    splitwise_retriever.graph = graph


def chatbot(input_message: str):
    for step in splitwise_retriever.graph.stream(
        {"messages": [{"role": "user", "content": input_message}]},
        config,
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
