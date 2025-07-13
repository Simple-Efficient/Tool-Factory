import asyncio
import atexit
import datetime
import json
import threading
import time
import uuid

from loguru import logger
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from src.utils.schema import ContentItem
from src.utils.utils import has_chinese_chars, json_loads, print_traceback, save_url_to_local_work_dir

from jsonschema import SchemaError, ValidationError

TOOL_REGISTRY = {}


class ToolServiceError(Exception):

    def __init__(self,
                 exception: Optional[Exception] = None,
                 code: Optional[str] = None,
                 message: Optional[str] = None,
                 extra: Optional[dict] = None):
        if exception is not None:
            super().__init__(exception)
        else:
            super().__init__(f'\nError code: {code}. Error message: {message}')
        self.exception = exception
        self.code = code
        self.message = message
        self.extra = extra


def register_tool(name, allow_overwrite=False):

    def decorator(cls):
        if name in TOOL_REGISTRY:
            if allow_overwrite:
                logger.warning(f'Tool `{name}` already exists! Overwriting with class {cls}.')
            else:
                raise ValueError(f'Tool `{name}` already exists! Please ensure that the tool name is unique.')
        if cls.name and (cls.name != name):
            raise ValueError(f'{cls.__name__}.name="{cls.name}" conflicts with @register_tool(name="{name}").')
        cls.name = name
        TOOL_REGISTRY[name] = cls

        return cls

    return decorator


def is_tool_schema(obj: dict) -> bool:
    """
    Check if obj is a valid JSON schema describing a tool compatible with OpenAI's tool calling.
    Example valid schema:
    {
      "name": "get_current_weather",
      "description": "Get the current weather in a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"]
          }
        },
        "required": ["location"]
      }
    }
    """
    import jsonschema
    try:
        assert set(obj.keys()) == {'name', 'description', 'parameters'}
        assert isinstance(obj['name'], str)
        assert obj['name'].strip()
        assert isinstance(obj['description'], str)
        assert isinstance(obj['parameters'], dict)

        assert set(obj['parameters'].keys()) == {'type', 'properties', 'required'}
        assert obj['parameters']['type'] == 'object'
        assert isinstance(obj['parameters']['properties'], dict)
        assert isinstance(obj['parameters']['required'], list)
        assert set(obj['parameters']['required']).issubset(set(obj['parameters']['properties'].keys()))
    except AssertionError:
        return False
    try:
        jsonschema.validate(instance={}, schema=obj['parameters'])
    except SchemaError:
        return False
    except ValidationError:
        pass
    return True


class BaseTool(ABC):
    name: str = ''
    description: str = ''
    parameters: Union[List[dict], dict] = []

    def __init__(self, cfg: Optional[dict] = None):
        self.cfg = cfg or {}
        if not self.name:
            raise ValueError(
                f'You must set {self.__class__.__name__}.name, either by @register_tool(name=...) or explicitly setting {self.__class__.__name__}.name'
            )
        if isinstance(self.parameters, dict):
            if not is_tool_schema({'name': self.name, 'description': self.description, 'parameters': self.parameters}):
                raise ValueError(
                    'The parameters, when provided as a dict, must confirm to a valid openai-compatible JSON schema.')

    @abstractmethod
    def call(self, params: Union[str, dict], **kwargs) -> Union[str, list, dict, List[ContentItem]]:
        """The interface for calling tools.

        Each tool needs to implement this function, which is the workflow of the tool.

        Args:
            params: The parameters of func_call.
            kwargs: Additional parameters for calling tools.

        Returns:
            The result returned by the tool, implemented in the subclass.
        """
        raise NotImplementedError

    def _verify_json_format_args(self, params: Union[str, dict], strict_json: bool = False) -> dict:
        """Verify the parameters of the function call"""
        if isinstance(params, str):
            try:
                if strict_json:
                    params_json: dict = json.loads(params)
                else:
                    params_json: dict = json_loads(params)
            except json.decoder.JSONDecodeError:
                raise ValueError('Parameters must be formatted as a valid JSON!')
        else:
            params_json: dict = params
        if isinstance(self.parameters, list):
            for param in self.parameters:
                if 'required' in param and param['required']:
                    if param['name'] not in params_json:
                        raise ValueError('Parameters %s is required!' % param['name'])
        elif isinstance(self.parameters, dict):
            import jsonschema
            jsonschema.validate(instance=params_json, schema=self.parameters)
        else:
            raise ValueError
        return params_json

    @property
    def function(self) -> dict:  # Bad naming. It should be `function_info`.
        return {
            # 'name_for_human': self.name_for_human,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            # 'args_format': self.args_format
        }

    @property
    def name_for_human(self) -> str:
        return self.cfg.get('name_for_human', self.name)

    @property
    def args_format(self) -> str:
        fmt = self.cfg.get('args_format')
        if fmt is None:
            if has_chinese_chars([self.name_for_human, self.name, self.description, self.parameters]):
                fmt = '此工具的输入应为JSON对象。'
            else:
                fmt = 'Format the arguments as a JSON object.'
        return fmt


