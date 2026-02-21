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
        self.intent = "create_file"
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
        self.description = "Create a new file of the given filename."
        self.pattern = r"<tool:create_file>(.*?)</tool:create_file>"
        self.is_slash = False
        self.intent = None
        self.arg_description = None

    def execute(self, match, context):
        import json
        arg_text = match.group(1).strip()
        if not arg_text:
            return

        filename = None
        content = ""

        # Check if it looks like JSON or pseudo-JSON from the model
        if arg_text.startswith('{') or arg_text.startswith('args={'):
            json_text = arg_text
            if arg_text.startswith('args='):
                json_text = arg_text[5:]
            
            try:
                # Basic cleanup for common model mistakes in JSON
                json_text = json_text.replace("'", '"')
                data = json.loads(json_text)
                filename = data.get("filename")
                content = data.get("content", "")
            except Exception:
                # If JSON parsing fails, we'll try to extract filename with regex
                name_match = re.search(r'"filename":\s*"([^"]+)"', json_text)
                if name_match:
                    filename = name_match.group(1)
                
                content_match = re.search(r'"content":\s*"(.*)"', json_text, re.DOTALL)
                if content_match:
                    content = content_match.group(1).replace('\\n', '\n').replace('\\"', '"')

        # Fallback: if not parsed as JSON, treat the whole string as the filename
        if not filename:
            # Clean up potential "args=" or quotes if it's not JSON
            filename = re.sub(r'^(args=)?["\']?|["\']?$', '', arg_text).strip()

        if not filename:
            return

        if os.path.exists(filename) and not content:
            print(f"\033[33m[create_file] {filename} already exists.\033[0m")
            return

        try:
            # Create directories if needed
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\033[32m[create_file] Created {filename} with {len(content)} bytes\033[0m")
            context["target_file"] = filename
        except Exception as e:
            print(f"\033[31m[create_file] Error: {e}\033[0m")
