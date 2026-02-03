import sys
from cx_Freeze import setup, Executable

# Increase recursion limit for deep dependency trees like torch/transformers
sys.setrecursionlimit(5000)

# Dependencies are automatically detected, but some need manual inclusion.
build_exe_options = {
    "packages": [
        "customtkinter", "PIL", "requests", "transformers", "torch", 
        "huggingface_hub", "gguf", "plyer", "tokenizers"
    ],
    "excludes": [],
    "include_files": [
        "logo.ico",
        "logo.png",
        "changelog.txt",
        "privacy_policy.txt",
        "terms_of_use.txt"
    ],
    "build_exe": "dist"  # Output to 'dist' folder to match Inno Setup script
}

# GUI applications require a different base on Windows (hides the console)
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Orion AI Chatbot",
    version="1.3.4",
    description="Orion AI Chatbot by OmniNode",
    options={"build_exe": build_exe_options},
    executables=[Executable("interface.py", base=base, target_name="Orion.exe", icon="logo.ico")]
)
