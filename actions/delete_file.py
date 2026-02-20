import os
from lococode.actions.base import BaseTool

class DeleteFileTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "delete_file"
        self.description = "Delete a file. Usage: /del <filename>"
        self.pattern = r"^/del\s+(.+)$"
        self.is_slash = True
        self.intent = "delete_file"
        self.arg_description = "filename to delete"

    def execute(self, match, context):
        file_to_del = match.group(1).strip()
        if os.path.exists(file_to_del):
            # Save backup before deletion
            if 'save_backup' in context:
                context['save_backup'](context, file_to_del)
            
            try:
                os.remove(file_to_del)
                print(f"\033[32mDeleted {file_to_del}\033[0m")
                if file_to_del == context.get('target_file'):
                     context['target_file'] = "index.html"
                     if not os.path.exists("index.html"):
                        with open("index.html", 'w', encoding='utf-8') as f:
                            f.write("<html><body>Hello World</body></html>")
                     print(f"\033[33mCurrent file deleted. Switched to index.html\033[0m")
            except Exception as e:
                print(f"\033[31mError deleting {file_to_del}: {e}\033[0m")
        else:
            print(f"\033[31mError: {file_to_del} does not exist.\033[0m")
        return True
