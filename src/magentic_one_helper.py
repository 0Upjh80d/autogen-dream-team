import asyncio
import os
import tempfile
from typing import AsyncGenerator, Awaitable, Callable, TypedDict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_core import SingleThreadedAgentRuntime
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.azure import ACADynamicSessionsCodeExecutor
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential, get_bearer_token_provider
from dotenv import load_dotenv
from promptflow.tracing import start_trace

from magentic_one_custom_agent import MagenticOneCustomAgent
from magentic_one_custom_rag_agent import MagenticOneRAGAgent

load_dotenv()

# You can view the traces in http://127.0.0.1:23333/v1.0/ui/traces/
start_trace()


class MagenticOneHelper:
    def __init__(
        self,
        model: str,
        azure_deployment: str,
        api_version: str,
        azure_endpoint: str,
        search_endpoint: str,
        api_key: str | None = None,
        search_key: str | None = None,
        logs_dir: str = None,
        save_screenshots: bool = False,
        run_locally: bool = False,
    ) -> None:
        """
        A helper class to interact with the `MagenticOne` system.
        Initializes `MagenticOne` instance.


        Args:
            model (str): The OpenAI model (i.e. gpt-4o, gpt-40-mini).
            azure_deployment (str): The Azure OpenAI deployment name.
            api_version (str): The API version.
            azure_endpoint (str): The Azure OpenAI endpoint.
            search_endpoint (str): The Azure AI Search service endpoint.
            api_key (str, optional): The Azure OpenAI API key. Defaults to None.
            search_key (str, optional): The admin key for the Azure AI Search service. Defaults to None.
            logs_dir (str, optional): The directory to store logs and downloads. Defaults to None.
            save_screenshots (bool, optional): Whether to save the screenshots of web pages. Defaults to False.
            run_locally (bool, optional): Whether to run locally. Defaults to False.
        """
        self.model = model
        self.azure_deployment = azure_deployment
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint

        self.search_endpoint = search_endpoint
        self.search_key = search_key

        self.logs_dir = logs_dir
        self.runtime: SingleThreadedAgentRuntime | None = None
        # self.log_handler: LogHandler | None = None
        self.save_screenshots = save_screenshots
        self.run_locally = run_locally

        self.max_rounds = 50
        self.max_time = 25 * 60
        self.max_stalls_before_replan = 5
        self.return_final_answer = True
        self.start_page = "https://www.bing.com"

        self.azure_credential: AzureKeyCredential | AsyncTokenCredential = (
            AzureDeveloperCliCredential()
            if os.getenv("AZURE_TENANT_ID") is None
            else AzureDeveloperCliCredential(
                tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=60
            )
        )
        self.azure_open_ai_credential = (
            self.azure_credential if api_key is None else AzureKeyCredential(api_key)
        )

        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

    async def create_client(self) -> AzureOpenAIChatCompletionClient:
        """
        Creates the `AzureOpenAIChatCompletionClient` client using the provided credential.

        Raises:
            TypeError: Raises a TypeError if the credential type is invalid.

        Returns:
            AzureOpenAIChatCompletionClient: The client.
        """

        class AuthArgs(TypedDict, total=False):
            api_key: str
            azure_ad_token_provider: Callable[[], str | Awaitable[str]]

        auth_args = AuthArgs()
        if isinstance(self.azure_open_ai_credential, AzureKeyCredential):
            auth_args["api_key"] = self.azure_open_ai_credential.key
        elif isinstance(self.azure_open_ai_credential, AsyncTokenCredential):
            auth_args["azure_ad_token_provider"] = get_bearer_token_provider(
                self.azure_open_ai_credential,
                "https://cognitiveservices.azure.com/.default",
            )
        else:
            raise TypeError("Invalid credential type.")

        return AzureOpenAIChatCompletionClient(
            model=self.model,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint,
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": True,
            },
            **auth_args,
        )

    async def initialize(self, agents: list[dict]) -> None:
        """
        Initializes the `MagenticOne` system, setting up agents and runtime.

        Args:
            agents (list[dict]): A list of dictionaries containing configurations.
        """
        # Create the runtime
        self.runtime = SingleThreadedAgentRuntime()

        self.client = await self.create_client()

        # Set up agents
        self.agents = await self.setup_agents(agents, self.client, self.logs_dir)
        print("Agents setup complete!")

    async def setup_agents(
        self, agents: list[dict], client: AzureOpenAIChatCompletionClient, logs_dir: str
    ) -> list[AssistantAgent]:
        agent_list = []
        for agent in agents:
            # This is default `MagenticOne` agent - `Coder`
            if agent["type"] == "MagenticOne" and agent["name"] == "Coder":
                coder = MagenticOneCoderAgent("Coder", model_client=client)
                agent_list.append(coder)
                print("Coder added!")

            # This is default `MagenticOne` agent - `Executor`
            elif agent["type"] == "MagenticOne" and agent["name"] == "Executor":
                # If run locally; local docker execution
                if self.run_locally:
                    # Docker
                    code_executor = DockerCommandLineCodeExecutor(work_dir=logs_dir)
                    await code_executor.start()

                    executor = CodeExecutorAgent(
                        "Executor", code_executor=code_executor
                    )

                # If run remotely; Azure Container Apps (ACA) Dynamic Sessions execution
                else:
                    pool_endpoint = os.getenv("POOL_MANAGEMENT_ENDPOINT")
                    assert (
                        pool_endpoint
                    ), "`POOL_MANAGEMENT_ENDPOINT` environment variable is not set."
                    with tempfile.TemporaryDirectory() as temp_dir:
                        executor = CodeExecutorAgent(
                            "Executor",
                            code_executor=ACADynamicSessionsCodeExecutor(
                                pool_management_endpoint=pool_endpoint,
                                credential=self.azure_open_ai_credential,
                                work_dir=temp_dir,
                            ),
                        )

                agent_list.append(executor)
                print("Executor added!")

            # This is default MagenticOne agent - WebSurfer
            elif agent["type"] == "MagenticOne" and agent["name"] == "WebSurfer":
                web_surfer = MultimodalWebSurfer("WebSurfer", model_client=client)
                agent_list.append(web_surfer)
                print("WebSurfer added!")

            # This is default MagenticOne agent - FileSurfer
            elif agent["type"] == "MagenticOne" and agent["name"] == "FileSurfer":
                file_surfer = FileSurfer("FileSurfer", model_client=client)
                agent_list.append(file_surfer)
                print("FileSurfer added!")

            # This is custom agent - simple SYSTEM message and DESCRIPTION is used inherited from AssistantAgent
            elif agent["type"] == "Custom":
                custom_agent = MagenticOneCustomAgent(
                    agent["name"],
                    model_client=client,
                    system_message=agent["system_message"],
                    description=agent["description"],
                )

                agent_list.append(custom_agent)
                print(f'{agent["name"]} (custom) added!')

            # This is custom agent — RAG agent — you need to specify `index_name` and
            # Azure AI Search service endpoint and admin key in .env file
            elif agent["type"] == "RAG":
                # RAG agent
                rag_agent = MagenticOneRAGAgent(
                    agent["name"],
                    model_client=client,
                    index_name=agent["index_name"],
                    description=agent["description"],
                    search_key=self.search_key,
                    search_endpoint=self.search_endpoint,
                )
                agent_list.append(rag_agent)
                print(f'{agent["name"]} (RAG) added!')

            else:
                raise ValueError("Unknown Agent!")

        return agent_list

    def main(
        self, task: str
    ) -> AsyncGenerator[AgentEvent | ChatMessage | TaskResult, None]:
        team = MagenticOneGroupChat(
            participants=self.agents,
            model_client=self.client,
            max_turns=self.max_rounds,
            max_stalls=self.max_stalls_before_replan,
        )
        stream = team.run_stream(task=task)
        return stream


