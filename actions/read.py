import os
from lococode.actions.base import BaseTool

class ReadTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "read"
        self.description = "Read another file into context for the next prompt. Usage: /read <filename>"
        self.pattern = r"^/read\s+(.+)$"
        self.is_slash = True
        self.intent = "read"
        self.arg_description = "filename"

    def execute(self, match, context):
        filename = match.group(1).strip()
        
        # We can get the project root by going up one level from this file's directory.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(project_root, filename)
        
        if not os.path.exists(file_path):
            # Try absolute path or relative to CWD
            file_path = os.path.abspath(filename)
            
        if not os.path.exists(file_path):
            print(f"\033[31mError: File not found: {filename}\033[0m")
            return True # Still return True so we don't try to 'edit' the /read command
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add to search_results so it gets included in the next prompt
            if "search_results" not in context:
                context["search_results"] = []
            
            context["search_results"].append(f"Content of {filename}:\n```\n{content}\n```")
            print(f"\033[32mRead {filename} into context.\033[0m")
            
        except Exception as e:
            print(f"\033[31mFailed to read file: {e}\033[0m")
            
        return True
