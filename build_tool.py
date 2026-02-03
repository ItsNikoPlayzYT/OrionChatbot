import os
import sys
import subprocess
import shutil

def clean_build():
    """Removes old build and dist folders to ensure a fresh compile."""
    folders = ['build', 'dist']
    for folder in folders:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)

def run_build():
    """Runs the setup.py script based on the current OS."""
    print(f"Detected Platform: {sys.platform}")
    
    # Use 'python' or 'python3' depending on the system
    python_cmd = sys.executable if sys.executable else "python"
    
    try:
        # Step 1: Install cx_Freeze if missing
        print("Checking for cx_Freeze...")
        subprocess.check_call([python_cmd, "-m", "pip", "install", "cx_Freeze"])
        
        # Step 2: Run the build
        print("Starting build process...")
        # 'build' is the standard command for cx_Freeze
        subprocess.check_call([python_cmd, "setup.py", "build"])
        
        print("\n" + "="*30)
        print("BUILD SUCCESSFUL!")
        print(f"Executables can be found in the 'dist' or 'build' folder.")
        print("="*30)

    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with exit code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    # Ask user for confirmation or just run
    clean_build()
    run_build()