async def main(agents: list[dict], task: str, run_locally: bool) -> None:
    magentic_one = MagenticOneHelper(logs_dir=".", run_locally=run_locally)
    await magentic_one.initialize(agents)

    team = MagenticOneGroupChat(
        participants=magentic_one.agents,
        model_client=magentic_one.client,
        max_turns=magentic_one.max_rounds,
        max_stalls=magentic_one.max_stalls_before_replan,
    )

    await Console(team.run_stream(task=task))


if __name__ == "__main__":
    import argparse

    MAGENTIC_ONE_DEFAULT_AGENTS = [
        {
            "input_key": "0001",
            "type": "MagenticOne",
            "name": "Coder",
            "system_message": "",
            "description": "",
            "icon": "👨‍💻",
        },
        {
            "input_key": "0002",
            "type": "MagenticOne",
            "name": "Executor",
            "system_message": "",
            "description": "",
            "icon": "💻",
        },
        {
            "input_key": "0003",
            "type": "MagenticOne",
            "name": "FileSurfer",
            "system_message": "",
            "description": "",
            "icon": "📂",
        },
        {
            "input_key": "0004",
            "type": "MagenticOne",
            "name": "WebSurfer",
            "system_message": "",
            "description": "",
            "icon": "🏄‍♂️",
        },
    ]

    parser = argparse.ArgumentParser(
        description="Run `MagenticOneHelper` with specified task and run_locally option.",
        epilog="Example: python magnetic_one_helper.py --task 'Find me a French restaurant in Dubai with 2 Michelin stars?'",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--task",
        "-t",
        type=str,
        required=True,
        help="The task to run, e.g. 'How much taxes has Elon Musk paid?'",
    )
    parser.add_argument(
        "--run_locally",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Runs locally if set",
    )

    args = parser.parse_args()

    asyncio.run(main(MAGENTIC_ONE_DEFAULT_AGENTS, args.task, args.run_locally))
