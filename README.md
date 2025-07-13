# ToolFactory

ToolFactory is a modular, extensible, lightweight multi-agent tool development system. Built on the MCP protocol, it empowers models with the ability to autonomously create and dynamically invoke tools, adapting to various complex task requirements.

## What's New

**[2025/6/20]** First release of ToolFactory with support for dynamic tool creation and validation.

## Contents

- [Features](#1-features)
- [System Architecture](#2-system-architecture)
- [Getting Started](#3-getting-started)
- [Customizing Your System](#4-customizing-your-system)
- [Inspiration and Acknowledgments](#5-inspiration-and-acknowledgments)

## 1. Features

### Efficient Workflow Automation

ToolFactory enables the system to dynamically create execution paths based on task requirements. The framework employs a task decomposition approach, automatically breaking down complex tasks into manageable subtasks and assigning the most suitable agent and tool combinations for each. During execution, the system can adjust workflows based on intermediate results.

### Minimalist Tool Predefinition

ToolFactory follows a minimalist design philosophy, achieving maximum functional flexibility with minimal tool predefinition. The system only requires defining basic tool interfaces and core functionalities without exhaustively describing every possible tool detail. This approach maintains a lightweight structure while significantly reducing overall complexity and long-term maintenance costs.

### Self-Evolution Capability

Self-evolution capability enables the system to improve its functionality through continuous optimization. The system allows agents to explore new problem-solving methods independently, discovering and implementing encapsulations of new tools. Through this cycle of continuous self-improvement, ToolFactory becomes increasingly intelligent and efficient over time, capable of handling increasingly complex task scenarios.

### Tool Validation Mechanism

The tool validation mechanism ensures that each tool in the system can be correctly understood and effectively used by agents. The system includes specialized validation agents that systematically test tool functionality, ensuring that tool descriptions are clear, accurate, and contain the necessary usage parameters and constraints, significantly improving tool usability and task completion efficiency.

## 2. System Architecture

ToolFactory employs an orchestrator-worker architecture. The Planner Agent serves as the central commander, precisely coordinating the overall workflow and intelligently assigning specialized tasks to various expert sub-agents. These specialized agents can operate in parallel, optimizing resource utilization and significantly enhancing system response speed and processing efficiency.

### 2.1 Planner Agent

- **Intent Recognition**: Parse user requirements and determine needed tools
- **Task Decomposition**: Plan tool development and utilization strategies
- **Resource Coordination**: Assign tasks to specialized sub-agents
- **Result Optimization**: Improve output quality through multiple iterations

### 2.2 Searcher Agent

- **Intelligent Search**: Perform joint searches across multiple platforms, dynamically optimizing search strategies
- **Information Integration**: Obtain relevant discussions and solutions from developer communities
- **Resource Evaluation**: Filter high-quality tools and information that meet requirements

### 2.3 Developer Agent

- **Resource Management**: Retrieve, evaluate, and prioritize available tool libraries
- **Environment Building**: Create isolated environments, resolve dependency conflicts
- **Standardized Integration**: Convert tools into standard components compliant with the MCP protocol

### 2.4 Validator Agent

- **Compliance Validation**: Ensure interface conformance to specifications and correct parameter types
- **Functional Testing**: Perform comprehensive edge case testing
- **Consistency Check**: Verify that implemented functionality matches descriptions

## 3. Getting Started

### 3.1 Installation

```bash
# Create and activate a Python 3.9 virtual environment
conda create -n your_env python=3.10 

# Install dependencies
pip install -r requirements.txt
```

### 3.2 Environment Variable Setup

Configure LLM parameters in `src/.env` 

## 4. Customizing Your System

We provide several examples in the `examples` directory. To customize your personalized system, you should:

1. Create a task directory within `examples`;
2. Write configuration files for your agents;
3. Define the basic tools required;
4. Specify agent execution and collaboration patterns;
5. Pose a question—ToolFactory will handle it for you.

We provide a clear and concise example in the `examples` directory to demonstrate the practical application capabilities of the ToolFactory system. Using speech recognition as an example, this sample demonstrates how the system recognizes content in audio files. The command to run it is:

```bash
cd ToolFactory
python3 -m examples.audio_recognition.agent
```

## 5. Inspiration and Acknowledgments

This project draws inspiration from the Alita project pioneered by CharlesQ9, and the Claude multi-agent research system developed by Anthropic.

**Reference projects:**

- **Alita Project**: [CharlesQ9/Alita](https://github.com/CharlesQ9/Alita) on GitHub
- **Claude Multi-Agent Research System**: [Anthropic's Multi-Agent Research System](https://www.anthropic.com/research/multi-agent)

We sincerely thank the developers and contributors of the above works, as these cutting-edge projects have provided valuable ideas and technical foundations for ToolFactory.

## Contributors
- [Zhongni Hou](https://github.com/houzhongni) - LLM Algorithm Engineer @ Meituan
- [Hannan Bai](https://github.com/dqtcyh) - Algorithm Intern @ Meituan
- [Xiaokun Guan](https://github.com/biscuit279) - Algorithm Engineer @ Meituan
- [Yufei Zhang](https://github.com/zyf001) - Algorithm Engineer @ Meituan
- [Xihao Liang](https://github.com/liangxh) - Algorithm Engineer @ Meituan
- [Qun Liao](https://github.com/robink87) - Algorithm Engineer @ Meituan
- [Guojun Yin](https://github.com/gjyin) - Algorithm Engineer @ Meituan

## Join Us!

We're looking for collaborators to help us revolutionize ToolFactory. If you have any questions, encounter bugs, or would like to collaborate on development, please feel free to contact us!

1. Submit an issue directly on GitHub.
2. Help refine, optimize and expand our framework.
3. Contact us via email at chaijiajun@meituan.com or gjyin@outlook.com.