import os
import importlib.util
import re
from lococode.actions.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self.tools = []
        self.load_actions()

    def load_actions(self):
        actions_dir = os.path.join(os.path.dirname(__file__), 'actions')
        if not os.path.exists(actions_dir):
            return
            
        for filename in os.listdir(actions_dir):
            if filename.endswith('.py') and filename != 'base.py' and filename != '__init__.py':
                module_name = f"lococode.actions.{filename[:-3]}"
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(actions_dir, filename))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                            self.tools.append(attr())

    def get_system_prompt_segment(self):
        tag_tools = [t for t in self.tools if not t.is_slash]
        if not tag_tools:
            return ""
        
        prompt = "\nAvailable Tools (Use these tags in your output to trigger actions):\n"
        for tool in tag_tools:
            prompt += f"  <tool:{tool.name}>args</tool:{tool.name}> - {tool.description}\n"
        return prompt

    def get_help_text(self):
        slash_tools = [t for t in self.tools if t.is_slash]
        help_text = "\nAvailable Commands:\n"
        for tool in slash_tools:
            # Clean up the regex pattern for display
            clean_name = tool.pattern
            clean_name = re.sub(r'[\^\$]', '', clean_name) # Remove start/end anchors
            clean_name = re.sub(r'\\s\+\(\.\+\)', ' <arg>', clean_name)
            clean_name = re.sub(r'\\s\*\(\.\*\)', ' [arg]', clean_name)
            # Hide technical-looking optional groups
            clean_name = re.sub(r'\(\?: <arg>\)\?', '', clean_name)
            clean_name = clean_name.strip()
            
            help_text += f"  {clean_name:<18} - {tool.description}\n"
        
        help_text += f"  {'/help':<18} - Show this help message.\n"
        help_text += f"  {'/exit / /quit':<18} - Exit the CLI.\n"
        return help_text

    def run_slash_command(self, user_input, context):
        for tool in self.tools:
            if tool.is_slash:
                match = re.match(tool.pattern, user_input.strip(), re.IGNORECASE)
                if match:
                    return tool.execute(match, context)
        return False

    def find_tool_by_intent(self, intent):
        """Find a slash tool that handles the given planner intent."""
        for tool in self.tools:
            if tool.is_slash and tool.intent == intent:
                return tool
        return None

    def process_model_output(self, output, context):
        modified_output = output
        for tool in self.tools:
            if not tool.is_slash:
                tag_pattern = rf"<tool:{tool.name}>(.*?)</tool:{tool.name}>"
                matches = list(re.finditer(tag_pattern, modified_output, re.DOTALL))
                for match in reversed(matches):
                    tool.execute(match, context)
                    modified_output = modified_output[:match.start()] + modified_output[match.end():]

        # Strip any remaining <tool:...> tags the LLM produced that don't match a registered tool
        modified_output = re.sub(r"</?tool:[^>]*>", "", modified_output)
        return modified_output
