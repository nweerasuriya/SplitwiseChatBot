"""
SplitwiseRetriever class

"""

__date__ = "2024-12-27"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"

import json

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.docstore.document import Document
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langgraph.checkpoint.memory import MemorySaver

from utilities import process_data

with open("config.json") as f:
    config = json.load(f)


class SplitwiseRetriever:
    def __init__(self, group_id):
        self.metadata_field_info = [
            AttributeInfo(
                name="type",
                description="Type of document: either 'individual' or 'summary'",
                type="string",
            ),
            AttributeInfo(name="day", description="Day of the expense", type="int"),
            AttributeInfo(
                name="month",
                description="Month of the expense",
                type="string",
            ),
            AttributeInfo(name="year", description="Year of the expense", type="int"),
            AttributeInfo(
                name="category",
                description="Category of the expense",
                type="string",
            ),
        ]

        self.memory = MemorySaver()
        self.graph = None
        self.documents, self.vector_store = self.data_processing(group_id)
        self.llm = ChatAnthropic(
            model=config["model"]["name"],
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"],
        )

    @staticmethod
    def data_processing(group_id):
        """
        Data preparation for langchain
        Get Splitwise data and convert to documents, embeddings and vector store
        """
        # Data preparation for langchain
        content_list, metadata = process_data(group_id)
        # grouped_list = groupby_date(content_list)
        documents = [
            Document(page_content=item.lower(), metadata=metadata[i])
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
            document_contents="Type of document (summary or individual). Description and cost breakdown of individual expense",
            metadata_field_info=self.metadata_field_info,
            search_kwargs={"k": len(self.documents)},
        )
