import os
from lococode.actions.base import BaseTool

class SaveSessionTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "save_session"
        self.description = "Save the console session history to a text file. Usage: /s [filename]"
        self.pattern = r"^/s(?: +(.+))?$"
        self.is_slash = True
        self.intent = "save_session"
        self.arg_description = "filename"

    def execute(self, match, context):
        filename = match.group(1).strip() if match.group(1) else "session_history.txt"
        history = context.get('session_history', [])
        
        if not history:
            print("\033[33mNo session history to save yet.\033[0m")
            return True
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for item in history:
                    f.write(item + '\n\n')
            print(f"\033[32mSession history saved to {filename}\033[0m")
        except Exception as e:
            print(f"\033[31mFailed to save session history: {e}\033[0m")
            
        return True
