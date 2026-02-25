# LOCOCODE
Agentic tool use platform and coding CLI. Designed for local LLMs.

LOCOCODE is a new, lightweight command-line interface designed for rapid, AI-driven development. It integrates directly with **LM Studio**'s local API to process natural language instructions and apply modifications to your project files.

## Features

- **Intelligence-First Planning**: Every instruction passes through a planning engine that classifies intent and selects the necessary tools before execution.
- **Dynamic Action Registry**: Extensible architecture where new capabilities (slash commands and model tags) are loaded dynamically from the `/actions` directory.
- **Web-Enhanced Context**: Integrated web search capabilities allow the AI to fetch real-world data and documentation to inform its edits.
- **Iterative Refinement**: The `/loop` command allows for multi-pass code generation, automatically improving and testing code until it meets specifications.
- **Direct File Manipulation**: Automatically reads and updates code based on your prompts, maintaining project context seamlessly.
- **Rich Terminal UI**: Features a 3D animated splash screen, gradient banners, and colored logging for a premium developer experience.
- **Output Sanitization**: Automatically strips `<think>` tags and markdown artifacts, ensuring only clean code is saved to your files.

## Prerequisites

- **Python 3.x**
- **LM Studio**: Must be running with the "Local Server" enabled (default: port 1234). The following model is required:
  - `google/gemma-3n-e4b`

## Usage

1. **Start LM Studio**: Load your preferred model (e.g., Llama 3, Qwen 2.5) and ensure the local server is active.
2. **Launch the CLI**:
   ```bash
   python cli.py
   ```
3. **Select a Target**: By default, it looks for `index.html`. Use `/file <name>` to switch.

## How It Works

1. **Intent Classification**: The tool analyzes your prompt to determine if you want to edit code, search the web, run a script, or manage files.
2. **Context Assembly**: It gathers the target file content, search results, and tool definitions into a structured prompt.
3. **Execution**: The model generates the requested changes or tool calls.
4. **Post-Processing**: `LOCOCODE` executes any requested tools (like creating files) and applies code edits back to the source file after sanitizing output.

## Commands

| Command | Description |
| :--- | :--- |
| `/file <filename>` | Switch editing focus to a different file. |
| `/loop [n] <specs>` | Run `n` iterations (default 3) to refine code based on specifications. |
| `/search <query>` | Search the web and select content to add to the AI's context. |
| `/make <filename>` | Create a new file and switch focus to it. |
| `/del <filename>` | Delete a file from the current directory. |
| `/clear` | Clear the terminal and reset the interface. |
| `/help` | List all available commands. |
| `/exit` | Close the CLI. |

## Model-Triggered Actions

The AI doesn't just write code; it can also perform actions by outputting special tags:
- `<tool:create_file>path/to/file</tool:create_file>`: Allows the AI to spawn new files during a code edit.
- `<tool:open_url>url</tool:open_url>`: Allows the AI to open documentation or previews for you.
- `<tool:run_script>script.py</tool:run_script>`: Allows the AI to test its own code or run utilities.
There are other tools, including a write_run tool that can create and execute a new action by writing and running a python script.

---
*Note: Ensure LM Studio is running before launching LOCOCODE.*
