"""
Chatbot for Splitwise

Use langchain to create a chatbot that can answer questions about Splitwise data
using Anthropics API
"""

__date__ = "2024-10-29"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


# %% --------------------------------------------------------------------------
# Import Modules
import pandas as pd
from src.splitwise_api import SplitwiseAPI, clean_data
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain import hub

# Get Splitwise data
def get_splitwise_data():
    splitwise = SplitwiseAPI()
    group_expense = splitwise.get_expenses(group_id=50024800)
    df = pd.DataFrame(group_expense["expenses"])
    df1 = clean_data(df)
    return df1

# Data preparation for langchain
data, content_list = get_splitwise_data()
documents = [Document(page_content=item) for item in content_list]
# convert to embeddings
embeddings = HuggingFaceEmbeddings()
# vector store
vector_store = FAISS.from_documents(documents, embeddings)

# %%
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0, max_tokens=100)
combine_chain = create_stuff_documents_chain(
    llm, hub.pull("langchain-ai/retrieval-qa-chat")
)
rag_chain = create_retrieval_chain(
    vector_store.as_retriever(search_kwargs={"k": 50}), combine_chain
)
# %%
rag_chain.invoke({"input": "What has been Ned's spend on Groceries in October?"})["answer"]

