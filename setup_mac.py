import sys
from cx_Freeze import setup, Executable

# Increase recursion limit for deep dependency trees like torch/transformers
sys.setrecursionlimit(5000)

# Include necessary packages and files
build_exe_options = {
    "packages": [
        "customtkinter", "PIL", "requests", "transformers", "torch",
        "huggingface_hub", "gguf", "plyer", "tokenizers", "os"
    ],
    "excludes": ["tkinter"],  # Only use customtkinter
    "include_files": [
        "logo.png",
        "changelog.txt",
        "privacy_policy.txt",
        "terms_of_use.txt",
        "icon.icns"  # macOS icon
    ],
    "build_exe": "dist"  # Output folder
}

# Determine base and target name
base = None
if sys.platform == "darwin":
    target_name = "Orion_Mac"
else:
    target_name = "Orion.exe" if sys.platform == "win32" else "Orion_Linux"

# Setup configuration
setup(
    name="Orion AI Chatbot",
    version="1.3.5",
    description="Orion AI Chatbot by OmniNode",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "interface.py",
            base=base,
            target_name=target_name,
            icon="icon.icns" if sys.platform == "darwin" else "logo.ico"
        )
    ]
)
