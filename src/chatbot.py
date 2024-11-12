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
from langchain_chroma import Chroma
from langchain.retrievers.document_compressors.chain_filter import LLMChainFilter
from langchain.docstore.document import Document
from langchain.chains.retrieval import create_retrieval_chain
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.tools import tool


metadata_field_info = [
    AttributeInfo(name="day", description="Day of the expense", type="int",),
    AttributeInfo(name="month", description="Month of the expense", type="string",),
    AttributeInfo(name="year", description="Year of the expense", type="int",),
    AttributeInfo(
        name="category", description="Category of the expense", type="string",
    ),
]

# Get Splitwise data
def get_splitwise_data():
    splitwise = SplitwiseAPI()
    group_expense = splitwise.get_expenses(group_id=50024800)
    df = pd.DataFrame(group_expense["expenses"])
    df1 = clean_data(df)
    return df1


def groupby_date(content_list):
    content_dict = {}
    # group content list by date
    for item in content_list:
        date = item.split("Date: ")[1].split("T")[0]
        if date in content_dict:
            content_dict[date] = content_dict[date] + " || \n " + item
        else:
            content_dict[date] = item

    return list(content_dict.values())


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


def implement_rag_chain(llm, system_prompt, metadata_field_info):
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{input}"),]
    )

    combine_chain = create_stuff_documents_chain(llm, prompt)
    # retrieval
    base_retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=vector_store,
        document_contents="Description and cost breakdown of individual expense",
        metadata_field_info=metadata_field_info,
        search_kwargs={"k": int(len(documents))},
    )

    compressor = LLMChainFilter.from_llm(llm)
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=base_retriever,
    )
    rag_chain = create_retrieval_chain(retriever, combine_chain)
    return rag_chain

documents, vector_store = data_processing()

#%%
llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0, max_tokens=500)

system_prompt = (
    "You are a chatbot that can answer questions about spending and expenses on Splitwise using the following contextual data. "
    "If you are calculating a user's spend, use the only amount of 'owed_share' for an item rather than what the paid share unless specified. "
    "If you are doing calculations of expenses, just show the final calculation and don't show the working unless specified in the question. "
    "Keep the answer concise, getting straight to the answer. No need to say things like 'based on provided data'. "
    "If no relevant docs are found, say that you don't know."
    "\n\n"
    "{context}"
)
rag_chain = implement_rag_chain(llm, system_prompt, metadata_field_info)

output = rag_chain.invoke(
    {
        "input": "What was Ned W's owed spend on Groceries in October? Only show your working"
    }
)
docs = output["context"]
output
# %%
# Find actual answer
owed_list = []
for doc in docs:
    content = doc.page_content
    # find Ned W's owed share
    if "Ned W" in content:
        owed_list.append(
            float(content.split("Ned W':")[1].split("owed_share': '")[1].split("'")[0])
        )
sum(owed_list)
# %%
