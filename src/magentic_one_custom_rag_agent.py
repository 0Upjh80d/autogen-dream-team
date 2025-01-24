import os

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from dotenv import load_dotenv

load_dotenv()

MAGENTIC_ONE_RAG_DESCRIPTION = (
    "An agent that has access to internal search index and can handle RAG tasks, "
    "call this agent if you are getting questions on your internal search index."
)

MAGENTIC_ONE_RAG_SYSTEM_MESSAGE = """
You are a helpful AI Assistant.
When given a user query, use available tools to help the user with their request.
Reply "TERMINATE" in the end when everything is done.
"""


class MagenticOneRAGAgent(AssistantAgent):
    """
    An agent, used by `MagenticOne` that provides coding assistance using an LLM model client.

    The prompts and description are sealed, to replicate the original `MagenticOne` configuration.
    See `AssistantAgent` if you wish to modify these values.
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        index_name: str,
        search_endpoint: str,
        search_key: str | None = None,
        description: str = MAGENTIC_ONE_RAG_DESCRIPTION,
    ):
        super().__init__(
            name,
            model_client,
            description=description,
            system_message=MAGENTIC_ONE_RAG_SYSTEM_MESSAGE,
            tools=[self.do_search],
            reflect_on_tool_use=True,
        )

        self.index_name = index_name
        self.search_endpoint = search_endpoint
        self.search_key = search_key

    def config_search(self) -> SearchClient:
        azure_credential = (
            AzureDeveloperCliCredential()
            if os.getenv("AZURE_TENANT_ID") is None
            else AzureDeveloperCliCredential(
                tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=60
            )
        )
        search_credential: AzureKeyCredential | AsyncTokenCredential = (
            azure_credential
            if self.search_key is None
            else AzureKeyCredential(self.search_key)
        )
        return SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=search_credential,
        )

    async def do_search(self, query: str) -> str:
        """Search indexed data using Azure AI Search with vector-based queries."""
        async with self.config_search() as search_client:
            fields = "text_vector"  # TODO: Check if this is the correct field name
            vector_query = VectorizableTextQuery(
                text=query, k_nearest_neighbors=1, fields=fields, exhaustive=True
            )

            results = await search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=[
                    "parent_id",
                    "chunk_id",
                    "chunk",
                ],  # TODO: Check if these are the correct field names
                top=1,  # TODO: Check if this is the correct number of results
            )
            answer = ""
            async for result in results:
                # print(f"parent_id: {result['parent_id']}")
                # print(f"chunk_id: {result['chunk_id']}")
                # print(f"Score: {result['@search.score']}")
                # print(f"Content: {result['chunk']}")
                answer = answer + result["chunk"]
            return answer
