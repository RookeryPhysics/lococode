import os
import webbrowser
from lococode.actions.base import BaseTool

class OpenCurrentHtmlTool(BaseTool):
    """Slash command: /html  — opens the current file if it's an html file."""

    def __init__(self):
        super().__init__()
        self.name = "open_current_html"
        self.description = "Open the current file in the web browser if it is an HTML file. Usage: /html"
        self.pattern = r"^/html(?: *(.*))?"
        self.is_slash = True
        self.intent = "open_current_html"
        self.arg_description = None

    def execute(self, match, context):
        target_file = context.get("target_file")
        if not target_file:
            print("\033[31mError: No active file to open.\033[0m")
            return True

        if not target_file.lower().endswith(('.html', '.htm')):
            print(f"\033[31mError: Active file '{target_file}' is not an HTML file.\033[0m")
            return True

        if not os.path.exists(target_file):
            print(f"\033[31mError: File '{target_file}' does not exist.\033[0m")
            return True

        abs_path = os.path.abspath(target_file)
        url = 'file:///' + abs_path.replace('\\', '/')
        
        print(f"\033[36mOpening HTML file in browser: {abs_path}\033[0m")
        webbrowser.open(url)
        return True
