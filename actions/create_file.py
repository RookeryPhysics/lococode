import os
from lococode.actions.base import BaseTool


class CreateFileTool(BaseTool):
    """Slash command: /make <filename>  — creates a new file."""

    def __init__(self):
        super().__init__()
        self.name = "create_file"
        self.description = "Create a new file. Usage: /make <filename>"
        self.pattern = r"/make\s+(.+)"
        self.is_slash = True
        self.intent = "file_create"
        self.arg_description = "filename to create"

    def execute(self, match, context):
        filename = match.group(1).strip()
        if not filename:
            print("\033[31mError: Please provide a filename.\033[0m")
            return True

        if os.path.exists(filename):
            print(f"\033[33m{filename} already exists. Switching to it.\033[0m")
            context["target_file"] = filename
            return True

        # Create parent directories if needed
        parent = os.path.dirname(filename)
        if parent:
            os.makedirs(parent, exist_ok=True)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("")
            context["target_file"] = filename
            print(f"\033[32mCreated {filename} and switched to it.\033[0m")
        except Exception as e:
            print(f"\033[31mError creating {filename}: {e}\033[0m")
        return True


class CreateFileTag(BaseTool):
    """Model tag: <tool:create_file>filename</tool:create_file>  — lets the model create files."""

    def __init__(self):
        super().__init__()
        self.name = "create_file"
        self.description = "Create a new file at the given path"
        self.pattern = r"<tool:create_file>(.*?)</tool:create_file>"
        self.is_slash = False
        self.intent = None
        self.arg_description = None

    def execute(self, match, context):
        filename = match.group(1).strip()
        if not filename:
            return

        if os.path.exists(filename):
            print(f"\033[33m[create_file] {filename} already exists.\033[0m")
            return

        parent = os.path.dirname(filename)
        if parent:
            os.makedirs(parent, exist_ok=True)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("")
            print(f"\033[32m[create_file] Created {filename}\033[0m")
        except Exception as e:
            print(f"\033[31m[create_file] Error: {e}\033[0m")
