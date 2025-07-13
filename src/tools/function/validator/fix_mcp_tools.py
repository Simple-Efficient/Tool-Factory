import json
import os
import re
from typing import Dict, Any, List

def fix_mcp_tool(config_path: str, fixes: dict = {}, issues_description: str = "") -> str:
    """Fix MCP tool according to the given fixes.
    
    Args:
        config_path: Path to the MCP config file.
        fixes: Dictionary of fixes, supports:
            - "description": "New description content"
            - "add_parameters": {"param_name": {"type": "string", "description": "Parameter description"}}
            - "function_name": "New function name"
            - "server_name": "New server name"
        issues_description: Description of the issues.
        
    Returns:
        str: Description of the fix result.
    
    Example usage:
        # Fix missing description
        fix_mcp_tool(config_path, {
            "description": "This is an echo tool for outputting user-provided text."
        }, "Missing tool description")
        
        # Fix missing parameters
        fix_mcp_tool(config_path, {
            "add_parameters": {
                "text": {"type": "string", "description": "Text to echo back"}
            }
        }, "Missing required parameters")
        
        # Fix based on validation result (manually construct fix parameters)
        validation_result = check_mcp_description_from_config(config_path)
        if not validation_result["valid"]:
            issues = validation_result["issues"]
            if any("description not provided" in issue for issue in issues):
                fix_mcp_tool(config_path, {
                    "description": "Description written according to tool function."
                }, "; ".join(issues))
    """
    if not fixes:
        return f"No fixes provided"
        
    try:
        # Check if config file exists
        if not os.path.exists(config_path):
            return f"Config file does not exist: {config_path}"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'mcpServers' not in config:
            return "Config file format error: 'mcpServers' node not found"
        
        fixed_files = []
        details = []
        
        for server_name, server_config in config['mcpServers'].items():
            if 'args' not in server_config or not server_config['args']:
                continue
                
            py_file_path = server_config['args'][0]
            if not os.path.isabs(py_file_path):
                py_file_path = os.path.join(os.path.dirname(config_path), py_file_path)
            
            if not os.path.exists(py_file_path):
                details.append(f"Python file does not exist: {py_file_path}")
                continue
                
            # Read Python file content
            with open(py_file_path, 'r', encoding='utf-8') as f:
                py_content = f.read()
            
            original_content = py_content
            
            # 1. Fix description
            if "description" in fixes:
                new_desc = fixes["description"]
                details.append(f"Fix description: {new_desc}")
                
                # Find @mcp.tool decorator
                tool_pattern = r'(@mcp\.tool\([^)]*\))'
                
                def replace_description(match):
                    tool_decorator = match.group(1)
                    if 'description=' in tool_decorator:
                        # Replace existing description
                        desc_pattern = r'description\s*=\s*["\'][^"\']*["\']'
                        new_decorator = re.sub(desc_pattern, f'description="{new_desc}"', tool_decorator)
                    else:
                        # Add description
                        if tool_decorator.endswith(')'):
                            # Check if decorator is empty
                            if tool_decorator == '@mcp.tool()':
                                new_decorator = tool_decorator[:-1] + f'description="{new_desc}")'
                            else:
                                new_decorator = tool_decorator[:-1] + f', description="{new_desc}")'
                        else:
                            new_decorator = tool_decorator + f', description="{new_desc}"'
                    return new_decorator
                
                py_content = re.sub(tool_pattern, replace_description, py_content)
                
                # If @mcp.tool decorator not found, try to add it
                if '@mcp.tool' not in py_content:
                    # Find function definition
                    func_pattern = r'(def\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+\s*)?:)'
                    
                    def add_decorator(match):
                        func_def = match.group(1)
                        return f'@mcp.tool(description="{new_desc}")\n{func_def}'
                    
                    py_content = re.sub(func_pattern, add_decorator, py_content, count=1)
            
            # 2. Add missing parameters
            if "add_parameters" in fixes:
                params = fixes["add_parameters"]
                details.append(f"Add parameters: {list(params.keys())}")
                
                # Find function definition and add parameters
                func_pattern = r'(def\s+\w+\s*\()([^)]*?)(\)\s*(?:->\s*\w+\s*)?:)'
                
                def add_parameters(match):
                    func_start = match.group(1)
                    existing_params = match.group(2).strip()
                    func_end = match.group(3)
                    
                    new_params = []
                    for param_name, param_info in params.items():
                        param_type = param_info.get("type", "str")
                        # Simple type mapping
                        type_mapping = {
                            "string": "str",
                            "integer": "int", 
                            "number": "float",
                            "boolean": "bool"
                        }
                        python_type = type_mapping.get(param_type, "str")
                        new_params.append(f"{param_name}: {python_type}")
                    
                    if existing_params:
                        all_params = existing_params + ", " + ", ".join(new_params)
                    else:
                        all_params = ", ".join(new_params)
                    
                    return func_start + all_params + func_end
                
                py_content = re.sub(func_pattern, add_parameters, py_content, count=1)
            
            # 3. Fix function name
            if "function_name" in fixes:
                new_func_name = fixes["function_name"]
                details.append(f"Fix function name: {new_func_name}")
                
                # Find and replace function definition
                func_pattern = r'def\s+(\w+)\s*\('
                py_content = re.sub(func_pattern, f'def {new_func_name}(', py_content, count=1)
                
                # Update name parameter in @mcp.tool
                name_pattern = r'(name\s*=\s*["\"]) [^"\']* (["\"])'
                py_content = re.sub(name_pattern, f'\\1{new_func_name}\\2', py_content)
            
            # 4. Fix server name
            if "server_name" in fixes:
                new_server_name = fixes["server_name"]
                details.append(f"Fix server name: {new_server_name}")
                
                # Find FastMCP instantiation
                fastmcp_pattern = r'(FastMCP\s*\(\s*["\"]) [^"\']* (["\"])'
                py_content = re.sub(fastmcp_pattern, f'\\1{new_server_name}\\2', py_content)
            
            # If content changed, create fixed version
            if py_content != original_content:
                # Create fixed version of Python file
                base_name = os.path.splitext(os.path.basename(py_file_path))[0]
                fixed_py_path = os.path.join(os.path.dirname(py_file_path), f"{base_name}_fixed.py")
                
                with open(fixed_py_path, 'w', encoding='utf-8') as f:
                    f.write(py_content)
                fixed_files.append(fixed_py_path)
                
                # Update config file path
                config['mcpServers'][server_name]['args'][0] = os.path.basename(fixed_py_path)
        
        # Create fixed version of config file
        base_name = os.path.splitext(os.path.basename(config_path))[0]
        fixed_config_path = os.path.join(os.path.dirname(config_path), f"{base_name}_fixed.json")
        
        with open(fixed_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        fixed_files.append(fixed_config_path)
        
        message = f"Fix successful!\n"
        message += f"Issue description: {issues_description}\n"
        message += f"Fix details: {'; '.join(details)}\n"
        message += f"Generated files: {', '.join(fixed_files)}"
        return message
    except Exception as e:
        return f"Fix failed: {str(e)}"