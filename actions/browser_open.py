import webbrowser
import os
from lococode.actions.base import BaseTool

class BrowserOpenTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "browser_open"
        self.description = "Open the current file in the default browser. Usage: /open"
        self.pattern = r"/open"
        self.is_slash = True
        self.intent = "browser_open"

    def execute(self, match, context):
        target_file = context.get('target_file', 'index.html')
        print(f"\033[92mOpening {target_file} in default browser...\033[0m")
        webbrowser.open('file://' + os.path.abspath(target_file))
        return True
