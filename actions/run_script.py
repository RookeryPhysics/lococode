import subprocess
from lococode.actions.base import BaseTool


class RunScriptSlashTool(BaseTool):
    """Slash command: /run <filename> — runs a Python script in the current directory."""

    def __init__(self):
        super().__init__()
        self.name = "run_script"
        self.description = "Run a Python script. Usage: /run <filename>"
        self.pattern = r"/run\s+(.+)"
        self.is_slash = True
        self.intent = "run_script"
        self.arg_description = "Python filename to run"

    def execute(self, match, context):
        filename = match.group(1).strip()
        return _run_python(filename)


class RunScriptTagTool(BaseTool):
    """Tag tool: <tool:run_script>filename</tool:run_script> — lets the model run a Python script."""

    def __init__(self):
        super().__init__()
        self.name = "run_script"
        self.description = "Run a Python script in the current directory"
        self.pattern = ""
        self.is_slash = False
        self.intent = None
        self.arg_description = None

    def execute(self, match, context):
        filename = match.group(1).strip()
        return _run_python(filename)


def _run_python(filename):
    """Runs `python <filename>` and prints stdout/stderr."""
    print(f"\033[92mRunning: python {filename}\033[0m")
    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout:
            print(f"\033[97m{result.stdout}\033[0m")
        if result.stderr:
            print(f"\033[31m{result.stderr}\033[0m")
        if result.returncode == 0:
            print(f"\033[32mScript finished successfully.\033[0m")
        else:
            print(f"\033[31mScript exited with code {result.returncode}.\033[0m")
    except subprocess.TimeoutExpired:
        print("\033[31mError: Script timed out after 60 seconds.\033[0m")
    except FileNotFoundError:
        print(f"\033[31mError: '{filename}' not found.\033[0m")
    except Exception as e:
        print(f"\033[31mError running script: {e}\033[0m")
    return True
