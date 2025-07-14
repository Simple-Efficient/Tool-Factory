import os
import json
import subprocess

def execute_shell_command(command: str, **kwargs) -> str:
    """
    Utility function to execute a shell command.

    Args:
        command (str): The shell command to execute, e.g., "ls -la" or "pip install -r requirements.txt"

    Returns:
        str: The output of the command execution, including stdout, stderr, and return code, in JSON format.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        # Return error information directly instead of raising an exception
        error_output = {
            "stdout": "",
            "stderr": f"Error occurred while executing command: {str(e)}",
            "returncode": -1
        }
        return json.dumps(error_output, ensure_ascii=False)

if __name__ == "__main__":
    print(execute_shell_command("ls -la"))
    