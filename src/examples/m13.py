"""Autonomously completes a coding task."""

import asyncio
import os
from typing import Awaitable, Callable, TypedDict

from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_core import SingleThreadedAgentRuntime

# from autogen_core import AgentId, AgentProxy
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()


azure_credential = (
    AzureDeveloperCliCredential()
    if os.getenv("AZURE_TENANT_ID") is None
    else AzureDeveloperCliCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=60
    )
)
azure_open_ai_credential: AzureKeyCredential | AsyncTokenCredential = (
    azure_credential
    if os.getenv("AZURE_OPENAI_API_KEY") is None
    else AzureKeyCredential(os.getenv("AZURE_OPENAI_API_KEY"))
)

runtime = SingleThreadedAgentRuntime()


async def create_client() -> AzureOpenAIChatCompletionClient:
    class AuthArgs(TypedDict, total=False):
        api_key: str
        azure_ad_token_provider: Callable[[], str | Awaitable[str]]

    auth_args = AuthArgs()
    if isinstance(azure_open_ai_credential, AzureKeyCredential):
        auth_args["api_key"] = azure_open_ai_credential.key
    elif isinstance(azure_open_ai_credential, AsyncTokenCredential):
        auth_args["azure_ad_token_provider"] = get_bearer_token_provider(
            azure_open_ai_credential, "https://cognitiveservices.azure.com/.default"
        )
    else:
        raise TypeError("Invalid credential type.")

    return AzureOpenAIChatCompletionClient(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        model_info={
            "vision": True,
            "function_calling": True,
            "json_output": True,
        },
        **auth_args
    )


async def main() -> None:

    client = await create_client()

    fs = FileSurfer("FileSurfer", model_client=client)
    ws = MultimodalWebSurfer("WebSurfer", model_client=client)
    coder = MagenticOneCoderAgent("Coder", model_client=client)
    # coder = AgentProxy(AgentId("Coder", "default"), runtime)
    executor = CodeExecutorAgent(
        "Executor", code_executor=LocalCommandLineCodeExecutor()
    )
    team = MagenticOneGroupChat([fs, ws, executor, coder], model_client=client)
    await Console(team.run_stream(task="How much taxes has Elon Musk paid?"))


if __name__ == "__main__":
    asyncio.run(main())
