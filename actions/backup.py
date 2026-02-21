import os
import time
import shutil
from lococode.actions.base import BaseTool

class BackupTool(BaseTool):
    """Slash command: /backup  — creates a backup of the current file."""

    def __init__(self):
        super().__init__()
        self.name = "backup"
        self.description = "Create a copy of the current file in the same directory. Usage: /backup"
        self.pattern = r"/backup(?: *(.*))?"
        self.is_slash = True
        self.intent = "backup"
        self.arg_description = None

    def execute(self, match, context):
        target_file = context.get("target_file")
        
        # If user explicitly provided a file to backup
        arg = match.group(1) if len(match.groups()) > 0 else None
        if arg and arg.strip():
            target = arg.strip()
            if os.path.exists(target):
                target_file = target
                
        if not target_file or not os.path.exists(target_file):
            print(f"\033[31mError: No valid file to backup ({target_file}).\033[0m")
            return True

        filename, ext = os.path.splitext(target_file)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = f"{filename}_backup_{timestamp}{ext}"

        try:
            shutil.copy2(target_file, backup_file)
            print(f"\033[32mCreated backup of {os.path.basename(target_file)} at: {os.path.basename(backup_file)}\033[0m")
        except Exception as e:
            print(f"\033[31mError creating backup: {e}\033[0m")
            
        return True
