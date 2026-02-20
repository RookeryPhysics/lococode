import re
from lococode.actions.base import BaseTool

class ModelSwitchTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "model"
        self.description = "Switch between 'fast' and 'thinking' models, or show current model. Usage: /model <fast|thinking>"
        self.pattern = r"^/model(?:\s+(.+))?$"
        self.is_slash = True
        self.intent = "model_switch"
        self.arg_description = "model mode (fast/thinking)"

    def execute(self, match, context):
        mode = match.group(1)
        if not mode:
            print(f"\033[36mCurrent model: {context['model_id']}\033[0m")
            return True
            
        mode = mode.strip().lower()
        if mode == 'fast':
            context['model_id'] = 'google/gemma-3n-e4b'
            print(f"\033[36mSwitched to fast mode ({context['model_id']})\033[0m")
        elif mode == 'thinking':
            context['model_id'] = 'qwen/qwen3-4b-thinking-2507'
            print(f"\033[36mSwitched to thinking mode ({context['model_id']})\033[0m")
        else:
            print("\033[31mInvalid mode. Use '/model fast' or '/model thinking'.\033[0m")
            return True

        if 'print_status' in context:
            context['print_status'](context)
        
        return True
