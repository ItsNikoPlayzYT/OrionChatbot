import sys
from cx_Freeze import setup, Executable

sys.setrecursionlimit(5000)

# --------------------
# Build options
# --------------------
build_exe_options = {
    "packages": [
        "customtkinter", "PIL", "requests", "transformers", "torch",
        "huggingface_hub", "gguf", "plyer", "tokenizers", "os"
    ],
    "include_files": [
        "icon.png",
        "icon.ico",
        "changelog.txt",
        "privacy_policy.txt",
        "terms_of_use.txt"
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
# Platform logic
# --------------------
base = None
target_name = "Orion"

if sys.platform == "win32":
    base = "Win32GUI"
    target_name = "Orion.exe"
    icon_file = "icon.ico"

elif sys.platform == "darwin":
    base = "GUI"              # REQUIRED to create .app
    target_name = "Orion.app"
    icon_file = "icon.png"

else:
    icon_file = None

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
    executables=[
        Executable(
            "interface.py",
            base=base,
            target_name=target_name,
            icon=icon_file,
        )
    ],
)
