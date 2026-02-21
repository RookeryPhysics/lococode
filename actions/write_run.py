import sys
import subprocess
import os
from lococode.actions.base import BaseTool

class WriteRunTool(BaseTool):
    """Slash command: /write_run <prompt> — writes and executes a python script."""

    def __init__(self):
        super().__init__()
        self.name = "write_run"
        self.description = "Write and execute a python script based on the prompt. Usage: /write_run <prompt>"
        self.pattern = r"^/write_run\s+(.+)$"
        self.is_slash = True
        self.intent = "write_run"
        self.arg_description = "prompt to write and execute"

    def execute(self, match, context):
        prompt = match.group(1).strip()
        
        apply_edit = context.get('apply_edit')
        registry = context.get('registry')
        model_id = context.get('model_id')

        if not prompt:
            print("\033[31mError: Please provide a prompt.\033[0m")
            return True

        i = 1
        while True:
            new_file = f"script_{i}.py"
            if not os.path.exists(new_file):
                break
            i += 1

        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("")

        print(f"\033[32mCreated and switched to {new_file}\033[0m")
        context['target_file'] = new_file
        target_file = new_file

        if 'print_status' in context:
            context['print_status'](context)
             
        print(f"\033[92mWriting script based on prompt: {prompt}\033[0m")
        success = apply_edit(
            target_file,
            prompt,
            model_id,
            registry,
            context,
            verbose=True,
            preplanned_intent={"intent": "code_edit", "args": None, "tags_needed": [], "reasoning": "Preplanned code editing for write_run action"}
        )
        
        if success:
            print(f"\n\033[92mExecuting {target_file}...\033[0m")
            try:
                # Use sys.executable to ensure we use the same Python environment
                result = subprocess.run([sys.executable, target_file], capture_output=True, text=True)
                
                if result.stdout:
                    print("\033[32m--- Output ---\033[0m")
                    print(result.stdout)
                
                if result.stderr:
                    print("\033[31m--- Errors ---\033[0m")
                    print(result.stderr)
                    
            except Exception as e:
                print(f"\033[31mError executing script: {e}\033[0m")
        else:
            print("\033[31mFailed to write the code. Execution skipped.\033[0m")
        
        return True
