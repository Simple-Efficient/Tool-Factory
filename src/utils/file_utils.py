import os
import yaml


def load_yaml(file_path: str) -> dict:
    """Load YAML file and return as dict."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def read_file_content(file_path: str) -> str:
    """Read the content of a file and return as string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def write_file_content(file_path=None, content=None, **kwargs):
    """
    Write content to a file and return status message.
    
    This function can be called in two ways:
    1. With separate parameters: write_file_content(file_path="./path/to/file.py", content="file content")
    2. With a single dictionary: write_file_content({"file_path": "./path/to/file.py", "content": "file content"})
    
    Args:
        file_path (str): Path to the file where content will be written
        content (str): The content to write to the file
        **kwargs: Alternative way to provide arguments as a dictionary
    
    Returns:
        str: Status message indicating success or failure
    
    Example:
        write_file_content(file_path="./example.txt", content="Hello World")
        write_file_content({"file_path": "./example.txt", "content": "Hello World"})
    """
    # Handle the case where arguments are passed as a single dictionary
    if file_path is not None and content is None and not kwargs and isinstance(file_path, dict):
        params = file_path
        file_path = params.get("file_path")
        content = params.get("content")
    
    # Parameter validation
    if not file_path:
        return "Error: file_path parameter is required"
    
    if content is None:  # Allow empty string content, but not missing content
        return "Error: content parameter is required"
    
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"File successfully written: {file_path}"
    
    except FileNotFoundError:
        return f"Error: Cannot access path - {file_path}. Please check if the path is correct or for permission issues."
    except PermissionError:
        return f"Error: No write permission for - {file_path}. Please check file permissions."
    except IsADirectoryError:
        return f"Error: Target is a directory, not a file - {file_path}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"
