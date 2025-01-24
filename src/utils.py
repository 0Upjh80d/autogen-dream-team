from datetime import datetime
import random
import streamlit as st

# Used for displaying messages from the agents
from autogen_agentchat.messages import (
    MultiModalMessage,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
)
from autogen_agentchat.base import TaskResult


def generate_random_agent_emoji() -> str:
    emoji_list = ["🤖", "🔄", "😊", "🚀", "🌟", "🔥", "💡", "🎉", "👍"]
    return random.choice(emoji_list)


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_agent_icon(agent_name: str) -> str:
    if agent_name == "MagenticOneOrchestrator":
        agent_icon = "🎻"
    elif agent_name == "WebSurfer":
        agent_icon = "🏄‍♂️"
    elif agent_name == "Coder":
        agent_icon = "👨‍💻"
    elif agent_name == "FileSurfer":
        agent_icon = "📂"
    elif agent_name == "Executor":
        agent_icon = "💻"
    elif agent_name == "user":
        agent_icon = "👤"
    else:
        agent_icon = "🤖"
    return agent_icon


def display_log_message(log_entry, logs_dir):
    # _log_entry_json  = json.loads(log_entry)
    _log_entry_json = log_entry

    # check if the message is a TaskResult class
    if isinstance(_log_entry_json, TaskResult):
        # st.write("TaskResult")
        # it is TaskResult class wth messages (list of all messages) and stop_reason
        # display last message
        _type = "TaskResult"
        _source = "TaskResult"
        _content = _log_entry_json.messages[-1]
        _stop_reason = _log_entry_json.stop_reason
        _timestamp = get_current_time()
        icon_result = "🎯"
        # do not display the final answer just yet, only set it in the session state
        st.session_state["final_answer"] = _content.content
        st.session_state["stop_reason"] = _stop_reason

    elif isinstance(_log_entry_json, MultiModalMessage):
        # message type, e.g.: TextMessage,'MultiModalMessage'
        _type = _log_entry_json.type
        # source of the message, e.g.: user, MagenticOneOrchestrator,'WebSurfer','Coder'
        _source = _log_entry_json.source
        # actual message content - if multimodal it will be list of contents, one of them is autogen_core._image.Image object where data_uri is base64 encoded image, image is PIL image
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        agent_icon = get_agent_icon(_source)
        with st.expander(f"{agent_icon} {_source} @ {_timestamp}", expanded=True):
            st.write("Message:")
            st.write(_content[0])
            st.image(_content[1].image)

    elif isinstance(_log_entry_json, TextMessage):
        # message type, e.g.: TextMessage,'MultiModalMessage'
        _type = _log_entry_json.type
        # source of the message, e.g.: user, MagenticOneOrchestrator,'WebSurfer','Coder'
        _source = _log_entry_json.source
        # actual message content - if multimodal it will be list of contents, one of them is autogen_core._image.Image object where data_uri is base64 encoded image, image is PIL image
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        agent_icon = get_agent_icon(_source)
        with st.expander(f"{agent_icon} {_source} @ {_timestamp}", expanded=True):
            st.write("Message:")
            st.write(_content)
    elif isinstance(_log_entry_json, ToolCallExecutionEvent):
        # message type, ToolCallRequestEvent, ToolCallExecutionEvent
        _type = _log_entry_json.type
        # source of the message, e.g.: user, MagenticOneOrchestrator,'WebSurfer','Coder'
        _source = _log_entry_json.source
        # actual message content - if multimodal it will be list of contents, one of them is autogen_core._image.Image object where data_uri is base64 encoded image, image is PIL image
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        agent_icon = get_agent_icon(_source)
        with st.expander(f"{agent_icon} {_source} @ {_timestamp}", expanded=True):
            st.write("Message:")
            st.write(_content)

    elif isinstance(_log_entry_json, ToolCallRequestEvent):
        # message type, ToolCallRequestEvent, ToolCallExecutionEvent
        _type = _log_entry_json.type
        # source of the message, e.g.: user, MagenticOneOrchestrator,'WebSurfer','Coder'
        _source = _log_entry_json.source
        # actual message content - if multimodal it will be list of contents, one of them is autogen_core._image.Image object where data_uri is base64 encoded image, image is PIL image
        _content = _log_entry_json.content
        _timestamp = get_current_time()
        _models_usage = _log_entry_json.models_usage

        agent_icon = get_agent_icon(_source)
        with st.expander(f"{agent_icon} {_source} @ {_timestamp}", expanded=True):
            st.write("Message:")
            st.write(_content)
    else:
        st.caption("🤔 Agents mumbling...")
