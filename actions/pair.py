import json
import re
from lococode.actions.base import BaseTool

class PairTool(BaseTool):
    """Slash command: /pair <prompt> — executes a sequence of 2 actions."""

    def __init__(self):
        super().__init__()
        self.name = "pair"
        self.description = "Execute a sequence of 2 actions based on the prompt. Usage: /pair <prompt>"
        self.pattern = r"^/pair\s+(.+)$"
        self.is_slash = True
        self.intent = "pair"
        self.arg_description = "The prompt to generate the 2-step sequence from"

    def execute(self, match, context):
        instruction = match.group(1).strip()
        if not instruction:
            print("\033[31mError: Please provide a prompt for the pair sequence.\033[0m")
            return True

        if 'registry' not in context or 'stream_response' not in context or 'apply_edit' not in context:
            print("\033[31mError: Missing dependencies in context.\033[0m")
            return True

        registry = context['registry']
        model_id = context['model_id']
        stream_response = context['stream_response']
        apply_edit = context['apply_edit']
        
        intent_descriptions = {
            "code_edit": "modify or write code in the current open file",
            "general_question": "answer a question without modifying any files or taking any other actions"
        }

        for t in registry.tools:
            if t.is_slash and t.intent and t.intent != "pair":
                arg_desc = f" (requires arg: {t.arg_description})" if t.arg_description else ""
                intent_descriptions[t.intent] = f"{t.description}{arg_desc}"

        intent_list_str = "\n".join([f"  - \"{intent}\": {desc}" for intent, desc in intent_descriptions.items()])
        valid_intents_str = ", ".join([f'"{intent}"' for intent in intent_descriptions.keys()])

        prompt = (
            "You are a planning assistant. Analyze the user's instruction and break it down into exactly 2 sequential actions.\n\n"
            "Available actions (intents):\n"
            f"{intent_list_str}\n\n"
            "Rules:\n"
            f"1. You MUST choose exactly 2 intents from this list: [{valid_intents_str}]\n"
            "2. For each action, determine 'args': the primary argument required by the chosen intent (e.g. filename for create_file, the prompt/instruction to run for code_edit, the url for open_url, etc.), or null if none required.\n"
            "3. Provide 'reasoning': a brief explanation for each choice.\n\n"
            "Respond with ONLY a JSON array containing exactly 2 objects. Example format:\n"
            "[\n"
            '  {"intent": "create_file", "args": "app.py", "reasoning": "Step 1: create the main file."},\n'
            '  {"intent": "code_edit", "args": "write a fast API server", "reasoning": "Step 2: implement the server."}\n'
            "]"
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": instruction}
        ]

        print("\033[90mPlanning pair sequence...\033[0m", end="", flush=True)
        result = stream_response(model_id, messages, silent=True)
        if not result:
            print("\n\033[31mFailed to get a response from the model.\033[0m")
            return True
            
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        
        plan = None
        if json_match:
            try:
                plan = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
                
        if not plan or not isinstance(plan, list) or len(plan) != 2:
            print(f"\n\033[31mFailed to parse exactly 2 actions from the plan. Model returned:\n{result}\033[0m")
            return True

        print(f"\r\033[90mPair Sequence Plan:\033[0m")
        for i, step in enumerate(plan):
            print(f"\033[90m  {i+1}. {step.get('intent')} - {step.get('reasoning')}\033[0m")

        for i, step in enumerate(plan):
            intent = step.get('intent')
            args = step.get('args')
            
            print(f"\n\033[94m=== PAIR SEQUENCE STEP {i+1}/2: {intent} ===\033[0m")
            
            matched_tool = registry.find_tool_by_intent(intent)
            if matched_tool:
                if matched_tool.arg_description and not args:
                    if matched_tool.name == "create_file":
                        intent = "code_edit"
                        matched_tool = None
                    else:
                        print(f"\033[31mSkipping step {i+1}: missing args for {intent}.\033[0m")
                        continue
                
                if matched_tool:
                    cmd_match = re.search(r'(/[a-z\d_]+)', matched_tool.pattern)
                    if cmd_match:
                        base_cmd = cmd_match.group(1)
                        fake_input = f"{base_cmd} {args}" if args else base_cmd
                        fake_match = re.search(matched_tool.pattern, fake_input, re.IGNORECASE | re.DOTALL)
                        if fake_match:
                            try:
                                matched_tool.execute(fake_match, context)
                            except Exception as e:
                                print(f"\033[31mError executing {intent}: {e}\033[0m")
                            continue
                    print(f"\033[31mFailed to build command for {matched_tool.name}.\033[0m")
                    continue
            
            if intent in ["code_edit", "general_question"]:
                step_instruction = args if args else step.get('reasoning', "code edit")
                try:
                    pre_intent = {"intent": intent, "args": step_instruction, "tags_needed": [], "reasoning": step.get('reasoning', '')}
                    apply_edit(context['target_file'], step_instruction, model_id, registry, context, verbose=True, preplanned_intent=pre_intent)
                except Exception as e:
                    print(f"\033[31mError applying edit: {e}\033[0m")
            else:
                print(f"\033[31mUnknown intent {intent}\033[0m")
        
        return True
