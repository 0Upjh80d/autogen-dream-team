from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient


# TODO: Add checks to user inputs to ensure it is a valid definition for a custom agent
class MagenticOneCustomAgent(AssistantAgent):
    """
    An agent, used by `MagenticOne` that provides coding assistance using an LLM model client.

    The prompts and description are sealed, to replicate the original `MagenticOne` configuration.
    See `AssistantAgent` if you wish to modify these values.
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        system_message: str,
        description: str,
    ):
        super().__init__(
            name,
            model_client,
            description=description,
            system_message=system_message,
        )
