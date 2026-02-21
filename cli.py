import sys
import subprocess
import shutil

def install_package(package):
    """Installs a python package via pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

try:
    import requests
except ImportError:
    print("\033[90mInstalling missing dependency 'requests'...\033[0m")
    if install_package("requests"):
        import requests
    else:
        print("\033[31mError: Failed to install 'requests' automatically. Please run 'pip install requests' manually.\033[0m")
        sys.exit(1)

import json
import argparse
import os
import math
import time
import re
import webbrowser
import threading

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.key_binding import KeyBindings
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    print(f"\033[90mInstalling missing dependency 'prompt_toolkit' for enhanced UI...\033[0m")
    if install_package("prompt_toolkit"):
        try:
            from prompt_toolkit import prompt
            from prompt_toolkit.formatted_text import ANSI
            from prompt_toolkit.key_binding import KeyBindings
            HAS_PROMPT_TOOLKIT = True
        except ImportError:
            HAS_PROMPT_TOOLKIT = False
    else:
        HAS_PROMPT_TOOLKIT = False

# Add the parent directory to sys.path so 'lococode' can be imported as a package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lococode.registry import ToolRegistry

BASE_URL = "http://localhost:1234/v1"

def get_models():
    """Fetches a list of available models from LM Studio."""
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Error fetching models: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        return None

BRACKET_RE = re.compile(r'([()\[\]{}<>])')

def stream_response(model_id, messages, silent=False, color="\033[92m"):
    """Sends a chat completion request with streaming enabled."""
    payload = {"model": model_id, "messages": messages, "stream": True, "temperature": 0, "max_tokens": -1}
    
    try:
        response = requests.post(f"{BASE_URL}/chat/completions", headers={"Content-Type": "application/json"}, data=json.dumps(payload), stream=True)
        if response.status_code != 200: return None

        content_list = []
        is_generating = [True]
        
        class AnimState:
            last_printed_lines = 0
            wave_pos = 0.0
            wave_dir = 1
            last_time = time.time()
            content_len = -1
            display_text = ""
            printed_lines = 0
        state = AnimState()
        
        if not silent:
            print("\033[?25l", end="") # Hide cursor

        def animation_thread():
            if silent: return
            
            while is_generating[0]:
                if len(content_list) != state.content_len:
                    state.content_len = len(content_list)
                    text = "".join(content_list)
                    
                    try:
                        term_width, term_height = os.get_terminal_size()
                    except:
                        term_width, term_height = 80, 24
                    
                    t_w = max(40, term_width - 2)
                    max_lines = max(5, term_height - 5)
                    
                    full_str = "Assistant: " + text
                    
                    lines = []
                    for paragraph in full_str.split('\n'):
                        if not paragraph:
                            lines.append("")
                        else:
                            for i in range(0, len(paragraph), t_w):
                                lines.append(paragraph[i:i+t_w])
                    
                    if len(lines) > max_lines:
                        lines = lines[-max_lines:]
                        if len(lines[0]) >= 5:
                            lines[0] = "(...)" + lines[0][5:]
                        else:
                            lines[0] = "(...)"
                    
                    state.display_text = '\n'.join(lines)
                    state.printed_lines = len(lines) - 1 if lines else 0

                display_text = state.display_text
                printed_lines = state.printed_lines
                current_time = time.time()
                dt = current_time - state.last_time
                state.last_time = current_time
                wave_speed = 60.0 # Characters per second
                
                total_len = len(display_text)
                if total_len > 0:
                    trip_len = total_len + 15
                    state.wave_pos += state.wave_dir * wave_speed * dt
                    
                    if state.wave_pos >= trip_len:
                        state.wave_pos = trip_len
                        state.wave_dir = -1
                    elif state.wave_pos <= 0:
                        state.wave_pos = 0
                        state.wave_dir = 1
                    wave_pos_int = int(state.wave_pos)
                else:
                    wave_pos_int = 0
                
                # Optimized coloring: Only color the area near the wave
                colored_parts = []
                last_color = None
                
                # Define color zones
                # 0: yellow (dist < 2), 1: dark yellow (dist < 5), 2: brackets, 3: default
                for i, char in enumerate(display_text):
                    if char == '\n':
                        colored_parts.append(char)
                        last_color = None
                        continue
                    
                    dist = abs(i - wave_pos_int)
                    current_color = None
                    
                    if dist < 2:
                        current_color = "\033[93m"
                    elif dist < 5:
                        current_color = "\033[33m"
                    elif char in "()[]{}<>":
                        current_color = "\033[36m"
                    else:
                        current_color = color
                    
                    if current_color != last_color:
                        colored_parts.append(current_color)
                        last_color = current_color
                    colored_parts.append(char)
                
                colored_text = "".join(colored_parts) + "\033[0m"
                
                if state.last_printed_lines > 0:
                    sys.stdout.write(f"\033[{state.last_printed_lines}A\r")
                else:
                    sys.stdout.write("\r")
                sys.stdout.write("\033[J")
                sys.stdout.write(colored_text)
                sys.stdout.flush()
                
                state.last_printed_lines = printed_lines
                time.sleep(0.05) # Increased sleep slightly for CPU efficiency

        anim_t = None
        if not silent:
            anim_t = threading.Thread(target=animation_thread, daemon=True)
            anim_t.start()
            
        def finalize_output(is_cancelled=False):
            if not silent:
                is_generating[0] = False
                if anim_t: anim_t.join()
                
                if state.last_printed_lines > 0:
                    sys.stdout.write(f"\033[{state.last_printed_lines}A\r\033[J")
                else:
                    sys.stdout.write("\r\033[J")
                
                final_text = "Assistant: " + "".join(content_list)
                final_text = BRACKET_RE.sub(rf'\033[36m\1{color}', final_text)
                print(f"{color}{final_text}\033[0m")
            
            if is_cancelled:
                print("\n\033[1;33m[Cancelled]\033[0m")
                
            if not silent:
                print("\033[?25h", end="", flush=True) # Show cursor

        for line in response.iter_lines():
            # Check for Escape key to cancel generation
            if msvcrt and msvcrt.kbhit():
                if msvcrt.getch() == b'\x1b':
                    finalize_output(is_cancelled=True)
                    response.close()
                    while msvcrt.kbhit():  # Clear remaining key presses
                        msvcrt.getch()
                    return None

            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]": break
                    try:
                        content = json.loads(data_str)['choices'][0].get('delta', {}).get('content', "")
                        content_list.append(content)
                    except: continue
        
        finalize_output(is_cancelled=False)
        return "".join(content_list)
    except: 
        print("\033[?25h", end="", flush=True)
        return None

def classify_intent(model_id, instruction, registry):
    """Planning step: classifies the user's intent, determines tags, and extracts arguments in one pass."""
    tag_tools = [t for t in registry.tools if not t.is_slash]
    tag_list = ", ".join([f"<tool:{t.name}> ({t.description})" for t in tag_tools])

    intent_descriptions = {
        "code_edit": "modify or write code in the current open file",
        "general_question": "answer a question without modifying any files or taking any other actions"
    }

    for t in registry.tools:
        if t.is_slash and t.intent:
            arg_desc = f" (requires arg: {t.arg_description})" if t.arg_description else ""
            # Some tool descriptions include "/command" instructions; strip or let it pass, the LLM will understand
            intent_descriptions[t.intent] = f"{t.description}{arg_desc}"

    intent_list_str = "\n".join([f"  - \"{intent}\": {desc}" for intent, desc in intent_descriptions.items()])
    valid_intents_str = ", ".join([f'"{intent}"' for intent in intent_descriptions.keys()])

    classify_prompt = (
        "You are a planning assistant. Analyze the user's instruction and determine the correct action to take.\n\n"
        "Available actions (intents):\n"
        f"{intent_list_str}\n\n"
        "Rules:\n"
        f"1. You MUST choose exactly one intent from this list: [{valid_intents_str}]\n"
        "2. Determine 'args': the primary argument required by the chosen intent (e.g. filename, search query, mode), or null if none required. For 'pair' or 'sequence', the arg is the full instruction.\n"
        "3. Determine 'tags_needed': a list of tool tag names the model should use to fulfill the instruction.\n"
        "4. Provide 'reasoning': a brief one-sentence explanation for your choice.\n"
        "5. If the instruction contains EXACTLY TWO distinct steps (e.g. 'create a file then edit it'), you MUST choose the 'pair' intent.\n"
        "6. If the instruction contains THREE OR MORE distinct steps, you MUST choose the 'sequence' intent.\n\n"
        f"Available tool tags for 'tags_needed': {tag_list}\n\n"
        "Respond with ONLY a JSON object. Examples:\n"
        '{"intent": "code_edit", "args": null, "tags_needed": [], "reasoning": "User wants to modify the current file."}\n'
        '{"intent": "create_file", "args": "app.py", "tags_needed": ["create_file", "edit_file"], "reasoning": "User wants a new app.py."}\n'
        '{"intent": "file_switch", "args": "main.py", "tags_needed": [], "reasoning": "User wants to start editing main.py instead."}\n'
        '{"intent": "pair", "args": "Create a new file called app.js and make it print hello world", "tags_needed": [], "reasoning": "Instruction involves exactly 2 distinct steps."}\n'
        '{"intent": "sequence", "args": "Create app.py, add a route, and then run it", "tags_needed": [], "reasoning": "Instruction involves 3 or more distinct steps."}\n'
        '{"intent": "ls", "args": null, "tags_needed": [], "reasoning": "User wants to list files in the directory."}'
    )

    messages = [
        {"role": "system", "content": classify_prompt},
        {"role": "user", "content": instruction}
    ]

    result = stream_response(model_id, messages, silent=True)
    if not result:
        return None

    # Strip <think> blocks if present
    result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
    # Try to extract JSON from the response
    json_match = re.search(r'\{.*\}', result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None

def apply_edit(target_file, instruction, model_id, registry, context, verbose=False, preplanned_intent=None):
    """Reads the target file, sends instruction to model using SEARCH/REPLACE blocks, and updates the file."""
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return False

    tool_prompt = registry.get_system_prompt_segment()
    
    if preplanned_intent:
        intent_info = preplanned_intent
        is_preplanned = True
    else:
        print(f"\033[90mPlanning...\033[0m", end="", flush=True)
        intent_info = classify_intent('google/gemma-3n-e4b', instruction, registry)
        is_preplanned = False
        
    if intent_info is None:
        return False
    
    intent_context = ""
    if intent_info:
        intent = intent_info.get("intent", "code_edit")
        tags_needed = intent_info.get("tags_needed", [])
        reasoning = intent_info.get("reasoning", "")
        arg = intent_info.get("args")
        
        if is_preplanned:
            print(f"\033[90mPlan: {intent}", end="")
        else:
            print(f"\r\033[90mPlan: {intent}", end="")
            
        if tags_needed:
            print(f" | Tags: {', '.join(tags_needed)}", end="")
        print(f"\033[0m")
        
        plan_str = f"Plan: {intent}" + (f" | Tags: {', '.join(tags_needed)}" if tags_needed else "")


        # ── Handle tool intents directly (Unified Planner) ──
        matched_tool = registry.find_tool_by_intent(intent)
        if matched_tool:
            if matched_tool.arg_description:
                if not arg:
                    if matched_tool.name == "create_file":
                        print(f"\033[33mNo filename specified, falling back to code editing.\033[0m")
                        matched_tool = None
                        intent = "code_edit"
                    else:
                        print(f"\033[31mCould not extract {matched_tool.arg_description} from instruction.\033[0m")
                        return False
                
                if matched_tool:
                    cmd_match = re.search(r'(/[a-z\d_]+)', matched_tool.pattern)
                    if cmd_match:
                        base_cmd = cmd_match.group(1)
                        fake_input = f"{base_cmd} {arg}" if arg else base_cmd
                        fake_match = re.search(matched_tool.pattern, fake_input, re.IGNORECASE | re.DOTALL)
                        if fake_match:
                            matched_tool.execute(fake_match, context)
                            return True
                    print(f"\033[31mFailed to build command for {matched_tool.name}.\033[0m")
                    return False
            else:
                fake_match = re.match(matched_tool.pattern, matched_tool.pattern, re.IGNORECASE | re.DOTALL)
                matched_tool.execute(fake_match, context)
                return True

        intent_context = f"\n\nPLAN: Intent={intent}."
        if tags_needed:
            intent_context += f" You MUST use these tool tags: {', '.join(['<tool:' + t + '>' for t in tags_needed])}."
        if reasoning:
            intent_context += f" ({reasoning})"
                
    else:
        print(f"\r\033[90mPlan: default (code_edit)\033[0m")

    research_section = ""
    search_results = context.get("search_results", [])
    if search_results:
        research_section = "\n\nRESEARCH:\n" + "\n".join(search_results)
        context["search_results"] = []

    # SEARCH/REPLACE System Prompt
    diff_system = (
        f"You are an expert developer updating {target_file}. "
        "To make changes, use SEARCH/REPLACE blocks. This is faster and uses fewer tokens.\n\n"
        "Format:\n"
        "<<<< SEARCH\n[exact code to find]\n====\n[replacement code]\n>>>> REPLACE\n\n"
        "Rules:\n"
        "1. SEARCH block must match the existing file content EXACTLY (including whitespace).\n"
        "2. Only provide blocks for parts you are changing.\n"
        "3. Do not output the whole file unless you are replacing it entirely.\n"
        "4. No conversational filler. No markdown unless requested."
    )

    prompt = f"INST:\n{instruction}{research_section}\n\nCTX:\n{current_content}"
    
    messages = [
        {"role": "system", "content": f"{diff_system} {tool_prompt}{intent_context}"},
        {"role": "user", "content": prompt}
    ]

    print(f"\033[92mProcessing...\033[0m")
    updated_content = stream_response(model_id, messages, color="\033[92m")

    if updated_content:
        updated_content = re.sub(r"<think>.*?</think>", "", updated_content, flags=re.DOTALL)

        updated_content = registry.process_model_output(updated_content, context)

        # Apply SEARCH/REPLACE blocks
        blocks = re.findall(r"<<<< SEARCH\n(.*?)\n====\n(.*?)(?:\n>>>> REPLACE|$)", updated_content, re.DOTALL | re.MULTILINE)
        
        if blocks:
            new_content = current_content
            applied_count = 0
            for search, replace in blocks:
                if search in new_content:
                    new_content = new_content.replace(search, replace, 1)
                    applied_count += 1
                else:
                    print(f"\033[31mError: Search block not found in {target_file}. Check indentation/content.\033[0m")
            
            if applied_count > 0:
                with open(context['target_file'], 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"\033[32mApplied {applied_count} change(s) to {context['target_file']}.\033[0m")
                return True
        else:
            if "<<<< SEARCH" in updated_content:
                print(f"\033[31mError: Model attempted to use SEARCH/REPLACE blocks but formatting was invalid.\033[0m")
                return False
                
            # Fallback if no blocks found but model output content (maybe for general questions or tiny files)
            cleaned = re.sub(r"```[a-z]*\n?", "", updated_content).replace("```", "").strip()
            if cleaned and intent == "code_edit":
                # If model ignored blocks but wrote code, we can overwrite if requested or just warn
                # For safety/pro-engineer status, let's allow overwrite if it looks like a full file and blocks were missing
                if len(cleaned) > 10:
                    with open(context['target_file'], 'w', encoding='utf-8') as f:
                        f.write(cleaned)
                    print(f"\033[32mUpdated {context['target_file']} (full file fallback).\033[0m")
                    return True
            elif intent == "general_question":
                return True # Already printed by stream_response

    return False

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_cube_frame(rot_x, rot_y, width, height):
    vertices = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]]
    edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
    
    scale_y = height / 4.0
    scale_x = scale_y * 2.0
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    def is_inside(x, y, p1, p2, p3):
        d1 = (x - p2[0]) * (p1[1] - p2[1]) - (p1[0] - p2[0]) * (y - p2[1])
        d2 = (x - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (y - p3[1])
        d3 = (x - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (y - p1[1])
        return not (((d1 < 0) or (d2 < 0) or (d3 < 0)) and ((d1 > 0) or (d2 > 0) or (d3 > 0)))
    
    def draw_cube(verts, color_code):
        proj_verts = []
        for x, y, z in verts:
            proj_verts.append((int(x * scale_x + width / 2), int(y * scale_y + height / 2)))
        
        for e in edges:
            p1, p2 = proj_verts[e[0]], proj_verts[e[1]]
            x0, y0 = p1
            x1, y1 = p2
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            while True:
                if 0 <= x0 < width and 0 <= y0 < height:
                    grid[y0][x0] = f'\033[{color_code}m#\033[0m'
                if x0 == x1 and y0 == y1: break
                e2 = 2 * err
                if e2 > -dy: err -= dy; x0 += sx
                if e2 < dx: err += dx; y0 += sy

    def fill_cube(verts, color_code):
        p_v = []
        for x, y, z in verts:
            p_v.append((x * scale_x + width / 2, y * scale_y + height / 2))
        
        faces = [(4, 5, 6, 7), (0, 3, 2, 1), (0, 4, 7, 3), (1, 2, 6, 5), (0, 1, 5, 4), (3, 7, 6, 2)]
        chars = "01$#@&%*+=-:."
        
        for f in faces:
            p = [p_v[i] for i in f]
            # Backface culling
            if (p[1][0]-p[0][0])*(p[2][1]-p[0][1]) - (p[1][1]-p[0][1])*(p[2][0]-p[0][0]) <= 0:
                continue
            
            min_x = max(0, int(min(v[0] for v in p)))
            max_x = min(width - 1, int(max(v[0] for v in p)))
            min_y = max(0, int(min(v[1] for v in p)))
            max_y = min(height - 1, int(max(v[1] for v in p)))
            
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    if is_inside(x, y, p[0], p[1], p[2]) or is_inside(x, y, p[0], p[2], p[3]):
                        grid[y][x] = f'\033[{color_code}m-\033[0m'

    # Big Cube
    big_verts = []
    cos_rx, sin_rx = math.cos(rot_x), math.sin(rot_x)
    cos_ry, sin_ry = math.cos(rot_y), math.sin(rot_y)
    
    for v in vertices:
        x, y, z = v
        # Rotate X
        y2 = y * cos_rx - z * sin_rx
        z2 = y * sin_rx + z * cos_rx
        y, z = y2, z2
        # Rotate Y
        x2 = x * cos_ry - z * sin_ry
        z2 = x * sin_ry + z * cos_ry
        x, z = x2, z2
        big_verts.append((x, y, z))
        
    # Orbiting cubes
    cubes = []
    # (orbit_angle_offset, orbit_y_phase, color_code)
    orbit_configs = [
        (0, 0, 33),          # Yellow
        (math.pi * 2/3, 1, 32), # Green
        (math.pi * 4/3, 2, 35)  # Magenta
    ]

    for offset, phase, color in orbit_configs:
        small_verts = []
        orbit_angle = rot_y * 1.5 + offset
        orbit_radius = 4.0
        orbit_x = math.cos(orbit_angle) * orbit_radius
        orbit_z = math.sin(orbit_angle) * orbit_radius
        orbit_y = math.sin(rot_x * 2 + phase) * 0.8
        
        s_rot_x = (rot_y + offset) * 2
        s_rot_y = (rot_x + phase) * 3
        cos_srx, sin_srx = math.cos(s_rot_x), math.sin(s_rot_x)
        cos_sry, sin_sry = math.cos(s_rot_y), math.sin(s_rot_y)

        for v in vertices:
            x, y, z = v[0]*0.2, v[1]*0.2, v[2]*0.2
            # Spin
            y2 = y * cos_srx - z * sin_srx
            z2 = y * sin_srx + z * cos_srx
            y, z = y2, z2
            x2 = x * cos_sry - z * sin_sry
            z2 = x * sin_sry + z * cos_sry
            x, z = x2, z2
            # Translate
            x += orbit_x
            y += orbit_y
            z += orbit_z
            small_verts.append((x, y, z))
        
        avg_z = sum(v[2] for v in small_verts) / len(small_verts)
        cubes.append({'verts': small_verts, 'color': color, 'z': avg_z, 'type': 'small'})

    cubes.append({'verts': big_verts, 'color': 36, 'z': 0, 'type': 'big'})
    
    # Sort all cubes by depth
    cubes.sort(key=lambda c: c['z'])
    
    for c in cubes:
        if c['type'] == 'big':
            fill_cube(c['verts'], 97)
            draw_cube(c['verts'], 36)
        else:
            draw_cube(c['verts'], c['color'])

    return ["".join(row) for row in grid]

def get_banner_colored():
    """Builds and returns the colored 'LOCOCODE' banner lines."""
    letters = {
        'L': [" █     ", " █     ", " █     ", " █     ", " █████ "],
        'O': ["  ███  ", " █   █ ", " █   █ ", " █   █ ", "  ███  "],
        'C': ["  ████ ", " █     ", " █     ", " █     ", "  ████ "],
        'D': [" ████  ", " █   █ ", " █   █ ", " █   █ ", " ████  "],
        'E': [" █████ ", " █     ", " ████  ", " █     ", " █████ "]
    }
    
    word = "LOCOCODE"
    base_rows = ["", "", "", "", ""]
    gradient = ["\033[38;5;129m", "\033[38;5;128m", "\033[38;5;127m", "\033[38;5;93m", "\033[38;5;92m", 
                "\033[38;5;91m", "\033[38;5;57m", "\033[38;5;56m", "\033[38;5;55m", "\033[38;5;21m",
                "\033[38;5;27m", "\033[38;5;33m", "\033[38;5;39m", "\033[38;5;45m", "\033[38;5;51m",
                "\033[38;5;50m", "\033[38;5;49m", "\033[38;5;48m", "\033[38;5;47m", "\033[38;5;46m"]

    for char in word:
        char_pattern = letters.get(char, letters['E'])
        for i in range(5): base_rows[i] += char_pattern[i]

    banner_colored = ["", "", "", "", ""]
    for i, row in enumerate(base_rows):
        colored_row = ""
        row_len = len(row)
        for j, char in enumerate(row):
            if char == '█':
                color_idx = int((j / row_len) * (len(gradient) - 1))
                colored_row += f"{gradient[color_idx]}█\033[0m"
            else: colored_row += char
        banner_colored[i] = colored_row
        
    return banner_colored

def print_banner():
    """Prints the colored 'LOCOCODE' banner."""
    banner = get_banner_colored()
    for line in banner:
        print(line)


def main():
    clear_console()
    banner_colored = get_banner_colored()
    
    print("\033[?25l", end="") # Hide cursor
    frame = 0
    try:
        while True:
            try:
                term_width, term_height = os.get_terminal_size()
            except:
                term_width, term_height = 80, 24
                
            t_w = max(40, term_width - 1)
            t_h = max(15, term_height - 1)

            rot = frame * 0.05
            cube_frame = get_cube_frame(rot, rot * 1.8, t_w, t_h)
            
            out = "\033[1;1H"
            for i in range(t_h):
                out += cube_frame[i] + "\033[K"
                if i < t_h - 1:
                    out += "\n"
            
            for i in range(5):
                out += f"\033[{i+1};1H" + banner_colored[i]
                
            prompt_text = "Press any key to begin."
            pad_len = max(0, (t_w - len(prompt_text)) // 2)
            out += f"\033[{t_h};1H" + " " * pad_len + prompt_text + "\033[K"
            
            print(out, end="", flush=True)
            
            if msvcrt and msvcrt.kbhit():
                while msvcrt.kbhit():
                    msvcrt.getch()
                clear_console()
                print_banner()
                break
                
            time.sleep(0.04)
            frame += 1
    finally:
        print("\033[?25h", end="", flush=True)

    print("\n\033[1;34mConnecting to LM Studio and loading models...\033[0m")
    
    models = get_models()
    if models is None:
        print("\033[90mStarting LM Studio server...\033[0m")
        subprocess.Popen("lms server start", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for _ in range(20):
            models = get_models()
            if models is not None:
                print("\033[90mServer is up!\033[0m")
                break
            time.sleep(1)
            
    if models is None:
        print("\033[31mError: Could not start or connect to LM Studio server.\033[0m")
        sys.exit(1)

    loaded_model_ids = [m.get('id') for m in models]
    required_models = ["google/gemma-3n-e4b"]
    
    for req_model in required_models:
        if not any(req_model in m_id for m_id in loaded_model_ids):
            print(f"\033[90mLoading model {req_model}...\033[0m")
            subprocess.run(f"lms load {req_model} --yes", shell=True)
            
    models = get_models()
    if not models:
        print("No models found. Please load a model in LM Studio.")
        return

    # Default to fast mode model
    model_id = 'google/gemma-3n-e4b'
    registry = ToolRegistry()
    
    def print_status(ctx):
        print(f"\n\033[1;34mEditing Mode: {ctx['target_file']}\033[0m")
        slash_cmds = [t.pattern for t in ctx['registry'].tools if t.is_slash]
        # print(f"\033[90mCommands: {', '.join(slash_cmds)}\033[0m")

    context = {
        'target_file': 'index.html',
        'model_id': model_id,
        'stream_response': stream_response,
        'apply_edit': apply_edit,
        'registry': registry,
        'print_banner': print_banner,
        'print_status': print_status
    }

    if not os.path.exists(context['target_file']):
        with open(context['target_file'], 'w', encoding='utf-8') as f:
            f.write("<html><body>Hello World</body></html>")
        print(f"Created initial {context['target_file']}")

    context['print_status'](context)
    print("Type your instructions and press Enter. Type '/help' for a list of commands or '/exit' to quit.")

    while True:
        try:
            if HAS_PROMPT_TOOLKIT:
                bindings = KeyBindings()
                @bindings.add('escape')
                def _(event):
                    event.app.exit(result=None)
                instruction = prompt(ANSI(f"\n\033[1;37m[{context['target_file']}] Edit Instruction: \033[0m"), key_bindings=bindings)
                if instruction is None:
                    continue
            else:
                instruction = input(f"\n\033[1;37m[{context['target_file']}] Edit Instruction: \033[0m")
                
            if not instruction.strip(): continue
            


            if instruction.lower() in ['/exit', '/quit']:
                print("\n\033[90mClosing models, server, and LM Studio...\033[0m")
                subprocess.run("lms unload --all", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run("lms server stop", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.name == 'nt':
                    subprocess.run("taskkill /IM \"LM Studio.exe\" /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run("pkill -f \"LM Studio\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            
            if instruction.strip().lower() == '/help':
                print(registry.get_help_text())
                continue


            # Run via registry (Slash commands)
            if registry.run_slash_command(instruction, context):
                continue

            # Apply normal edit
            apply_edit(context['target_file'], instruction, context['model_id'], registry, context, verbose=False)
        
        except KeyboardInterrupt: break
        except Exception as e: print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
