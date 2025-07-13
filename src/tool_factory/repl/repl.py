import json
import logging
import datetime
import os
import sys
import re
from src.tool_factory import ToolFactory

# Global variables for log file path and original stdout/stderr
_current_log_file = None
_original_stdout = sys.stdout
_original_stderr = sys.stderr

END_SYMBOL = '### END ###'


def setup_logging(log_dir=None):
    """Setup logging to file and console.
    Args:
        log_dir: Directory for log files. If None, use default path.
    Returns:
        Path to the log file.
    """
    global _current_log_file

    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "examples", "application", "tools_creation", ".log")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_run_{timestamp}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(_original_stdout)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    logging.info(f"Log file created: {log_file}")
    _current_log_file = log_file

    class LoggerWriter:
        def __init__(self, logger_func):
            self.logger_func = logger_func
            self.buffer = ''
        def write(self, message):
            if message and message.strip():
                self.logger_func(message)
        def flush(self):
            pass

    sys.stdout = LoggerWriter(lambda msg: logging.info(msg.rstrip()))
    sys.stderr = LoggerWriter(lambda msg: logging.error(msg.rstrip()))
    return log_file

def log_print(*args, **kwargs):
    """Enhanced print function: outputs to both console and log file.
    Args:
        *args: Arguments to print
        **kwargs: Supports 'end', 'flush', etc.
    """
    global _current_log_file
    if _current_log_file is None:
        _current_log_file = setup_logging()
    end = kwargs.get('end', '\n')
    flush = kwargs.get('flush', False)
    message = ' '.join(str(arg) for arg in args)
    console_message = message
    file_message = re.sub(r'\033\[\d+m', '', message)
    print(console_message, end=end, flush=flush, file=_original_stdout)
    try:
        with open(_current_log_file, 'a', encoding='utf-8') as f:
            f.write(file_message)
            if end:
                f.write(end)
    except Exception as e:
        print(f"Log write failed: {e}", file=_original_stderr)

def log_cmd_output(cmd, output):
    """Log command execution result to log file.
    Args:
        cmd: Command executed
        output: Command output
    """
    log_print(f"\nCommand executed: {cmd}")
    log_print("-" * 40)
    log_print(output)
    log_print("-" * 40)

def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""
    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]
        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                log_print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            log_print(chunk["content"], end="", flush=True)
            content += chunk["content"]
        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                log_print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")
        if "delim" in chunk and chunk["delim"] == "end" and content:
            log_print()  # End of response message
            content = ""
        if "response" in chunk:
            return chunk["response"]

def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue
        log_print(f"\033[94m{message['sender']}\033[0m:", end=" ")
        if message["content"]:
            log_print(message["content"])
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            log_print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            log_print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")

def run_demo_loop(
    starting_agent, context_variables=None, stream=False, debug=False, user_input=None, log_dir=None
) -> None:
    """Run the demo loop for Swarm CLI.
    Args:
        starting_agent: The initial agent
        context_variables: Context variables
        stream: Use streaming response or not
        debug: Enable debug mode
        user_input: User input
        log_dir: Directory for log files, if None use default
    """
    setup_logging(log_dir)
    client = Swarm()
    log_print("Starting Swarm CLI 🐝")
    messages = []
    agent = starting_agent

    messages.append({"role": "user", "content": user_input})
    log_print(f"\033[90mUser\033[0m: {user_input}")

    try:
        while True:
            try:
                response = client.run(
                    agent=agent,
                    messages=messages,
                    context_variables=context_variables or {},
                    stream=stream,
                    debug=debug,
                )
                if stream:
                    response_content = process_and_print_streaming_response(response)
                    if response_content and END_SYMBOL in response_content:
                        break
                else:
                    pretty_print_messages(response.messages)
                    for msg in response.messages:
                        if msg["role"] == "assistant" and msg.get("content") and END_SYMBOL in msg["content"]:
                            break
                    else:
                        messages.extend(response.messages)
                        agent = response.agent
                        continue
                    break
                messages.extend(response.messages)
                agent = response.agent
            except Exception as e:
                log_print(f"\033[91mError: {str(e)}\033[0m")
                import traceback
                log_print(traceback.format_exc())
                break
    except KeyboardInterrupt:
        log_print("\n\033[93mExecution interrupted by user\033[0m")
    finally:
        log_print("\nSession ended")
        log_print(f"Log saved to: {_current_log_file}")
        sys.stdout = _original_stdout
        sys.stderr = _original_stderr
