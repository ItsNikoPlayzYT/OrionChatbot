import sys
import os
from cx_Freeze import setup, Executable

# Increase recursion limit for deep dependency trees like torch/transformers
sys.setrecursionlimit(5000)

# Dependencies are automatically detected, but some need manual inclusion.
build_exe_options = {
    "packages": [
        "customtkinter", "PIL", "requests", "transformers", "torch", 
        "huggingface_hub", "gguf", "plyer", "tokenizers", "os"
    ],
    "excludes": ["tkinter"], # Use 'customtkinter' only to save space
    "include_files": [
        "logo.ico",
        "logo.png",
        "changelog.txt",
        "privacy_policy.txt",
        "terms_of_use.txt"
    ],
    "build_exe": "dist"  # Output folder
}

# Logic for Platform Specifics
base = None
target_name = "Orion"

if sys.platform == "win32":
    base = "Win32GUI"  # Hides console on Windows
    target_name = "Orion.exe"
elif sys.platform == "darwin":
    target_name = "Orion_Mac" # Mac Executable
else:
    target_name = "Orion_Linux" # Linux Executable

setup(
    name="Orion AI Chatbot",
    version="1.3.5", # Updated to match your latest release
    description="Orion AI Chatbot by OmniNode",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "interface.py", 
            base=base, 
            target_name=target_name, 
            icon="logo.ico" if sys.platform == "win32" else None
        )
    ]
)
