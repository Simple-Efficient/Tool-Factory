# -- coding: utf-8 --
import os
import json
import argparse

from typing import List, Callable, Union, Optional

from src.tool_factory import Agent
from src.tool_factory.repl.repl import run_demo_loop
from src.utils.file_utils import load_yaml, read_file_content, write_file_content
from src.tools.function.bing_search import bing_search
from src.tools.function.python_repl import python_repl_tool
from src.tools.function.github_search import github_search
from src.tools.function.execute_shell_command import execute_shell_command
from src.utils.mcp_utils import load_mcp_tools, get_mcp_tools_schema
from src.tools.function.validator.validate_tools import (
                                                       validate_mcp_availability_from_config,
                                                       check_mcp_format_from_config,
                                                       check_mcp_description_from_config)
from src.tools.function.validator.fix_mcp_tools import fix_mcp_tool

# Get absolute paths for current, prompts, logs, and MCP directories
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(CURRENT_DIR, "prompts")
LOG_DIR = os.path.join(CURRENT_DIR, "logs")
MCP_PATH = os.path.join(CURRENT_DIR, "mcp_box")

def transfer_to_planner():
    """
    Switch to planner agent.
    Returns:
        Agent: Instance of planner agent
    """
    return planner_agent

def transfer_to_searcher():
    """
    Switch to searcher agent.
    Returns:
        Agent: Instance of searcher agent
    """
    return searcher_agent

def transfer_to_developer():
    """
    Switch to developer agent.
    Returns:
        Agent: Instance of developer agent
    """
    return developer_agent

def transfer_to_validator():
    """
    Switch to validator agent.
    Returns:
        Agent: Instance of validator agent
    """
    return validator_agent

def show_developer_funcs() -> List[str]:
    """
    Show all tool function names owned by developer_agent.
    Returns:
        List[str]: List of function names
    """
    result_list = [func.__name__ for func in developer_agent.functions]
    return result_list

planner_agent = Agent(
    name="planner Agent",
    instructions=load_yaml(os.path.join(PROMPTS_DIR, "planner.yaml"))["planner_prompt"],
    functions=[
        bing_search,
        transfer_to_searcher,
        transfer_to_developer,
        show_developer_funcs
    ],
    tool_choice='auto'
)

searcher_agent = Agent(
    name="searcher Agent",
    instructions=load_yaml(os.path.join(PROMPTS_DIR, "searcher.yaml"))["searcher_prompt"],
    functions=[
        github_search,
        transfer_to_developer
    ],
    tool_choice='auto'
)

developer_agent = Agent(
    name="developer Agent",
    instructions=load_yaml(os.path.join(PROMPTS_DIR, "developer.yaml"))["developer_prompt"] + f"\nUse tool 'write_file_content' to save file at the path:{MCP_PATH}",
    functions=[
        execute_shell_command,
        python_repl_tool,
        transfer_to_planner,
        show_developer_funcs,
        fix_mcp_tool,
        transfer_to_validator,
        read_file_content,
        write_file_content
    ],
    tool_choice='auto'
)

validator_agent = Agent(
    name = "validator Agent",
    instructions = load_yaml(os.path.join(PROMPTS_DIR, "validator.yaml"))["validator_prompt"],
    functions = [
                 transfer_to_developer,
                 get_mcp_tools_schema,
                 validate_mcp_availability_from_config,
                 check_mcp_format_from_config,
                 check_mcp_description_from_config,
                 ],
    tool_choice='auto')

# Add MCP tools to developer_agent
developer_agent.functions.extend(load_mcp_tools(MCP_PATH))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Recognition Agent Runner")
    parser.add_argument('--config_path', type=str, default="", help="Path to MCP tool config file")
    parser.add_argument('--user_input', type=str, default=None, help="User input command")
    parser.add_argument('--log_dir', type=str, default=LOG_DIR, help="Log directory")
    parser.add_argument('--audio_file_path', type=str, default="", help="Audio file path")
    args = parser.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)

    # Validate MCP tool using validator agent
    # config_path = args.config_path
    # user_input = args.user_input or f"Please validate the MCP tool located at {config_path}, and end the task after providing the validation results"
    # run_demo_loop(validator_agent, debug=True, user_input=user_input, log_dir=args.log_dir)

    # Build audio recognition tool using planner agent
    # audio_file_path = args.audio_file_path
    audio_file_path = "query_understand/voice_001.wav"
    user_input = f"Please build an audio recognition tool using the tiny model from https://github.com/openai/whisper.git, and recognize {audio_file_path}"
    run_demo_loop(planner_agent, debug=True, user_input=user_input, log_dir=LOG_DIR)