import os
from lococode.actions.base import BaseTool

class ClearConsoleTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "clear_console"
        self.description = "Clear the console and reprint the banner. Usage: /clear"
        self.pattern = r"^/clear$"
        self.is_slash = True
        self.intent = "clear_console"

    def execute(self, match, context):
        os.system('cls' if os.name == 'nt' else 'clear')
        if 'print_banner' in context:
            context['print_banner']()
        target = context.get('target_file')
        model = context.get('model_id')
        print(f"\n\033[1;34mEditing Mode: {target} | Model: {model}\033[0m")
        print("Type your instructions and press Enter. Type '/help' for a list of commands or '/exit' to quit.")
        return True
