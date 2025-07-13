import os
import json

from loguru import logger
from typing import Any, Dict, List, Callable
from inspect import Parameter, Signature

from src.utils.mcp_manager import MCPManager

_config_cache = {}

def get_python_type_from_schema(schema: dict) -> type:
    """
    Return the corresponding Python type based on the 'type' field in the schema.

    Args:
        schema (dict): parameter schema

    Returns:
        type: Corresponding Python type
    """
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    t = schema.get("type", "string")
    return type_map.get(t, str)

def _get_cached_callable_tools(mcp_config_path: str) -> Dict[str, Callable]:
    """
    Cached version of create_callable_mcp_tools to avoid reloading the same config file.
    """
    if mcp_config_path not in _config_cache: 
        _config_cache[mcp_config_path] = create_callable_mcp_tools(mcp_config_path)
    return _config_cache[mcp_config_path]

def load_mcp_tools(mcp_config_path: str) -> List[Callable]:
    """
    Batch load MCP tools from the config directory.
    
    Args:
        mcp_config_path (str): Path to MCP config directory
        
    Returns:
        List[Callable]: List of loaded callable tool functions
    """
    mcp_tools = []
    for root, dirs, files in os.walk(mcp_config_path):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    tools = load_mcp_config(file_path, return_callable=True)
                    mcp_tools.extend(tools)
                except Exception as e:
                    print(f"Error loading MCP config from {file_path}: {e}")
    return mcp_tools

def load_mcp_config(mcp_config_path: str, return_callable: bool = False) -> list:
    """
    Load MCP tools from a config file.
    
    Args:
        mcp_config_path (str): Path to MCP config file
        return_callable (bool): Whether to return callable functions instead of original tool objects

    Returns:
        list: List of loaded MCP tool objects or callable functions
    """
    try:
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        manager = MCPManager()
        tools = manager.initConfig(config)
        
        if return_callable:
            funcs = list(wrap_tools(tools).values())
            func_names = [func.__name__ for func in funcs]
            logger.info(f"Loaded MCP tools from config: {', '.join(func_names)}")
            return funcs
        else:
            # Return original tool object list
            tool_names = [tool.name for tool in tools]
            print(f"Loaded MCP tools from config: {', '.join(tool_names)}")
            return tools

    except Exception as e:
        error_msg = f"Failed to load MCP config: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return []

def wrap_tools(tools: List[Any]) -> Dict[str, Callable]:
    """
    Wrap a list of tool objects as a dict of callable functions for direct use.

    Args:
        tools (List[Any]): List of tool objects

    Returns:
        Dict[str, Callable]: Mapping from tool name to wrapped function
    """
    functions_map = {}

    for tool in tools:
        tool_name = getattr(tool, 'name', f"tool_{id(tool)}")

        def create_wrapper(tool_obj):
            params = tool_obj.function.get("parameters", {})
            logger.info(params)

            param_items = []
            if isinstance(params, dict) and "properties" in params:
                for name, value in params["properties"].items():
                    param_items.append((name, value))
            elif isinstance(params, dict):
                for name, value in params.items():
                    param_items.append((name, value))
            else:
                param_items = []

            def wrapper(*args, **kwargs):
                """
                Tool wrapper function. Accepts args/kwargs and returns tool execution result.

                Args:
                    *args, **kwargs: Tool parameters

                Returns:
                    str: Tool execution result
                """
                try:
                    if 'args' in kwargs and 'kwargs' in kwargs:
                        args_str = kwargs.get('args', '')
                        kwargs_str = kwargs.get('kwargs', '')
                        params = {}
                        
                        # Parse kwargs string
                        if kwargs_str and kwargs_str.strip():
                            try:
                                params.update(json.loads(kwargs_str))
                            except json.JSONDecodeError:
                                kwargs_fixed = kwargs_str.replace('="', ':"').replace('"="', '":"')
                                try:
                                    params.update(json.loads(kwargs_fixed))
                                except json.JSONDecodeError:
                                    pass
                        
                        # Parse args string
                        if args_str and args_str.strip():
                            try:
                                args_data = json.loads(args_str)
                                if isinstance(args_data, dict):
                                    params.update(args_data)
                            except json.JSONDecodeError:
                                pass
                        params_json = json.dumps(params, ensure_ascii=False)
                    elif args and isinstance(args[0], dict):
                        params_json = json.dumps(args[0], ensure_ascii=False)
                    else:
                        params_json = json.dumps(kwargs, ensure_ascii=False)
                    return tool_obj.call(params_json)
                except Exception as e:
                    return f"Tool call error: {str(e)}"
                    
            # Set function name and docstring
            wrapper.__name__ = tool_obj.name if hasattr(tool_obj, 'name') else f"tool_{id(tool_obj)}"
            wrapper.__qualname__ = wrapper.__name__
            wrapper.__doc__ = tool_obj.description if hasattr(tool_obj, 'description') else ""
            
            # Set function signature and type annotations
            sig = Signature([
                Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, annotation=get_python_type_from_schema(value))
                for name, value in param_items
            ])
            wrapper.__signature__ = sig
            wrapper.__annotations__ = {name: get_python_type_from_schema(value) for name, value in param_items}
            
            wrapper.mcp_tool = tool_obj
            wrapper.parameters = getattr(tool_obj, 'parameters', {})
            wrapper.description = getattr(tool_obj, 'description', '')
            return wrapper
            
        functions_map[tool_name] = create_wrapper(tool)
    return functions_map

