"""
Chatbot for Splitwise

Use langchain to create a chatbot that can answer questions about Splitwise data
using Anthropics API
"""

__date__ = "2024-12-26"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import json

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

# %% --------------------------------------------------------------------------
# Import Modules
from src.utilities import get_splitwise_data

with open("config.json") as f:
    config = json.load(f)


class SplitwiseRetriever:
    def __init__(self, documents, vector_store, llm):
        self.documents = documents
        self.vector_store = vector_store
        self.llm = llm
        self.metadata_field_info = [
            AttributeInfo(name="day", description="Day of the expense", type="int"),
            AttributeInfo(
                name="month", description="Month of the expense", type="string"
            ),
            AttributeInfo(name="year", description="Year of the expense", type="int"),
            AttributeInfo(
                name="category", description="Category of the expense", type="string"
            ),
        ]

    def get_retriever(self):
        """Create and return a configured retriever"""
        return SelfQueryRetriever.from_llm(
            llm=self.llm,
            vectorstore=self.vector_store,
            document_contents="Description and cost breakdown of individual expense",
            metadata_field_info=self.metadata_field_info,
            search_kwargs={"k": len(self.documents)},
        )


def chatbot(input_message: str, graph: StateGraph):
    for step in graph.stream(
        {"messages": [{"role": "user", "content": input_message}]},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()


def data_processing():
    """
    Data preparation for langchain
    Get Splitwise data and convert to documents, embeddings and vector store
    """
    # Data preparation for langchain
    data, content_list, metadata = get_splitwise_data()
    # grouped_list = groupby_date(content_list)
    documents = [
        Document(page_content=item, metadata=metadata[i])
        for i, item in enumerate(content_list)
    ]
    # convert to embeddings
    embeddings = HuggingFaceEmbeddings()
    # vector store
    vector_store = Chroma.from_documents(documents, embeddings)
    return documents, vector_store


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


# Step 1
def query_or_respond(state: MessagesState):
    """
    Generate tool call for retrieval or respond
    """
    llm_with_tools = llm.bind_tools([retrieve_relevant_docs])
    response = llm_with_tools.invoke(state["messages"])
    # MessagesState appends messages to state instead of overwriting
    return {"messages": [response]}


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
    response = llm.invoke(prompt)
    return {"messages": [response]}


# %%
documents, vector_store = data_processing()
llm = ChatAnthropic(
    model=config["model"]["name"],
    temperature=config["model"]["temperature"],
    max_tokens=config["model"]["max_tokens"],
)
splitwise_retriever = SplitwiseRetriever(documents, vector_store, llm)

# %%
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

graph = graph_builder.compile()

input_message = "What was Ned's Dining out owed share in October?"
chatbot(input_message, graph)
# %%
