import asyncio
import os
import random
import string
import sys

import streamlit as st

from dotenv import load_dotenv

from magentic_one_custom_rag_agent import MAGENTIC_ONE_RAG_DESCRIPTION
from magentic_one_helper import MagenticOneHelper
from utils import display_log_message, generate_random_agent_emoji

load_dotenv()

# Enable asyncio for Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize a global cancellation event
cancel_event = asyncio.Event()

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

# Initialize session state for instructions
if "instructions" not in st.session_state:
    st.session_state["instructions"] = ""
if "running" not in st.session_state:
    st.session_state["running"] = False
if "final_answer" not in st.session_state:
    st.session_state["final_answer"] = None
if "stop_reason" not in st.session_state:
    st.session_state["stop_reason"] = None
if "run_mode_locally" not in st.session_state:
    st.session_state["run_mode_locally"] = True

if "saved_agents" not in st.session_state:
    st.session_state["saved_agents"] = MAGENTIC_ONE_DEFAULT_AGENTS

if "max_rounds" not in st.session_state:
    st.session_state["max_rounds"] = 30
if "max_time" not in st.session_state:
    st.session_state["max_time"] = 25
if "max_stalls_before_replan" not in st.session_state:
    st.session_state["max_stalls_before_replan"] = 5
if "return_final_answer" not in st.session_state:
    st.session_state["return_final_answer"] = True
if "start_page" not in st.session_state:
    st.session_state["start_page"] = "https://www.bing.com"
if "save_screenshots" not in st.session_state:
    st.session_state["save_screenshots"] = True

st.set_page_config(layout="wide")
st.write("### Dream Team powered by Magentic 1")


@st.dialog("Add agent")
def add_agent(item=None):
    # st.write(f"Setuup your agent:")
    st.caption(
        "Note: Always use unique name with no spaces. Always fill System message and Description."
    )
    st.caption(
        'In the system message use as last sentence: Reply "TERMINATE" in the end when everything is done.'
    )
    # agent_type = st.selectbox(
    #     "Type",
    #     ["MagenticOne", "Custom"],
    #     key=f"type{input_key}",
    #     index=0 if agent and agent["type"] == "MagenticOne" else 1,
    #     disabled=is_disabled(agent["type"]) if agent else False,
    # )
    agent_type = "Custom"
    agent_name = st.text_input("Name", value=None)
    system_message = st.text_area("System Message", value=None)
    description = st.text_area("Description", value=None)

    if st.button("Submit"):
        # st.session_state.vote = {"item": item, "reason": reason}
        st.session_state["saved_agents"].append(
            {
                "input_key": random.choice(string.ascii_uppercase)
                + str(random.randint(0, 999999)),
                "type": agent_type,
                "name": agent_name,
                "system_message": system_message,
                "description": description,
                "icon": generate_random_agent_emoji(),
            }
        )
        st.rerun()


@st.dialog("Add RAG agent")
def add_rag_agent(item=None):
    # st.write(f"Setuup your agent:")
    st.caption(
        """
        **Note**: Always use unique name with no spaces.

        Index name must be your existing index in Azure AI Search service which is indexed with data. We expect a structure of index:

        - `parent_id`
        - `chunk_id`
        - `chunk`
        - `text_vector`

        This structure is default when you ingest and vectorize the document directly with Azure AI Search.
        """
    )

    # agent_type = st.selectbox(
    #     "Type",
    #     ["MagenticOne", "Custom"],
    #     key=f"type{input_key}",
    #     index=0 if agent and agent["type"] == "MagenticOne" else 1,
    #     disabled=is_disabled(agent["type"]) if agent else False,
    # )
    agent_type = "RAG"
    agent_name = st.text_input("Name", value=None)
    # system_message = st.text_area("System Message", value=None)
    description = st.text_area("Description", value=MAGENTIC_ONE_RAG_DESCRIPTION)

    index_name = st.text_input("Index Name", value=None)

    if st.button("Submit"):
        # st.session_state.vote = {"item": item, "reason": reason}
        st.session_state["saved_agents"].append(
            {
                "input_key": random.choice(string.ascii_uppercase)
                + str(random.randint(0, 999999)),
                "type": agent_type,
                "name": agent_name,
                # "system_message": system_message,
                "description": description,
                "icon": "🔍",
                "index_name": index_name,
            }
        )
        st.rerun()


@st.dialog("Edit agent")
def edit_agent(input_key=None):
    agent = next(
        (i for i in st.session_state["saved_agents"] if i["input_key"] == input_key),
        None,
    )
    # st.write(f"Setup your agent:")
    st.caption(
        "Note: Always use unique name with no spaces. Always fill System message and Description."
    )
    # agent_type = st.selectbox("Type", ["MagenticOne","Custom"], key=f"type{input_key}", index=0 if agent and agent["type"] == "MagenticOne" else 1, disabled=is_disabled(agent["type"]) if agent else False)
    # agent_type = "Custom"
    # agent_name = st.text_input("Name", value=None)
    # system_message = st.text_area("System Message", value=None)
    # description = st.text_area("Description", value=None)
    if agent["type"] == "MagenticOne":
        disabled = True
        st.info("MagenticOne agents cannot be edited. Only deleted.")
    else:
        disabled = False
    agent_type = "Custom"
    agent_name = st.text_input(
        "Name",
        key=f"name{input_key}",
        value=agent["name"] if agent else None,
        disabled=disabled,
    )
    system_message = st.text_area(
        "System Message",
        key=f"sys{input_key}",
        value=agent["system_message"] if agent else None,
        disabled=disabled,
    )
    description = st.text_area(
        "Description",
        key=f"desc{input_key}",
        value=agent["description"] if agent else None,
        disabled=disabled,
    )

    if st.button("Submit", disabled=disabled):
        agent["name"] = agent_name
        agent["system_message"] = system_message
        agent["description"] = description
        st.rerun()

    if st.button("Delete", key=f'delete{agent["input_key"]}', type="primary"):
        st.session_state["saved_agents"] = [
            i for i in st.session_state["saved_agents"] if i["input_key"] != input_key
        ]
        st.rerun()


