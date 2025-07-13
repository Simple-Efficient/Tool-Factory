import inspect
import json

from typing import Any, Dict, List
from loguru import logger
from graph_agent.utils.mcp_utils import _get_cached_callable_tools


def validate_mcp_availability(mcp_tool, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the availability and effectiveness of an MCP tool.

    This function uses test cases automatically constructed from the original query to call the MCP tool, verify whether it can be invoked normally and complete the specified task, check whether the main function of the tool meets the task requirements, and whether the output meets expectations.
    If problems are found, detailed problem types and modification suggestions are provided to help the developer agent fix them.

    Args:
        mcp_tool: The MCP tool object or its callable wrapper to be validated.
        test_cases (List[Dict[str, Any]]): List of test cases, each case is a parameter dictionary.

    Returns:
        Dict[str, Any]: Validation results, including:
            - valid (bool): Whether all cases passed
            - issues (List[str]): Issues found
            - suggestions (List[str]): Suggestions for modification
            - details (List[Dict]): Execution details for each case
    """
    if isinstance(test_cases, str):
        test_cases = json.loads(test_cases)
        
    results = []
    issues = []
    suggestions = []

    for idx, case in enumerate(test_cases, 1):
        try:
            # Support callable wrappers and raw objects
            if hasattr(mcp_tool, 'call'):
                output = mcp_tool.call(json.dumps(case))
            else:
                # Directly callable objects
                output = mcp_tool(**case)
            results.append({
                'input': case,
                'output': output,
                'success': True
            })
        except Exception as e:
            issues.append(f"Test case {idx} failed: {str(e)}")
            suggestions.append(f"Please check the parameters and implementation of test case {idx} to ensure it can be called and returns results correctly.")
            results.append({
                'input': case,
                'error': str(e),
                'success': False
            })

    valid = all(r['success'] for r in results)
    if not valid and not suggestions:
        suggestions.append("Please fix the tool implementation or test case parameters according to the error information.")

    return {
        'valid': valid,
        'issues': issues,
        'suggestions': suggestions,
        'details': results
    }

def check_mcp_format(mcp_tool) -> Dict[str, Any]:
    """
    Check the parameter completeness and input format of the MCP tool, and output detailed conclusions and suggestions for modification.

    This function automatically checks the parameter schema of the MCP tool, specifically:
    - Check whether the 'parameters' attribute exists and contains top-level fields such as 'type', 'properties', and 'required';
    - Check whether each parameter contains a 'type' field;
    - Check whether the parameters in the 'required' list are all defined in 'properties';
    - Output all found issues and corresponding suggestions for developers to fix;
    - Return whether the check passed, the list of issues, suggestions, and the original parameter schema.

    Args:
        mcp_tool: The MCP tool object or its callable wrapper to be validated.

    Returns:
        Dict[str, Any]: Validation results, including:
            - valid (bool): Whether the check passed
            - issues (List[str]): Issues found
            - suggestions (List[str]): Suggestions for modification
            - parameters (dict): Original parameter schema
    """
    params_schema = getattr(mcp_tool, 'parameters', None)
    description = getattr(mcp_tool, 'description', '')
    issues = []
    suggestions = []

    if params_schema is None:
        return {'valid': False, 'issues': ['No parameters attribute found, unable to check parameter format.'], 'suggestions': ['Please add a parameters attribute to the tool.']}

    # Check top-level fields
    for field in ['type', 'properties', 'required']:
        if field not in params_schema:
            issues.append(f"Missing top-level field: {field}")
            suggestions.append(f"Please add the {field} field in parameters.")

    # Check 'type' field for each parameter
    if 'properties' in params_schema:
        for name, prop in params_schema['properties'].items():
            if 'type' not in prop:
                issues.append(f"Parameter {name} is missing the type field.")
                suggestions.append(f"Please add the type field for parameter {name}.")

    # Check required items
    if 'required' in params_schema:
        for req in params_schema.get('required', []):
            if req not in params_schema.get('properties', {}):
                issues.append(f"Required parameter {req} is not defined in properties.")
                suggestions.append(f"Please add the required parameter {req} in properties.")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'suggestions': suggestions,
        'parameters': params_schema
    }

def check_mcp_description(mcp_tool) -> Dict[str, Any]:
    """
    Check whether the description of the MCP tool is accurate and clear, and whether it fully reflects the tool's function and usage. Output detailed conclusions and suggestions for modification.

    This function automatically checks the description field of the MCP tool, specifically:
    - Check whether the description exists and is not empty;
    - Check whether the description length is reasonable (if too short, prompt to supplement);
    - If problems are found, detailed problem types and modification suggestions are provided for developers to fix;
    - Return whether the check passed, the list of issues, suggestions, and the description content.

    Args:
        mcp_tool: The MCP tool object or its callable wrapper to be validated.

    Returns:
        Dict[str, Any]: Validation results, including:
            - valid (bool): Whether the check passed
            - issues (List[str]): Issues found
            - suggestions (List[str]): Suggestions for modification
            - description (str): Description content
    """
    # Prefer attribute, then docstring
    description = getattr(mcp_tool, 'description', None)
    if not description:
        description = inspect.getdoc(mcp_tool)
    issues = []
    suggestions = []

    if not description or not description.strip():
        issues.append("Description is missing or empty.")
        suggestions.append("Please add a description for the tool, briefly explaining its function and usage.")
        return {
            'valid': False,
            'issues': issues,
            'suggestions': suggestions,
            'description': description or ""
        }

    # Check length
    if len(description.strip()) < 6:
        issues.append("Description is too short to fully reflect the tool's function and usage.")
        suggestions.append("Please provide a more detailed description, explaining the tool's function, input/output, and typical usage.")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'suggestions': suggestions,
        'description': description
    }

def check_mcp_format_from_config(config_path: str) -> Dict[str, Any]:
    """
    Check the parameter completeness and input format of the first tool directly from the MCP config file.

    Args:
        config_path (str): MCP config file path

    Returns:
        Dict[str, Any]: Validation results, same structure as check_mcp_format
    """
    callable_tools = _get_cached_callable_tools(config_path)
    if not callable_tools:
        return {
            'valid': False,
            'issues': ["No MCP tool found in the config file."],
            'suggestions': ["Please check the config file to ensure at least one MCP tool is included."],
            'parameters': {}
        }
    first_tool = next(iter(callable_tools.values()))
    result = check_mcp_format(first_tool)
    logger.info(f"----check_mcp_format_from_config----: {result}")
    return result

def check_mcp_description_from_config(config_path: str) -> Dict[str, Any]:
    """
    Check the description of the first tool directly from the MCP config file.

    Args:
        config_path (str): MCP config file path

    Returns:
        Dict[str, Any]: Validation results, same structure as check_mcp_description
    """
    callable_tools = _get_cached_callable_tools(config_path)
    if not callable_tools:
        return {
            'valid': False,
            'issues': ["No MCP tool found in the config file."],
            'suggestions': ["Please check the config file to ensure at least one MCP tool is included."],
            'description': ""
        }
    first_tool = next(iter(callable_tools.values()))
    result = check_mcp_description(first_tool)
    logger.info(f"----check_mcp_description_from_config----: {result}")
    return result

def validate_mcp_availability_from_config(config_path: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the availability and effectiveness of the first tool directly from the MCP config file.

    Args:
        config_path (str): MCP config file path
        test_cases (List[Dict[str, Any]]): List of test cases

    Returns:
        Dict[str, Any]: Validation results, same structure as validate_mcp_availability
    """
    callable_tools = _get_cached_callable_tools(config_path)
    if not callable_tools:
        return {
            'valid': False,
            'issues': ["No MCP tool found in the config file."],
            'suggestions': ["Please check the config file to ensure at least one MCP tool is included."],
            'details': []
        }
    first_tool = next(iter(callable_tools.values()))
    result = validate_mcp_availability(first_tool, test_cases)
    logger.info(f"----validate_mcp_availability_from_config----: {result}")
    return result