class MCPManager:
    _instance = None  # Private class variable to store the unique instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'clients'):  # The singleton should only be inited once
            """Set a new event loop in a separate thread"""
            try:
                import mcp  # noqa
            except ImportError as e:
                raise ImportError('Could not import mcp. Please install mcp with `pip install -U mcp`.') from e

            load_dotenv()  # Load environment variables from .env file
            self.clients: dict = {}
            self.loop = asyncio.new_event_loop()
            self.loop_thread = threading.Thread(target=self.start_loop, daemon=True)
            self.loop_thread.start()

            # A fallback way to terminate MCP tool processes after Qwen-Agent exits
            self.processes = []
            self.monkey_patch_mcp_create_platform_compatible_process()

    def monkey_patch_mcp_create_platform_compatible_process(self):
        try:
            import mcp.client.stdio
            target = mcp.client.stdio._create_platform_compatible_process
        except (ModuleNotFoundError, AttributeError) as e:
            raise ImportError('Qwen-Agent needs to monkey patch MCP for process cleanup. '
                              'Please upgrade MCP to a higher version with `pip install -U mcp`.') from e

        async def _monkey_patched_create_platform_compatible_process(*args, **kwargs):
            process = await target(*args, **kwargs)
            self.processes.append(process)
            return process

        mcp.client.stdio._create_platform_compatible_process = _monkey_patched_create_platform_compatible_process

    def start_loop(self):
        asyncio.set_event_loop(self.loop)

        # Set a global exception handler to silently handle cross-task exceptions from MCP SSE connections
        def exception_handler(loop, context):
            exception = context.get('exception')
            if exception:
                # Silently handle cross-task exceptions from MCP SSE connections
                if (isinstance(exception, RuntimeError) and
                        'Attempted to exit cancel scope in a different task' in str(exception)):
                    return  # Silently ignore this type of exception
                if (isinstance(exception, BaseExceptionGroup) and  # noqa
                        'Attempted to exit cancel scope in a different task' in str(exception)):  # noqa
                    return  # Silently ignore this type of exception

            # Other exceptions are handled normally
            loop.default_exception_handler(context)

        self.loop.set_exception_handler(exception_handler)
        self.loop.run_forever()

    def is_valid_mcp_servers(self, config: dict):
        """Example of mcp servers configuration:
        {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"]
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
                }
            }
        }
        """

        # Check if the top-level key "mcpServers" exists and its value is a dictionary
        if not isinstance(config, dict) or 'mcpServers' not in config or not isinstance(config['mcpServers'], dict):
            return False
        mcp_servers = config['mcpServers']
        # Check each sub-item under "mcpServers"
        for key in mcp_servers:
            server = mcp_servers[key]
            # Each sub-item must be a dictionary
            if not isinstance(server, dict):
                return False
            if 'command' in server:
                # "command" must be a string
                if not isinstance(server['command'], str):
                    return False
                # "args" must be a list
                if 'args' not in server or not isinstance(server['args'], list):
                    return False
            if 'url' in server:
                # "url" must be a string
                if not isinstance(server['url'], str):
                    return False
                # "headers" must be a dictionary
                if 'headers' in server and not isinstance(server['headers'], dict):
                    return False
            # If the "env" key exists, it must be a dictionary
            if 'env' in server and not isinstance(server['env'], dict):
                return False
        return True

    def initConfig(self, config: Dict):
        if not self.is_valid_mcp_servers(config):
            raise ValueError('Config of mcpservers is not valid')
        logger.info(f'Initializing MCP tools from mcp servers: {list(config["mcpServers"].keys())}')
        # Submit coroutine to the event loop and wait for the result
        future = asyncio.run_coroutine_threadsafe(self.init_config_async(config), self.loop)
        try:
            result = future.result()  # You can specify a timeout if desired
            return result
        except Exception as e:
            logger.info(f'Failed in initializing MCP tools: {e}')
            raise e

    async def init_config_async(self, config: Dict):
        tools: list = []
        mcp_servers = config['mcpServers']
        for server_name in mcp_servers:
            client = MCPClient()
            server = mcp_servers[server_name]
            await client.connection_server(mcp_server_name=server_name,
                                           mcp_server=server)  # Attempt to connect to the server

            client_id = server_name + '_' + str(
                uuid.uuid4())  # To allow the same server name be used across different running agents
            client.client_id = client_id  # Ensure client_id is set on the client instance
            self.clients[client_id] = client  # Add to clients dict after successful connection
            for tool in client.tools:
                """MCP tool example:
                {
                    "name": "read_query",
                    "description": "Execute a SELECT query on the SQLite database",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                            "type": "string",
                            "description": "SELECT SQL query to execute"
                            }
                        },
                        "required": ["query"]
                }
                """
                parameters = tool.inputSchema
                # The required field in inputSchema may be empty and needs to be initialized.
                if 'required' not in parameters:
                    parameters['required'] = []
                # Remove keys from parameters that do not conform to the standard OpenAI schema
                # Check if the required fields exist
                required_fields = {'type', 'properties', 'required'}
                missing_fields = required_fields - parameters.keys()
                if missing_fields:
                    raise ValueError(f'Missing required fields in schema: {missing_fields}')

                # Keep only the necessary fields
                cleaned_parameters = {
                    'type': parameters['type'],
                    'properties': parameters['properties'],
                    'required': parameters['required']
                }
                register_name = server_name + '-' + tool.name
                agent_tool = self.create_tool_class(register_name=register_name,
                                                    register_client_id=client_id,
                                                    tool_name=tool.name,
                                                    tool_desc=tool.description,
                                                    tool_parameters=cleaned_parameters)
                tools.append(agent_tool)

            if client.resources:
                """MCP resource example:
                {
                    uri: string;           // Unique identifier for the resource
                    name: string;          // Human-readable name
                    description?: string;  // Optional description
                    mimeType?: string;     // Optional MIME type
                }
                """
                # List resources
                list_resources_tool_name = server_name + '-' + 'list_resources'
                list_resources_params = {'type': 'object', 'properties': {}, 'required': []}
                list_resources_agent_tool = self.create_tool_class(
                    register_name=list_resources_tool_name,
                    register_client_id=client_id,
                    tool_name='list_resources',
                    tool_desc='Servers expose a list of concrete resources through this tool. '
                    'By invoking it, you can discover the available resources and obtain resource templates, which help clients understand how to construct valid URIs. '
                    'These URI formats will be used as input parameters for the read_resource function. ',
                    tool_parameters=list_resources_params)
                tools.append(list_resources_agent_tool)

                # Read resource
                resources_template_str = ''  # Check if there are resource templates
                try:
                    if client.session is not None:
                        list_resource_templates = await client.session.list_resource_templates()
                        if list_resource_templates.resourceTemplates:
                            resources_template_str = '\n'.join(
                                str(template) for template in list_resource_templates.resourceTemplates)

                except Exception as e:
                    logger.info(f'Failed in listing MCP resource templates: {e}')

                read_resource_tool_name = server_name + '-' + 'read_resource'
                read_resource_params = {
                    'type': 'object',
                    'properties': {
                        'uri': {
                            'type': 'string',
                            'description': 'The URI identifying the specific resource to access'
                        }
                    },
                    'required': ['uri']
                }
                original_tool_desc = 'Request to access a resource provided by a connected MCP server. Resources represent data sources that can be used as context, such as files, API responses, or system information.'
                if resources_template_str:
                    tool_desc = original_tool_desc + '\nResource Templates:\n' + resources_template_str
                else:
                    tool_desc = original_tool_desc
                read_resource_agent_tool = self.create_tool_class(register_name=read_resource_tool_name,
                                                                  register_client_id=client_id,
                                                                  tool_name='read_resource',
                                                                  tool_desc=tool_desc,
                                                                  tool_parameters=read_resource_params)
                tools.append(read_resource_agent_tool)

        return tools

    def create_tool_class(self, register_name, register_client_id, tool_name, tool_desc, tool_parameters):

        class ToolClass(BaseTool):
            name = register_name
            description = tool_desc
            parameters = tool_parameters
            client_id = register_client_id

            def call(self, params: Union[str, dict], **kwargs) -> str:
                if isinstance(params, str):
                    tool_args = json.loads(params)
                else:
                    tool_args = params
                # Submit coroutine to the event loop and wait for the result
                manager = MCPManager()
                client = manager.clients[self.client_id]
                future = asyncio.run_coroutine_threadsafe(client.execute_function(tool_name, tool_args), manager.loop)
                try:
                    result = future.result()
                    return result
                except Exception as e:
                    logger.info(f'Failed in executing MCP tool: {e}')
                    raise e

        ToolClass.__name__ = f'{register_name}_Class'
        return ToolClass()

    def shutdown(self):
        futures = []
        for client_id in list(self.clients.keys()):
            client: MCPClient = self.clients[client_id]
            future = asyncio.run_coroutine_threadsafe(client.cleanup(), self.loop)
            futures.append(future)
            del self.clients[client_id]
        time.sleep(1)  # Wait for the graceful cleanups, otherwise fall back

        # fallback
        if asyncio.all_tasks(self.loop):
            logger.info(
                'There are still tasks in `MCPManager().loop`, force terminating the MCP tool processes. There may be some exceptions.'
            )
            for process in self.processes:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass  # it's ok, the process may exit earlier

        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()


