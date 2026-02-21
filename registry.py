import os
import importlib.util
import re
from lococode.actions.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self.tools = []
        self.load_actions()

    def load_actions(self):
        actions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'actions')
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
        
        # Define categories and map tools to them
        categories = {
            "File Operations": ["file_switch", "create_file", "delete_file", "backup", "ls"],
            "Search & Research": ["open_url", "open_current_html"],
            "Execution": ["write_run"],
            "System": ["model", "loop", "sequence", "pair", "clear_console", "save_session"]
        }
        
        # Reverse mapping for quick lookup
        tool_to_cat = {}
        for cat, tool_names in categories.items():
            for name in tool_names:
                tool_to_cat[name] = cat

        help_text = "\n\033[1;35m--- LOCOCODE COMMANDS ---\033[0m\n"
        
        # Group tools by category
        grouped = {}
        for tool in slash_tools:
            cat = tool_to_cat.get(tool.name, "Other")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(tool)
            
        # Add hardcoded system commands to the System category
        system_cat = "System"
        
        for cat in sorted(grouped.keys()):
            if cat == "Other" and not grouped[cat]: continue
            
            help_text += f"\n\033[1;34m{cat}:\033[0m\n"
            for tool in sorted(grouped[cat], key=lambda x: x.pattern):
                # Clean up the regex pattern for display
                clean_name = tool.pattern
                clean_name = re.sub(r'[\^\$]', '', clean_name) # Remove start/end anchors
                clean_name = re.sub(r'\\s\+\(\.\+\)', ' <arg>', clean_name)
                clean_name = re.sub(r'\\s\*\(\.\*\)', ' [arg]', clean_name)
                clean_name = re.sub(r'\\s\+', ' ', clean_name)
                clean_name = re.sub(r'\\b', '', clean_name)
                # Hide technical-looking optional groups
                clean_name = re.sub(r'\(\?:\s+<arg>\)\?', '', clean_name)
                # Handle special case for /model which has a complex regex
                if tool.name == "model":
                    clean_name = "/model [mode]"
                
                clean_name = clean_name.strip()
                help_text += f"  \033[92m{clean_name:<18}\033[0m - {tool.description}\n"
            
            # Add hardcoded commands to the System section
            if cat == "System":
                help_text += f"  \033[92m{'/help':<18}\033[0m - Show this help message.\n"
                help_text += f"  \033[92m{'/exit':<18}\033[0m - Close models/server and exit.\n"
                help_text += f"  \033[92m{'/quit':<18}\033[0m - Alias for /exit.\n"
        
        return help_text

    def run_slash_command(self, user_input, context):
        cleaned_input = user_input.strip()
        if not cleaned_input.startswith('/'):
            return False
            
        # Get the command part (e.g., /undo from "/undo file.txt")
        cmd_part = cleaned_input.split()[0].lower()
        
        for tool in self.tools:
            if tool.is_slash:
                # Check if the pattern is a simple slash command or a regex
                pattern = tool.pattern
                if pattern.startswith('/') or pattern.startswith('^/'):
                    # Match exact command or regex
                    match = re.match(pattern, cleaned_input, re.IGNORECASE | re.DOTALL)
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
