# ToolFactory

ToolFactory is a modular, extensible, lightweight multi-agent tool development system. Built on the MCP protocol, it empowers models with the ability to autonomously create and dynamically invoke tools, adapting to various complex task requirements.

## What's New

**🔥 [2025/7/14]** First release of ToolFactory with support for dynamic tool creation and validation.

## Features

### Efficient Workflow Automation

ToolFactory enables the system to dynamically create execution paths based on task requirements. The framework employs a task decomposition approach, automatically breaking down complex tasks into manageable subtasks and assigning the most suitable agent and tool combinations for each. During execution, the system can adjust workflows based on intermediate results.

### Minimalist Tool Predefinition

ToolFactory follows a minimalist design philosophy, achieving maximum functional flexibility with minimal tool predefinition. The system only requires defining basic tool interfaces and core functionalities without exhaustively describing every possible tool detail. This approach maintains a lightweight structure while significantly reducing overall complexity and long-term maintenance costs.

### Self-Evolution Capability

Self-evolution capability enables the system to improve its functionality through continuous optimization. The system allows agents to explore new problem-solving methods independently, discovering and implementing encapsulations of new tools. Through this cycle of continuous self-improvement, ToolFactory becomes increasingly intelligent and efficient over time, capable of handling increasingly complex task scenarios.

### Tool Validation Mechanism

The tool validation mechanism ensures that each tool in the system can be correctly understood and effectively used by agents. The system includes specialized validation agents that systematically test tool functionality, ensuring that tool descriptions are clear, accurate, and contain the necessary usage parameters and constraints, significantly improving tool usability and task completion efficiency.

## System Architecture

ToolFactory employs an orchestrator-worker architecture. The Planner Agent serves as the central commander, precisely coordinating the overall workflow and intelligently assigning specialized tasks to various expert sub-agents. These specialized agents can operate in parallel, optimizing resource utilization and significantly enhancing system response speed and processing efficiency.

### 🧠 Planner Agent

- **Intent Recognition**: Parse user requirements and determine needed tools
- **Task Decomposition**: Plan tool development and utilization strategies
- **Resource Coordination**: Assign tasks to specialized sub-agents
- **Result Optimization**: Improve output quality through multiple iterations

### 🔍 Searcher Agent

- **Intelligent Search**: Perform joint searches across multiple platforms, dynamically optimizing search strategies
- **Information Integration**: Obtain relevant discussions and solutions from developer communities
- **Resource Evaluation**: Filter high-quality tools and information that meet requirements

### 🔧 Developer Agent

- **Resource Management**: Retrieve, evaluate, and prioritize available tool libraries
- **Environment Building**: Create isolated environments, resolve dependency conflicts
- **Standardized Integration**: Convert tools into standard components compliant with the MCP protocol

### 🛡️ Validator Agent

- **Compliance Validation**: Ensure interface conformance to specifications and correct parameter types
- **Functional Testing**: Perform comprehensive edge case testing
- **Consistency Check**: Verify that implemented functionality matches descriptions

## Quick Start

1. Set up the Python environment:

    ```bash
    # Create and activate a Python 3.9 virtual environment
    conda create -n your_env python=3.10 

    # Install dependencies
    pip install -r requirements.txt
    ```

2. Configure LLM/Tools parameters in `src/.env` 

3. Define the basic tools and required in `src/tools`; 

4. Modify prompt files in `src/prompts`; 

5. Specify agent execution and collaboration patterns;

6. Pose a question—ToolFactory will handle it for you.

We provide a clear and concise example in the `examples` directory to demonstrate the practical application capabilities of the ToolFactory system. Using speech recognition as an example, this sample demonstrates how the system recognizes content in audio files. The command to run it is:

```bash
cd ToolFactory
python3 -m examples.audio_recognition.agent
```

## Inspiration and Acknowledgments

This project draws inspiration from the Alita project pioneered by CharlesQ9, and the Claude multi-agent research system developed by Anthropic.

**Reference projects:**

- **Alita Project**: [CharlesQ9/Alita](https://github.com/CharlesQ9/Alita) on GitHub
- **Claude Multi-Agent Research System**: [Anthropic's Multi-Agent Research System](https://www.anthropic.com/research/multi-agent)

We sincerely thank the developers and contributors of the above works, as these cutting-edge projects have provided valuable ideas and technical foundations for ToolFactory.

## 🌟 Join Us!

We're looking for collaborators to help us revolutionize ToolFactory. If you have any questions, encounter bugs, or would like to collaborate on development, please feel free to contact us!

1. Submit an issue directly on GitHub.
2. Help refine, optimize and expand our framework.
3. Contact us via email at zhangyufei08@meituan.com or gjyin@outlook.com.

## Contributors

We extend our heartfelt gratitude to all contributors who have made this project possible.

- [Guojun Yin](https://github.com/gjyin) - Senior Reseacher @ Meituan
- [Hannan Bai](https://github.com/dqtcyh) - LLM Algorithm Intern @ Meituan
- [Qun Liao](https://github.com/robink87) - LLM Algorithm Engineer @ Meituan
- [Xiaokun Guan](https://github.com/biscuit279) - LLM Algorithm Engineer @ Meituan
- [Xihao Liang](https://github.com/liangxh) - LLM Algorithm Engineer @ Meituan
- [Yufei Zhang](https://github.com/zyf001) - LLM Algorithm Engineer @ Meituan
- [Zhongni Hou](https://github.com/houzhongni) - LLM Algorithm Engineer @ Meituan

Contributors are listed in alphabetical order by first name.