def mcp_tool_to_callable(mcp_tool) -> Callable:
    """
    Convert an MCP tool object to a callable function. 
    
    Args:
        mcp_tool: MCP tool object, must have a call method
        
    Returns:
        Callable: Callable function that accepts dict parameters and returns a string result
    """
    tools_dict = wrap_tools([mcp_tool])
    if tools_dict:
        return next(iter(tools_dict.values()))
    def callable_wrapper(*args, **kwargs):
        try:
            if 'args' in kwargs and 'kwargs' in kwargs:
                args_str = kwargs.get('args', '')
                kwargs_str = kwargs.get('kwargs', '')
                params = {}
                if kwargs_str and kwargs_str.strip():
                    try:
                        params.update(json.loads(kwargs_str))
                    except json.JSONDecodeError:
                        kwargs_fixed = kwargs_str.replace('="', ':"').replace('"="', '":"')
                        try:
                            params.update(json.loads(kwargs_fixed))
                        except json.JSONDecodeError:
                            pass
                if args_str and args_str.strip():
                    try:
                        args_data = json.loads(args_str)
                        if isinstance(args_data, dict):
                            params.update(args_data)
                    except json.JSONDecodeError:
                        pass
                params_json = json.dumps(params)
            elif args and isinstance(args[0], dict):
                params_json = json.dumps(args[0])
            else:
                params_json = json.dumps(kwargs)
            return mcp_tool.call(params_json)
        except Exception as e:
            return f"Tool call error: {str(e)}"
    callable_wrapper.__name__ = getattr(mcp_tool, 'name', 'mcp_tool')
    callable_wrapper.__doc__ = getattr(mcp_tool, 'description', 'MCP Tool')
    callable_wrapper.mcp_tool = mcp_tool
    callable_wrapper.parameters = getattr(mcp_tool, 'parameters', {})
    callable_wrapper.description = getattr(mcp_tool, 'description', '')
    return callable_wrapper

def create_callable_mcp_tools(config_path: str) -> Dict[str, Callable]:
    """
    Load MCP tools from config file and convert to a dict of callable functions.
    
    Args:
        config_path (str): Path to MCP config file
        
    Returns:
        Dict[str, Callable]: Mapping from tool name to callable function
    """
    tools = load_mcp_config(config_path)
    callable_tools = wrap_tools(tools)
    return callable_tools

def get_mcp_tools_schema(config_path_or_tool) -> Dict[str, Dict[str, Any]]:
    """
    Get the parameter schema and description for MCP tools. Accepts config file path or tool object.
    If a config file path is provided, only the first tool's schema and description are returned.

    Args:
        config_path_or_tool: MCP config file path or tool object

    Returns:
        Dict[str, Dict[str, Any]]: Parameter schema and description for the tool, format:
            {
                tool_name: {
                    "parameters": ...,
                    "description": ...
                }
            }
    """
    if isinstance(config_path_or_tool, str):
        # If a config file path is provided
        callable_tools = _get_cached_callable_tools(config_path_or_tool)
        if not callable_tools:
            logger.info("----get_mcp_tools_schema----: No MCP tools found")
            return {}
        first_tool_name = next(iter(callable_tools.keys()))
        first_tool = callable_tools[first_tool_name]
        schema = {
            first_tool_name: {
                "parameters": getattr(first_tool, 'parameters', {}),
                "description": getattr(first_tool, 'description', '')
            }
        }
        logger.info(f"----get_mcp_tools_schema----: {schema}")
        return schema
    else:
        tool_name = getattr(config_path_or_tool, 'name', 'unknown_tool')
        return {
            tool_name: {
                "parameters": getattr(config_path_or_tool, 'parameters', {}),
                "description": getattr(config_path_or_tool, 'description', '')
            }
        }
