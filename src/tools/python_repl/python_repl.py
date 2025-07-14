import logging
from typing import Annotated, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# Initialize Python REPL
repl = PythonREPL()


def python_repl_tool(code: Optional[str] = None, **kwargs):
    """
    Execute Python code for data analysis or computation. If you want to see the output of a value, use `print(...)` to print it.

    Args:
        code: Python code to execute for further analysis or computation.
    
    Returns:
        Returns the execution result or error message as a string.
    
    Examples:
        # Correct usage:
        python_repl_tool("print('Hello, world!')")
        
        # Or use named arguments:
        python_repl_tool(code="print('Hello, world!')")
        
        # Incorrect usage (to avoid):
        python_repl_tool()  # Missing code argument
        python_repl_tool(kwargs={"code": "print('Hello')"})  # Argument nested in kwargs
    """
    # Handle various parameter passing methods
    if code is None:
        # Handle empty call
        if not kwargs:
            return "Error: Missing required 'code' argument. Please provide a Python code string. For example: python_repl_tool(\"print('Hello, world!')\")"
        
        # Handle nested kwargs
        if 'kwargs' in kwargs:
            if isinstance(kwargs['kwargs'], dict) and 'code' in kwargs['kwargs']:
                code = kwargs['kwargs']['code']
            elif isinstance(kwargs['kwargs'], str):
                code = kwargs['kwargs']
        # Handle normal named argument
        elif 'code' in kwargs:
            code = kwargs['code']
    
    # Final check for code to execute
    if code is None:
        return "Error: Unrecognized parameter format. Please provide a Python code string. For example: python_repl_tool(\"print('Hello, world!')\")"
    
    if not isinstance(code, str):
        error_msg = f"Invalid input: code must be a string, got {type(code)}"
        return f"Error executing code:\n```python\n{str(code)}\n```\nError: {error_msg}"
    
    try:
        result = repl.run(code)
        # Check if the result is an error message by looking for typical error patterns
        if isinstance(result, str) and ("Error" in result or "Exception" in result):
            return f"Error executing code:\n```python\n{code}\n```\nError: {result}"
    except BaseException as e:
        error_msg = repr(e)
        return f"Error executing code:\n```python\n{code}\n```\nError: {error_msg}"

    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return result_str
