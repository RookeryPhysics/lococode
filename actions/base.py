import re

class BaseTool:
    """Base class for all tools (slash commands and model tags)."""
    def __init__(self):
        self.name = ""
        self.description = ""
        self.pattern = "" # Regex pattern to match
        self.is_slash = False # True for /commands, False for <tags>
        self.intent = None  # Planner intent this tool handles (e.g. "create_file", "file_switch")
        self.arg_description = None  # What argument the LLM should extract (e.g. "search query", "filename"), None if no args needed

    def execute(self, match, context):
        """
        Executes the tool logic.
        match: The re.Match object.
        context: A dictionary containing state (target_file, model_id, etc.)
        """
        raise NotImplementedError("Tools must implement execute()")

    def get_prompt_description(self):
        """Returns the description used in the system prompt."""
        if self.is_slash:
            return f"  {self.pattern} - {self.description}"
        return f"  <{self.name}>args</{self.name}> - {self.description}"
