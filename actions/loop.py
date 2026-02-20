import re
from lococode.actions.base import BaseTool

class LoopTool(BaseTool):
    """Slash command: /loop [count] <specs> — iterates multiple times to refine code."""

    def __init__(self):
        super().__init__()
        self.name = "loop_edit"
        self.description = "Iterate on code multiple times (default 3). Usage: /loop [count] <specs>"
        self.pattern = r"/loop\s+(.+)"
        self.is_slash = True
        self.intent = "loop_edit"
        self.arg_description = "iteration count (optional) and specifications"

    def execute(self, match, context):
        full_args = match.group(1).strip()
        
        # Default defaults
        count = 3
        specifications = full_args

        # Check if the first word is a number
        # Matches "5 some specs" or just "5" (though specs are required below)
        count_match = re.match(r'^(\d+)\s+(.+)$', full_args)
        if count_match:
            try:
                count = int(count_match.group(1))
                specifications = count_match.group(2).strip()
            except ValueError:
                pass # Fallback to default
        
        if not specifications:
            print("\033[31mError: Please provide specifications for the loop.\033[0m")
            return True

        if 'apply_edit' not in context or 'registry' not in context:
             print("\033[31mError: Missing dependencies (apply_edit/registry) in context.\033[0m")
             return True

        apply_edit = context['apply_edit']
        registry = context['registry']
        model_id = context['model_id']
        target_file = context['target_file']

        for i in range(count):
            print(f"\033[92m\n--- Loop Iteration {i+1}/{count} ---\033[0m")
            imp_inst = specifications if i == 0 else f"Iterate on and improve the code further: {specifications}"
            
            # call apply_edit with verbose=True to show progress
            success = apply_edit(
                target_file, 
                imp_inst, 
                model_id, 
                registry, 
                context, 
                verbose=True
            )
            
            if not success:
                break
            
            # If HTML file, open in browser using the browser_open tool
            if target_file.lower().endswith('.html'):
                browser_tool = next((t for t in registry.tools if t.name == 'browser_open'), None)
                if browser_tool:
                    print(f"\033[90m(Auto-opening {target_file} in browser...)\033[0m")
                    browser_tool.execute(None, context)
        
        return True
