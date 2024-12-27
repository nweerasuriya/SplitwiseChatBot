"""
SplitwiseRetriever class

"""

__date__ = "2024-12-27"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"

import json

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langgraph.checkpoint.memory import MemorySaver

from src.utilities import get_splitwise_data

with open("config.json") as f:
    config = json.load(f)


class SplitwiseRetriever:
    def __init__(self):
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
        self.memory = MemorySaver()
        self.graph = None
        self.documents, self.vector_store = self.data_processing()
        self.llm = ChatAnthropic(
            model=config["model"]["name"],
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"],
        )

    @staticmethod
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

    def get_retriever(self):
        """
        Create and return a configured retriever
        """
        return SelfQueryRetriever.from_llm(
            llm=self.llm,
            vectorstore=self.vector_store,
            document_contents="Description and cost breakdown of individual expense",
            metadata_field_info=self.metadata_field_info,
            search_kwargs={"k": len(self.documents)},
        )