class MCPClient:

    def __init__(self):
        from mcp import ClientSession
        self.session: Optional[ClientSession] = None
        self.tools: Optional[list] = None
        self.exit_stack = AsyncExitStack()
        self.resources: bool = False
        self._last_mcp_server_name = None
        self._last_mcp_server = None
        self.client_id = None  # For replacing in MCPManager.clients

    async def connection_server(self, mcp_server_name, mcp_server):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.sse import sse_client
        from mcp.client.stdio import stdio_client
        from mcp.client.streamable_http import streamablehttp_client
        """Connect to an MCP server and retrieve the available tools."""
        # Save parameters
        self._last_mcp_server_name = mcp_server_name
        self._last_mcp_server = mcp_server

        try:
            if 'url' in mcp_server:
                url = mcp_server.get('url')
                sse_read_timeout = mcp_server.get('sse_read_timeout', 300)
                logger.info(f'{mcp_server_name} sse_read_timeout: {sse_read_timeout}s')
                if mcp_server.get('type', 'sse') == 'streamable-http':
                    # streamable-http mode
                    """streamable-http mode mcp example:
                    {"mcpServers": {
                            "streamable-mcp-server": {
                            "type": "streamable-http",
                            "url":"http://0.0.0.0:8000/mcp"
                            }
                        }
                    }
                    """
                    self._streams_context = streamablehttp_client(
                        url=url, sse_read_timeout=datetime.timedelta(seconds=sse_read_timeout))
                    read_stream, write_stream, get_session_id = await self.exit_stack.enter_async_context(
                        self._streams_context)
                    self._session_context = ClientSession(read_stream, write_stream)
                    self.session = await self.exit_stack.enter_async_context(self._session_context)
                else:
                    # sse mode
                    headers = mcp_server.get('headers', {'Accept': 'text/event-stream'})
                    self._streams_context = sse_client(url, headers, sse_read_timeout=sse_read_timeout)
                    streams = await self.exit_stack.enter_async_context(self._streams_context)
                    self._session_context = ClientSession(*streams)
                    self.session = await self.exit_stack.enter_async_context(self._session_context)
            else:
                server_params = StdioServerParameters(command=mcp_server['command'],
                                                      args=mcp_server['args'],
                                                      env=mcp_server.get('env', None))
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                self.stdio, self.write = stdio_transport
                self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
                # logger.info(
                #     f'Initializing a MCP stdio_client, if this takes forever, please check the config of this mcp server: {mcp_server_name}'
                # )

            await self.session.initialize()
            list_tools = await self.session.list_tools()
            self.tools = list_tools.tools
            # try:
            #     list_resources = await self.session.list_resources()  # Check if the server has resources
            #     if list_resources.resources:
            #         self.resources = True
            # except Exception:
            #     # logger.info(f"No list resources: {e}")
            #     pass
        except Exception as e:
            logger.warning(f'Failed in connecting to MCP server: {e}')
            raise e

    async def reconnect(self):
        # Create a new MCPClient and connect
        if self.client_id is None:
            raise RuntimeError(
                'Cannot reconnect: client_id is None. This usually means the client was not properly registered in MCPManager.'
            )
        new_client = MCPClient()
        new_client.client_id = self.client_id
        await new_client.connection_server(self._last_mcp_server_name, self._last_mcp_server)
        return new_client

    async def execute_function(self, tool_name, tool_args: dict):
        from mcp.types import TextResourceContents

        # Check if session is alive
        try:
            if self.session is not None:
                await self.session.send_ping()
        except Exception as e:
            logger.info(f"Session is not alive, please increase 'sse_read_timeout' in the config, try reconnect: {e}")
            # Auto reconnect
            try:
                manager = MCPManager()
                if self.client_id is not None:
                    manager.clients[self.client_id] = await self.reconnect()
                    return await manager.clients[self.client_id].execute_function(tool_name, tool_args)
                else:
                    logger.info('Reconnect failed: client_id is None')
                    return 'Session reconnect (client creation) exception: client_id is None'
            except Exception as e3:
                logger.info(f'Reconnect (client creation) exception type: {type(e3)}, value: {repr(e3)}')
                return f'Session reconnect (client creation) exception: {e3}'
        if tool_name == 'list_resources':
            try:
                if self.session is not None:
                    list_resources = await self.session.list_resources()
                    if list_resources.resources:
                        resources_str = '\n\n'.join(str(resource) for resource in list_resources.resources)
                    else:
                        resources_str = 'No resources found'
                    return resources_str
                else:
                    return 'Session is not alive'
            except Exception as e:
                logger.info(f'No list resources: {e}')
                return f'Error: {e}'
        elif tool_name == 'read_resource':
            try:
                uri = tool_args.get('uri')
                if not uri:
                    raise ValueError('URI is required for read_resource')
                if self.session is not None:
                    read_resource = await self.session.read_resource(uri)
                    texts = []
                    for resource in read_resource.contents:
                        if isinstance(resource, TextResourceContents):
                            texts.append(resource.text)
                        # if isinstance(resource, BlobResourceContents):
                        #     texts.append(resource.blob)
                    if texts:
                        return '\n\n'.join(texts)
                    else:
                        return 'Failed to read resource'
                else:
                    return 'Session is not alive'
            except Exception as e:
                logger.info(f'Failed to read resource: {e}')
                return f'Error: {e}'
        else:
            if self.session is not None:
                response = await self.session.call_tool(tool_name, tool_args)
                texts = []
                for content in response.content:
                    if content.type == 'text':
                        texts.append(content.text)
                if texts:
                    return '\n\n'.join(texts)
                else:
                    return 'execute error'
            else:
                return 'Session is not alive'

    async def cleanup(self):
        await self.exit_stack.aclose()


def _cleanup_mcp(_sig_num=None, _frame=None):
    if MCPManager._instance is None:
        return
    manager = MCPManager()
    manager.shutdown()

