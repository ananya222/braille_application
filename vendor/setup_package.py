import os

src_path = r"o:\braille_app2\liblouis-src\liblouis-3.38.0\python\louis\__init__.py.in"
dest_dir = r"o:\braille_app2\louis"
dest_path = os.path.join(dest_dir, "__init__.py")

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the replacement code for liblouis DLL loading
replacement = """import os
from ctypes import CDLL, WinDLL

# Try to find liblouis.dll relative to this package or in the workspace
dll_name = "liblouis.dll"
possible_paths = [
    os.path.join(os.path.dirname(__file__), dll_name),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", dll_name)),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "liblouis-win64", "bin", dll_name)),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "liblouis-win64", "bin", dll_name)),
]

liblouis = None
for path in possible_paths:
    if os.path.exists(path):
        try:
            # On Windows, windll or cdll can load it depending on the loader choice.
            # We'll use the _loader from liblouis setup (windll on Win32, cdll on Unix)
            liblouis = _loader[path]
            break
        except Exception:
            pass

if liblouis is None:
    try:
        # Fallback to standard library search
        liblouis = _loader["liblouis"]
    except Exception as e:
        raise ImportError(f"Could not load liblouis DLL from paths {possible_paths}. Error: {e}")"""

# Replace the specific line
target = 'liblouis = _loader["###LIBLOUIS_SONAME###"]'
if target in content:
    content = content.replace(target, replacement)
    print("Successfully replaced SONAME placeholder.")
else:
    print("Warning: target placeholder not found!")

with open(dest_path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Written updated python binding to {dest_path}")
