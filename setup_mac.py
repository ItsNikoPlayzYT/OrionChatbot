import sys
import os
from cx_Freeze import setup, Executable

# Increase recursion limit
sys.setrecursionlimit(5000)

# Absolute path to repo root
HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------
# Platform-specific settings
# --------------------
if sys.platform == "win32":
    base = "Win32GUI"
    target_name = "Orion.exe"
    icon_file = os.path.join(HERE, "icon.ico")
elif sys.platform == "darwin":
    base = None  # macOS GUI auto-detected
    target_name = "Orion"  # cx_Freeze adds .app automatically
    icon_file = os.path.join(HERE, "icon.icns")  # generated in workflow
else:
    base = None
    target_name = "Orion"
    icon_file = None

# --------------------
# Build options
# --------------------
build_exe_options = {
    "packages": [
        "customtkinter", "PIL", "requests", "transformers", "torch",
        "huggingface_hub", "gguf", "plyer", "tokenizers", "os"
    ],
    "include_files": [
        os.path.join(HERE, "logo.png"),      # original logo
        os.path.join(HERE, "icon.ico"),      # Windows icon
        os.path.join(HERE, "changelog.txt"),
        os.path.join(HERE, "privacy_policy.txt"),
        os.path.join(HERE, "terms_of_use.txt")
    ],
}

# --------------------
# macOS DMG options
# --------------------
bdist_dmg_options = {
    "volume_label": "Orion Installer",
    "applications_shortcut": True,
}

# --------------------
# Executable
# --------------------
executables = [
    Executable(
        "interface.py",
        base=base,
        target_name=target_name,
        icon=icon_file,
    )
]

# --------------------
# Setup
# --------------------
setup(
    name="Orion AI Chatbot",
    version="1.3.5",
    description="Orion AI Chatbot by OmniNode",
    options={
        "build_exe": build_exe_options,
        "bdist_dmg": bdist_dmg_options,
    },
    executables=executables,
)
