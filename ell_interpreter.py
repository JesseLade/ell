import tkinter as tk
import re
import time
import pygame
import sys, os
from tkinter.scrolledtext import ScrolledText

ELL_MODULES_PATH = os.path.expanduser("~/.ell_modules")
if ELL_MODULES_PATH not in sys.path:
    sys.path.insert(0, ELL_MODULES_PATH)

def import_invite(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        print(f"❌ Could not invite {module_name}")
        return None





pygame.mixer.init()
print("Pygame mixer initialized:", pygame.mixer.get_init())

# Context for storing variables and functions
context = {}
functions = {}
gui_elements = []

# Dynamic audio registries
audio_loaders = {}  # Stores all audio loaders (sound and music)
audios = {}         # Stores all loaded audio objects (sound effects and music)

html_blocks = []



def load_return_plugins():
    if "returnHandler" in context:
        handler = context["returnHandler"]
        print(f"🔌 Loaded return handler: {handler}")
        # You can add more plugin support here if needed

def load_ell_file(path):
    try:
        with open(path, 'r') as f:
            content = f.readlines()
        run_ell_lines(content)
    except FileNotFoundError:
        print(f"❌ ELL file not found: {path}")
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")

def resolve_vars(expr):
    if expr in context:
        return context[expr]
    return expr

def eval_concat_expr(expr):
    parts = [p.strip() for p in expr.split('+')]
    result = ''
    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            result += part[1:-1]  # remove quotes
        elif part in context:
            result += str(context[part])
        else:
            result += part
    return result

def run_ell_lines(lines):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "returnHandler" in context:
            load_return_plugins()

        if not line or line.startswith("--"):
            i += 1
            continue

        if line.startswith("///"):
            while i < len(lines) and not lines[i].strip().endswith("///"):
                i += 1
            i += 1
            continue

        # Function definition
        if line.startswith("the function of"):
            match = re.match(r'the function of (\w+)\((.*?)\) \{', line)
            if match:
                fname = match.group(1)
                params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                body = []
                i += 1
                while i < len(lines) and lines[i].strip() != '}':
                    body.append(lines[i].strip())
                    i += 1
                functions[fname] = {"params": params, "body": body}
            i += 1
            continue

        # Function call
        elif line.startswith("function ="):
            match = re.match(r'function = "(\w+)\((.*?)\)"', line)
            if match:
                fname = match.group(1)
                args = [resolve_vars(arg.strip()) for arg in match.group(2).split(',')]
                if fname in functions:
                    local_context = dict(zip(functions[fname]["params"], args))
                    original_context = context.copy()
                    context.update(local_context)
                    run_ell_lines(functions[fname]["body"])
                    context.clear()
                    context.update(original_context)
                else:
                    print(f"❌ Function '{fname}' not defined.")
            i += 1
            continue
                # invite "filename"
        elif re.match(r'invite\s+"(.*?)"', line):
            filename = re.match(r'invite\s+"(.*?)"', line).group(1)
            if filename.endswith(".ell"):
                load_ell_file(filename)
            else:
                # support Python-based .py modules (e.g., dubem.py)
                try:
                    __import__(filename)
                except Exception as e:
                    print(f"❌ Failed to import module '{filename}': {e}")
            i += 1
            continue
                # keep var as alias
        elif re.match(r'keep\s+(\w+)\s+as\s+(\w+)', line):
            var, alias = re.match(r'keep\s+(\w+)\s+as\s+(\w+)', line).groups()
            context[alias] = context.get(var, None)
            i += 1
            continue


        # party "file1", "module1"
        elif re.match(r'party\s+(.*)', line):
            items = [x.strip().strip('"') for x in re.match(r'party\s+(.*)', line).group(1).split(',')]
            for item in items:
                if item.endswith(".ell"):
                    load_ell_file(item)
                else:
                    try:
                        __import__(item)
                    except Exception as e:
                        print(f"❌ Failed to import module '{item}': {e}")
            i += 1
            continue

        # Input prompt
        elif re.match(r'(\w+) = inputprompt\("(.*?)"\)', line):
            var, prompt = re.match(r'(\w+) = inputprompt\("(.*?)"\)', line).groups()
            context[var] = input(f"{prompt} ")
            i += 1
            continue

        # Console.typeline
        elif re.match(r'console\.typeline\((.*?)\)', line):
            expr = re.match(r'console\.typeline\((.*?)\)', line).group(1)
            try:
                output = eval_concat_expr(expr)
                for c in output:
                    print(c, end='', flush=True)
                    time.sleep(0.05)
                print()
            except Exception as e:
                print(f"❌ Error in typeline: {e}")
            i += 1
            continue

        # Console.puttext
        elif re.match(r'console\.puttext\((.*?)\)', line):
            expr = re.match(r'console\.puttext\((.*?)\)', line).group(1)
            try:
                output = eval_concat_expr(expr)
                print(output)
            except Exception as e:
                print(f"❌ Error in puttext: {e}")
            i += 1
            continue

        # Draw cube
        elif re.match(r'draw\.cube = (\w+)', line):
            name = re.match(r'draw\.cube = (\w+)', line).group(1)
            gui_elements.append({"type": "cube", "name": name})
            i += 1
            continue

        # Draw image path
        elif re.match(r'draw\.path = (.*?)/name="(.*?)"', line):
            path, name = re.match(r'draw\.path = (.*?)/name="(.*?)"', line).groups()
            gui_elements.append({
                "type": "image",
                "name": name,
                "path": path.strip(),
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "color": None
            })
            i += 1
            continue

        elif re.match(r'(\w+)\.(\w+) = "(.*?)"', line):
            name, prop, value = re.match(r'(\w+)\.(\w+) = "(.*?)"', line).groups()
            for el in gui_elements:
                if el.get("name") == name:
                    if prop in ["x", "y", "width", "height"]:
                        el[prop] = int(value.replace("px", "").strip())
                    elif prop in ["color", "text"]:
                        el[prop] = value
                    else:
                        el[prop] = value


        # Draw button
        elif re.match(r'draw\.button = text="(.*?)"/x=(.*?)/y=(.*?)/function=(.*?)$', line):
            text, x, y, function = re.match(r'draw\.button = text="(.*?)"/x=(.*?)/y=(.*?)/function=(.*?)$', line).groups()
            x = int(x.replace("px", "").strip())
            y = int(y.replace("px", "").strip())
            gui_elements.append({"type": "button", "text": text, "x": x, "y": y, "function": function})
            i += 1
            continue
        # Draw text
        elif re.match(r'draw\.text = (\w+)', line):
            name = re.match(r'draw\.text = (\w+)', line).group(1)
            gui_elements.append({
                "type": "text",
                "name": name,
                "text": "",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 30,
                "color": "black"
            })
            i += 1
            continue


        # If / Else If / Else blocks
        elif line.startswith("if "):
            blocks = []
            while i < len(lines):
                block_line = lines[i].strip()
                if re.match(r'^(if|else if) (.*?) \{$', block_line):
                    condition = re.match(r'^(if|else if) (.*?) \{$', block_line).group(2)
                    condition = resolve_vars(condition)
                    body = []
                    i += 1
                    while i < len(lines) and lines[i].strip() != '}':
                        body.append(lines[i].strip())
                        i += 1
                    blocks.append(("condition", condition, body))
                elif block_line == "else {":
                    body = []
                    i += 1
                    while i < len(lines) and lines[i].strip() != '}':
                        body.append(lines[i].strip())
                        i += 1
                    blocks.append(("else", None, body))
                    i += 1
                    break
                else:
                    break
                i += 1
            for block in blocks:
                if block[0] == "condition":
                    try:
                        if eval(block[1], {}, context):
                            run_ell_lines(block[2])
                            break
                    except Exception as e:
                        print(f"❌ Error in if condition: {e}")
                        break
                elif block[0] == "else":
                    run_ell_lines(block[2])
                    break
            continue

        # Create audio loader
        elif re.match(r'(\w+) = new audioLoaderForEll\(\)', line):
            loader_name = re.match(r'(\w+) = new audioLoaderForEll\(\)', line).group(1)
            audio_loaders[loader_name] = {}
            print(f"🆕 Created audio loader: {loader_name}")
            i += 1
            continue

        # Load audio path
        elif re.match(r'(\w+)\.load\("(.*?)"\)', line):
            loader_name, path = re.match(r'(\w+)\.load\("(.*?)"\)', line).groups()
            if loader_name in audio_loaders:
                audio_loaders[loader_name]["path"] = path.strip()
                print(f"📂 Loader '{loader_name}' loaded path: {path}")
            else:
                print(f"❌ Audio loader '{loader_name}' not defined.")
            i += 1
            continue

        # Play audio
        elif re.match(r'(\w+)\.play\(loop="(\d+)"\)', line):
            match = re.match(r'(\w+)\.play\(loop="(\d+)"\)', line)
            if match:
                name, loop = match.groups()
                loop = int(loop) - 1
                if name in audios:
                    try:
                        if isinstance(audios[name], pygame.mixer.Sound):
                            print(f"🔊 Playing sound '{name}' with loop={loop + 1}")
                            audios[name].play(loops=loop)
                        else:
                            print(f"🎵 Loading music '{name}' from path '{audios[name]}'")
                            pygame.mixer.music.load(audios[name])
                            pygame.mixer.music.play(loops=loop)
                            print(f"🎵 Music '{name}' is now playing with loop={loop + 1}")
                    except Exception as e:
                        print(f"❌ Error playing audio '{name}': {e}")
                else:
                    print(f"❌ Audio '{name}' not found.")
            i += 1
            continue

        # Assign name to audio
        elif re.match(r'(\w+)\.name = "(.*?)"', line):
            loader_name, name = re.match(r'(\w+)\.name = "(.*?)"', line).groups()
            if loader_name in audio_loaders:
                path = audio_loaders[loader_name].get("path")
                if path:
                    try:
                        if path.endswith((".wav", ".ogg")):
                            audios[name] = pygame.mixer.Sound(path)
                            print(f"🔊 Sound '{name}' loaded from path '{path}'")
                        elif path.endswith((".mp3", ".flac")):
                            audios[name] = path
                            print(f"🎵 Music '{name}' loaded from path '{path}'")
                        else:
                            print(f"❌ Unsupported audio format: {path}")
                    except Exception as e:
                        print(f"❌ Error loading audio '{path}': {e}")
            i += 1
            continue
                # Language-based return: returnhtml(...), returnpython(...), returnc++(...)
               # Handle returnhtml, returnpython, returnc++
        elif line.startswith("returnhtml("):
            content = line[len("returnhtml("):-1]
            print(f"🌐 Queued HTML block: {content}")
            html_blocks.append(content)  # store it for GUI or file
            i += 1
            continue

        elif line.startswith("returnpython("):
            code = line[len("returnpython("):-1]
            print(f"🐍 Running inline Python code: {code}")
            try:
                exec(code, {}, context)
            except Exception as e:
                print(f"❌ Python error: {e}")
            i += 1
            continue

        elif line.startswith("returnc++("):
            code = line[len("returnc++("):-1]
            print(f"💻 Queued C++ logic (not executed): {code}")
            # You could save this into a .cpp file, send it to compiler, etc.
            i += 1
            continue


# After processing all lines, render HTML in GUI


    # Optional: write to an HTML file



def render_gui():
    root = tk.Tk()
    root.title("ELL GUI")

    def make_callback(func_call):
        def callback():
            match = re.match(r'(\w+)\((.*?)\)', func_call)
            if match:
                fname = match.group(1)
                raw_args = match.group(2)
                args = [resolve_vars(arg.strip()) for arg in raw_args.split(',')]
            else:
                fname = func_call.strip()
                args = []

            if fname in functions:
                local_context = dict(zip(functions[fname]["params"], args))
                original_context = context.copy()
                context.update(local_context)
                run_ell_lines(functions[fname]["body"])
                context.clear()
                context.update(original_context)
            else:
                print(f"❌ Function '{fname}' not defined.")
        return callback

    for el in gui_elements:
        if el["type"] == "cube":
            frame = tk.Frame(root, bg=el.get("color", "gray"),
                             width=el.get("width", 100), height=el.get("height", 100))
            frame.place(x=el.get("x", 0), y=el.get("y", 0))

        elif el["type"] == "button":
            button = tk.Button(root, text=el["text"], command=make_callback(el["function"]))
            button.place(x=el["x"], y=el["y"])

        elif el["type"] == "image":
            try:
                from PIL import Image, ImageTk
                img = Image.open(el["path"])
                img = img.resize((el.get("width", 100), el.get("height", 100)))
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(root, image=photo)
                label.image = photo
                label.place(x=el["x"], y=el["y"])
            except Exception as e:
                print(f"❌ Error loading image '{el['path']}': {e}")

        elif el["type"] == "text":
            label = tk.Label(root, text=el.get("text", ""), fg=el.get("color", "black"), bg="white",
                             width=el.get("width", 100) // 10)
            label.place(x=el.get("x", 0), y=el.get("y", 0))

    # ✅ Render HTML blocks at the bottom
    if html_blocks:
        html_frame = tk.Frame(root, bg="lightgray")
        html_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        from tkhtmlview import HTMLLabel

        for block in html_blocks:
            html_label = HTMLLabel(html_frame, html=block, background="lightgray")
            html_label.pack(fill=tk.BOTH, pady=4, expand=True)


    root.geometry("800x600")
    root.mainloop()



# Debug printout
print(f"Audio loader initialized: {audio_loaders}")
print(f"Audio objects: {audios}")
