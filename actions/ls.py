import subprocess
import os
from lococode.actions.base import BaseTool

class LsTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "ls"
        self.description = "List all files in the same directory as cli.py. Usage: /ls"
        self.pattern = r"^/ls(?: *(.*))?"
        self.is_slash = True
        self.intent = "ls"

    def execute(self, match, context):
        # We can get the project root by going up one level from this file's directory.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # print(f"\033[34mListing files in: {project_root}\033[0m")
        
        try:
            # Run 'dir' command on Windows, 'ls' on others
            if os.name == 'nt':
                # cmd /c dir lists files. /b for bare format if we wanted, but the user asked for "dir command"
                result = subprocess.run("dir", cwd=project_root, capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(["ls", "-F"], cwd=project_root, capture_output=True, text=True)
            
            if result.stdout:
                # print("\033[32m--- Files ---\033[0m")
                print(result.stdout)
            if result.stderr:
                print(f"\033[31m{result.stderr}\033[0m")
                
        except Exception as e:
            print(f"\033[31mFailed to list files: {e}\033[0m")
            
        return True
