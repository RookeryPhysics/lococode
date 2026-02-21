import re
from lococode.actions.base import BaseTool

class EditTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "edit"
        self.description = "Jump to making edits to the current file. Usage: /edit <instruction>"
        self.pattern = r"^/edit\s+(.+)$"
        self.is_slash = True
        self.intent = "edit"
        self.arg_description = "edit instruction"

    def execute(self, match, context):
        instruction = match.group(1).strip()
        if not instruction:
            print("\033[31mError: Please provide an instruction for the /edit command.\033[0m")
            return True

        apply_edit = context.get('apply_edit')
        if not apply_edit:
            print("\033[31mError: apply_edit not found in context.\033[0m")
            return True

        # Use a preplanned intent to force a code edit
        pre_intent = {
            "intent": "code_edit",
            "args": None,
            "tags_needed": [],
            "reasoning": "Explicit /edit command used."
        }
        
        # We call apply_edit with the extracted instruction and the preplanned intent
        apply_edit(
            context['target_file'],
            instruction,
            context['model_id'],
            context['registry'],
            context,
            verbose=False,
            preplanned_intent=pre_intent
        )
        return True
