import os
from lococode.actions.base import BaseTool

class FileSwitchTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "file_switch"
        self.description = "Switch to editing a different file. Usage: /file <filename>"
        self.pattern = r"^/file\s+(.+)$"
        self.is_slash = True
        self.intent = "file_switch"
        self.arg_description = "filename to switch to"

    def execute(self, match, context):
        new_file = match.group(1).strip()
        context['target_file'] = new_file
        if not os.path.exists(new_file):
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write("<html><body>Hello World</body></html>")
            print(f"\033[32mCreated and switched to {new_file}\033[0m")
        else:
            print(f"\033[32mSwitched to {new_file}\033[0m")
            
        if 'print_status' in context:
            context['print_status'](context)
        return True