image_path = "contoso.png"

# Display the image in the sidebar
with st.sidebar:
    st.image(image_path, use_container_width=True)

    with st.container(border=True):
        st.caption("Settings:")
        st.session_state["max_rounds"] = st.number_input(
            "Max Rounds", min_value=1, value=50
        )
        st.session_state["max_time"] = st.number_input(
            "Max Time (Minutes)", min_value=1, value=10
        )
        st.session_state["max_stalls_before_replan"] = st.number_input(
            "Max Stalls Before Replan", min_value=1, max_value=10, value=5
        )
        st.session_state["return_final_answer"] = st.checkbox(
            "Return Final Answer", value=True
        )

        st.session_state["start_page"] = st.text_input(
            "Start Page URL", value="https://www.bing.com"
        )

run_button_text = "Run Agents"
if not st.session_state["running"]:
    with st.expander("Agents configuration", expanded=True):
        st.caption("You can configure your agents here.")
        agents = st.session_state["saved_agents"]
        # st.write(agents)
        # create st.columns for each agent
        cols = st.columns(len(agents))
        for col, agent in zip(cols, agents):
            with col:
                with st.container(border=True):
                    st.write(agent["icon"])
                    st.write(agent["name"])
                    st.caption(agent["type"])
                    # st.caption(agent["description"])
                    # if st.button("❌", key=f'delete{agent["input_key"]}'):
                    #     delete_agent(agent["input_key"])
                    if st.button("✏️", key=f'edit{agent["input_key"]}'):
                        edit_agent(agent["input_key"])

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            if st.button("Restore MagenticOne agents", icon="🔄"):
                st.session_state["saved_agents"] = MAGENTIC_ONE_DEFAULT_AGENTS
                st.rerun()
        with col3:
            if st.button("Add Agent", type="primary", icon="➕"):
                add_agent("A")
            if st.button("Add RAG Agent", type="primary", icon="➕"):
                add_rag_agent("A")

    # Define predefined values
    predefined_values = [
        "How do I setup my Surface Pro?",
        "Find me a French restaurant in Dubai with 2 Michelin stars.",
        "When and where is the next game of Arsenal? Print a link for purchase.",
        "Based on your knowledge base how much taxes has Elon Musk paid in 2024?",
        "Generate a Python script and execute Fibonacci sequence below 1000",
    ]

    # Add an option for custom input
    custom_option = "Write your own query"

    # Use selectbox for predefined values and custom option
    selected_option = st.selectbox(
        "Select your instructions:", options=predefined_values + [custom_option]
    )

    # If custom option is selected, show text input for custom instructions
    if selected_option == custom_option:
        instructions = st.text_area("Enter your custom instructions:", height=200)
    else:
        instructions = selected_option

    # Update session state with instructions
    st.session_state["instructions"] = instructions

    run_mode_locally = st.toggle("Run Locally", value=False)

    if run_mode_locally:
        st.session_state["run_mode_locally"] = True
        st.caption(
            "**Run Locally**: Run the workflow in a Docker container on your local machine."
        )
    else:
        st.caption(
            "**Run in Azure**: Run the workflow in a Azure Container Apps (ACA) Dynamic Sessions on Azure."
        )
        # Check if the Azure infrastructure is setup
        _pool_endpoint = os.getenv("POOL_MANAGEMENT_ENDPOINT")
        if not _pool_endpoint:
            st.error(
                "You need to setup the Azure infrastructure first. Try `azd up` in your project."
            )
            # st.session_state["run_mode_locally"] = True
            # st.rerun()
        st.session_state["run_mode_locally"] = False
else:
    run_button_text = "Cancel Run"

if st.button(run_button_text, type="primary"):
    if not st.session_state["running"]:
        st.session_state["instructions"] = instructions
        st.session_state["running"] = True
        st.session_state["final_answer"] = None
        cancel_event.clear()  # Clear the cancellation event
        st.rerun()
    else:
        st.session_state["running"] = False
        st.session_state["instructions"] = ""
        st.session_state["final_answer"] = None
        st.session_state["run_mode_locally"] = True
        cancel_event.set()  # Set the cancellation event
        st.rerun()


async def main(task, logs_dir="./logs"):

    # Create folder for logs if not exists
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Initialize the MagenticOne system
    magentic_one = MagenticOneHelper(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        search_endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY"),
        logs_dir=logs_dir,
        save_screenshots=st.session_state["save_screenshots"],
        run_locally=st.session_state["run_mode_locally"],
    )
    await magentic_one.initialize(agents=st.session_state["saved_agents"])

    # Start the MagenticOne system
    stream = magentic_one.main(task=task)

    # Stream and process logs
    with st.container(border=True):
        async for log_entry in stream:
            display_log_message(log_entry=log_entry, logs_dir=logs_dir)


if st.session_state["running"]:
    assert st.session_state["instructions"] != "", "Instructions can't be empty."

    with st.spinner("Dream Team is running..."):
        asyncio.run(main(st.session_state["instructions"]))

    final_answer = st.session_state["final_answer"]
    if final_answer:
        st.success("Task completed successfully.")
        st.write("## Final answer:")
        st.write(final_answer)
        st.write("## Stop reason:")
        st.write(st.session_state["stop_reason"])
        cancel_event.set()  # Set the cancellation event
    else:
        st.error("Task failed.")
        st.write("Final answer not found.")
