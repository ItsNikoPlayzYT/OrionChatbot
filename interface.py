import customtkinter as ctk
import time
import threading
import os
import pickle
import json
import winsound
import webbrowser
import requests
import sys
import stat
from tkinter import Menu, filedialog
from PIL import Image, ImageGrab
from io import BytesIO
import zipfile
import tempfile
import shutil
import re
from plyer import notification
try:
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download, scan_cache_dir
except ImportError:
    pass

try:
    from main import OrionChatbot
    ORION_AVAILABLE = True
except ImportError as e:
    ORION_AVAILABLE = False
    print(f"Warning: Could not import OrionChatbot: {e}")

class OrionGUI:
    def __init__(self):
        if not ORION_AVAILABLE:
            raise RuntimeError("OrionChatbot is not available. Please check main.py")

        self.root = ctk.CTk()
        # Set window icon if available
        if os.path.exists('logo.ico'):
           self.root.iconbitmap('logo.ico')
           
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.withdraw() # Hide main window initially

        # --- Futuristic Loading Screen ---
        self.loading_window = ctk.CTkToplevel(self.root)
        self.loading_window.title("INITIALIZING ORION SYSTEMS")
        self.loading_window.geometry("500x300")
        self.loading_window.overrideredirect(True) # Remove window decorations
        self.center_window(self.loading_window, 500, 300)
        
        # Deep dark cyber aesthetic
        self.loading_window.configure(fg_color="#050510") # Very dark blue/black
        
        # Main Frame with neon border effect
        loading_frame = ctk.CTkFrame(self.loading_window, fg_color="#0a0a1a", border_color="#00ffcc", border_width=2)
        loading_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Logo/Title with glow effect (simulated with color)
        title_label = ctk.CTkLabel(loading_frame, text="O R I O N   A I", font=("Roboto Medium", 30), text_color="#00ffff")
        title_label.pack(pady=(50, 10))
        
        subtitle_label = ctk.CTkLabel(loading_frame, text="Neural Interface v1.3.5", font=("Consolas", 12), text_color="#0088aa")
        subtitle_label.pack(pady=(0, 30))

        # Progress Bar
        self.loading_progress = ctk.CTkProgressBar(loading_frame, width=400, height=20, progress_color="#00e5ff")
        self.loading_progress.pack(pady=10)
        self.loading_progress.set(0)

        # Animated Status Text
        self.loading_status = ctk.CTkLabel(loading_frame, text="Initializing core systems...", font=("Consolas", 11), text_color="#00ccaa")
        self.loading_status.pack(pady=5)
        
        # Force update to show window immediately
        self.loading_window.update()

        # Initialize settings variables (moved from original init)
        self.font_size_var = ctk.IntVar(value=12)
        self.ollama_model_var = ctk.StringVar(value="gemma3:1b")
        self.temp_var = ctk.DoubleVar(value=0.7)
        self.tokens_var = ctk.IntVar(value=500)
        self.auto_save_var = ctk.BooleanVar(value=True)
        self.sound_var = ctk.BooleanVar(value=False)
        self.thinking_var = ctk.BooleanVar(value=True)
        self.typing_speed_var = ctk.IntVar(value=15)
        self.strict_mode_var = ctk.BooleanVar(value=False)
        self.startup_greeting_var = ctk.StringVar(value="Hello! I am Orion, an AI chatbot created by OmniNode. How can I help you today?")
        self.system_prompt = ""
        self.last_interaction_time = 0
        self.running = True
        self.current_model = "Basic (1.3)"
        self.sidebar_collapsed = False
        self.current_chat_id = None
        self.chat_history_data = []

        # Start background initialization
        threading.Thread(target=self.run_initialization, daemon=True).start()

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def run_initialization(self):
        steps = [
            ("Loading core configuration...", 0.1),
            ("Mounting data partitions...", 0.2),
            ("Initializing neural network...", 0.3),
            ("Loading Qwen 2.5 1.5B (High Intelligence)...", 0.4),
        ]
        
        for text, progress in steps:
            # Schedule GUI update on main thread
            self.root.after(0, lambda t=text, p=progress: self.update_loading_status(t, p))
            time.sleep(0.3) # Aesthetic delay
            
        try:
            self.orion = OrionChatbot() # This acts as the heavy lifting
            if not self.orion.llm:
                 self.root.after(0, lambda: self.update_loading_status("AI Engine failed to load. Running in legacy mode.", 0.9))
                 time.sleep(1)
        except Exception as e:
            self.root.after(0, lambda: self.loading_status.configure(text=f"CRITICAL ERROR: {e}", text_color="red"))
            return

        self.root.after(0, lambda: self.update_loading_status("Finalizing interface...", 0.9))
        time.sleep(0.5)
        
        # Setup the rest of the UI on the main thread
        self.root.after(0, self.complete_ui_setup)

    def update_loading_status(self, text, progress):
        try:
            if self.loading_window.winfo_exists():
                self.loading_status.configure(text=text)
                self.loading_progress.set(progress)
        except Exception:
            pass

    def complete_ui_setup(self):
        # Define data directory
        self.data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), '.orion')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Load saved settings
        self.load_settings()

        # Apply loaded model and title
        self.orion.current_model = self.current_model
        self.root.title(f"Orion {self.current_model} Chat Client - AI Chatbot by OmniNode")

        # --- Reconstruct Main UI ---
        # Model selector frame
        model_frame = ctk.CTkFrame(self.root)
        model_frame.pack(fill="x", padx=10, pady=5)

        model_label = ctk.CTkLabel(model_frame, text="Model:")
        model_label.pack(side="left", padx=5)

        # Updated model list to match capabilities
        self.model_selector = ctk.CTkComboBox(model_frame, values=["Basic (1.3.5)"], command=self.change_model)
        self.model_selector.pack(side="left", padx=5)
        self.model_selector.set(self.current_model)

        self.legacy_selector = ctk.CTkComboBox(model_frame, values=["Legacy Basic (1.1)", "Legacy Pro (1.1)", "Legacy Advanced (1.1)", "Legacy (1.0)", "Legacy (0.9)", "Legacy (0.8)"], command=self.change_legacy_model)

        # Sidebar toggle button
        self.sidebar_toggle = ctk.CTkButton(model_frame, text="☰", width=40, command=self.toggle_sidebar)
        self.sidebar_toggle.pack(side="right", padx=5)

        # Settings button
        settings_button = ctk.CTkButton(model_frame, text="⚙️", width=40, command=self.open_settings)
        settings_button.pack(side="right", padx=5)

        # Vision toggle button
        self.vision_button = ctk.CTkButton(model_frame, text="👁️", width=40, command=self.toggle_vision)
        self.vision_button.pack(side="right", padx=5)

        # Main container frame
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 5))

        # Sidebar title
        sidebar_title = ctk.CTkLabel(self.sidebar_frame, text="Chats", font=("Arial", 16, "bold"))
        sidebar_title.pack(pady=10)

        # New chat button
        new_chat_button = ctk.CTkButton(self.sidebar_frame, text="+ New Chat", command=self.create_new_chat)
        new_chat_button.pack(fill="x", padx=5, pady=5)

        # Import chat button
        import_chat_button = ctk.CTkButton(self.sidebar_frame, text="📥 Import Chat", command=self.import_chat_file, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        import_chat_button.pack(fill="x", padx=5, pady=(0, 5))

        # Search bar
        self.search_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Search chats...")
        self.search_entry.pack(fill="x", padx=5, pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_chat_list())

        # Chat list (scrollable)
        self.chat_list = ctk.CTkScrollableFrame(self.sidebar_frame)
        self.chat_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Load existing chat buttons
        self.refresh_chat_list()

        # Content frame (right side)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Chat history scrollable frame for bubbles
        self.chat_history = ctk.CTkScrollableFrame(self.content_frame)
        self.chat_history.pack(pady=10, padx=10, fill="both", expand=True)

        # Thinking frame (initially hidden)
        self.thinking_frame = ctk.CTkFrame(self.content_frame)
        self.thinking_label = ctk.CTkLabel(self.thinking_frame, text="Orion is thinking...")
        self.thinking_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.thinking_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # Input frame
        self.input_frame = ctk.CTkFrame(self.content_frame)
        self.input_frame.pack(fill="x", padx=10, pady=5)

        self.input_field = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message here...")
        self.input_field.pack(side="left", fill="x", expand=True, padx=5)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right", padx=5)

        # Status bar for memory indicator
        self.status_bar = ctk.CTkFrame(self.content_frame, height=20, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

        self.memory_status_indicator = ctk.CTkLabel(self.status_bar, text="⚫ Not Loaded", text_color="gray", font=("Arial", 10))
        self.memory_status_indicator.pack(side="right", padx=5)

        self.retry_button = ctk.CTkButton(self.status_bar, text="↻", width=15, height=15, font=("Arial", 12, "bold"), command=self.manual_retry_connection, fg_color="transparent", text_color="red", hover_color=("gray85", "gray25"))
        # Hidden by default

        self.ram_usage_label = ctk.CTkLabel(self.status_bar, text="", text_color="gray", font=("Arial", 10))
        self.ram_usage_label.pack(side="right", padx=5)
        
        self.internet_status_indicator = ctk.CTkLabel(self.status_bar, text="🌐 Checking...", text_color="gray", font=("Arial", 10))
        self.internet_status_indicator.pack(side="right", padx=5)

        # Bind Enter key to send
        self.input_field.bind("<Return>", lambda event: self.send_message())

        # Start memory status check
        self.start_memory_status_check()

        # Start internet connection check
        self.start_internet_check()
        
        # Close loading screen and show main
        self.loading_window.destroy()
        self.root.deiconify()
        
        # Initial greeting
        self.add_to_history(f"Orion: {self.startup_greeting_var.get()}\n", animate=True)  

    def on_closing(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def change_model(self, selected_model):
        if selected_model == "Legacy ▼":
            # Show legacy selector
            self.legacy_selector.pack(side="left", padx=5)
            self.legacy_selector.set("Legacy (1.0)")
            self.current_model = "Legacy (1.0)"
        else:
            # Hide legacy selector if visible
            try:
                self.legacy_selector.pack_forget()
            except:  # noqa: E722
                pass
            self.current_model = selected_model
        self.orion.current_model = self.current_model  # Update orion's current_model
        self.root.title(f"Orion ({self.current_model}) - AI Chatbot by OmniNode")
        self.add_to_history(f"Orion: Switched to {selected_model} model.\n")

    def change_legacy_model(self, selected_legacy):
        self.current_model = selected_legacy
        self.orion.current_model = self.current_model  # Update orion's current_model
        self.root.title(f"Orion ({self.current_model}) - AI Chatbot by OmniNode")
        self.add_to_history(f"Orion: Switched to {selected_legacy} model.\n")

    def open_settings(self):
        # Reload settings from file to reflect saved state
        self.load_settings()

        # Create settings window
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Orion Settings")
        settings_window.geometry("800x800")
        settings_window.resizable(False, False)

        # Create tabview for organized settings
        tabview = ctk.CTkTabview(settings_window, width=550, height=650)
        tabview.pack(pady=10, padx=10, expand=True, fill="both")

        # General Tab
        tabview.add("General")
        general_tab = tabview.tab("General")

        # Model info
        model_info_label = ctk.CTkLabel(general_tab, text=f"Current Model: {self.current_model}")
        model_info_label.pack(pady=10)

        # Creator info
        creator_label = ctk.CTkLabel(general_tab, text="Created by: OmniNode")
        creator_label.pack(pady=5)

        # Version info
        version_label = ctk.CTkLabel(general_tab, text=f"Version: {self.orion.model_version}")
        version_label.pack(pady=5)

        # Theme selector
        theme_label = ctk.CTkLabel(general_tab, text="Theme:")
        theme_label.pack(pady=(20, 5))
        theme_selector = ctk.CTkComboBox(general_tab, values=["System", "Light", "Dark"], command=self.change_theme)
        theme_selector.pack(pady=5)
        theme_selector.set(ctk.get_appearance_mode())

        # Font size
        font_label = ctk.CTkLabel(general_tab, text="Font Size:")
        font_label.pack(pady=(20, 5))
        font_frame = ctk.CTkFrame(general_tab)
        font_frame.pack(pady=5)
        font_minus = ctk.CTkButton(font_frame, text="-", width=30, command=lambda: self.adjust_font_size(-1))
        font_minus.pack(side="left", padx=5)
        font_size_label = ctk.CTkLabel(font_frame, textvariable=self.font_size_var)
        font_size_label.pack(side="left", padx=10)
        font_plus = ctk.CTkButton(font_frame, text="+", width=30, command=lambda: self.adjust_font_size(1))
        font_plus.pack(side="right", padx=5)

        # Startup Greeting
        greeting_label = ctk.CTkLabel(general_tab, text="Startup Greeting:")
        greeting_label.pack(pady=(20, 5))
        greeting_entry = ctk.CTkEntry(general_tab, textvariable=self.startup_greeting_var, width=350)
        greeting_entry.pack(pady=5)

        # Models Tab
        tabview.add("Models")
        models_tab = tabview.tab("Models")

        # Search Controls
        controls_frame = ctk.CTkFrame(models_tab)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        self.model_search_entry = ctk.CTkEntry(controls_frame, placeholder_text="Search models...", width=200)
        self.model_search_entry.pack(side="left", padx=5)
        
        self.model_sort_var = ctk.StringVar(value="Most Downloaded")
        sort_combo = ctk.CTkComboBox(controls_frame, values=["Most Downloaded", "Best Rated", "Newest", "Oldest"], variable=self.model_sort_var, width=130)
        sort_combo.pack(side="left", padx=5)
        
        search_btn = ctk.CTkButton(controls_frame, text="Search", width=60, command=self.search_models)
        search_btn.pack(side="left", padx=5)

        import_btn = ctk.CTkButton(controls_frame, text="Import Folder", width=80, fg_color="#28a745", hover_color="#218838", command=self.import_local_folder)
        import_btn.pack(side="left", padx=5)

        # Quick Categories
        cats_frame = ctk.CTkScrollableFrame(models_tab, height=40, orientation="horizontal", fg_color="transparent")
        cats_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        ctk.CTkButton(cats_frame, text="🚀 Fastest (Nano)", height=24, width=80, fg_color="#4b4b4b", command=lambda: self.quick_search("TinyLlama")).pack(side="left", padx=2)
        ctk.CTkButton(cats_frame, text="⚡ Balanced (Small)", height=24, width=80, fg_color="#4b4b4b", command=lambda: self.quick_search("Qwen 2.5 1.5B")).pack(side="left", padx=2)
        ctk.CTkButton(cats_frame, text="🧠 Smartest (Medium)", height=24, width=80, fg_color="#4b4b4b", command=lambda: self.quick_search("Llama 3.2 3B")).pack(side="left", padx=2)
        ctk.CTkButton(cats_frame, text="🌟 Trending", height=24, width=80, fg_color="#4b4b4b", command=lambda: self.quick_search("")).pack(side="left", padx=2)

        # Results List
        self.models_list_frame = ctk.CTkScrollableFrame(models_tab)
        self.models_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Populate with installed models initially
        self.refresh_installed_models()

        # Behavior Tab
        tabview.add("Behavior")
        behavior_tab = tabview.tab("Behavior")

        # Auto-save toggle
        auto_save_check = ctk.CTkCheckBox(behavior_tab, text="Auto-save chats", variable=self.auto_save_var)
        auto_save_check.pack(pady=(20, 5))

        # Sound notifications
        sound_check = ctk.CTkCheckBox(behavior_tab, text="Sound notifications", variable=self.sound_var)
        sound_check.pack(pady=5)

        # Show thinking animation
        thinking_check = ctk.CTkCheckBox(behavior_tab, text="Show thinking animation", variable=self.thinking_var)
        thinking_check.pack(pady=5)

        # Strict Mode
        strict_check = ctk.CTkCheckBox(behavior_tab, text="Strict Command Mode (Disable auto-actions)", variable=self.strict_mode_var)
        strict_check.pack(pady=5)

        # Typing Speed
        speed_label = ctk.CTkLabel(behavior_tab, text="Typing Speed (ms delay - lower is faster):")
        speed_label.pack(pady=(20, 5))
        speed_slider = ctk.CTkSlider(behavior_tab, from_=1, to=100, variable=self.typing_speed_var, number_of_steps=99)
        speed_slider.pack(pady=5)

        # Data Management Tab
        tabview.add("Data")
        data_tab = tabview.tab("Data")

        # Export chat history
        export_button = ctk.CTkButton(data_tab, text="Export Chat History", command=self.export_chat_history)
        export_button.pack(pady=(20, 10))

        # Clear all chats
        clear_button = ctk.CTkButton(data_tab, text="Clear All Chat History", fg_color="red", command=self.clear_all_chats)
        clear_button.pack(pady=10)

        # Chat statistics
        stats_label = ctk.CTkLabel(data_tab, text="Chat Statistics:")
        stats_label.pack(pady=(20, 5))
        chat_count = len([f for f in os.listdir(self.data_dir) if f.startswith('chat_') and f.endswith('.dat')])
        stats_text = ctk.CTkLabel(data_tab, text=f"Total chats: {chat_count}")
        stats_text.pack(pady=5)

        # Delete .orion folder button
        delete_data_button = ctk.CTkButton(data_tab, text="Delete .orion Folder", fg_color="red", hover_color="darkred", command=self.delete_orion_folder)
        delete_data_button.pack(pady=20)

        # About Tab
        tabview.add("About")
        about_tab = tabview.tab("About")

        about_text = f"""Orion AI Chatbot v{self.orion.model_version}

A sophisticated AI assistant created by OmniNode.

Powered by Transformers and local LLMs.
Built with Python and CustomTkinter."""

        about_label = ctk.CTkLabel(about_tab, text=about_text, justify="left")
        about_label.pack(pady=20, padx=20)

        # Check for updates
        update_button = ctk.CTkButton(about_tab, text="Check for Updates", command=self.check_for_updates)
        update_button.pack(pady=10)

        # Save and Close buttons at bottom
        button_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        button_frame.pack(side="bottom", pady=20)

        save_button = ctk.CTkButton(button_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(side="left", padx=10)

        close_button = ctk.CTkButton(button_frame, text="Close", command=settings_window.destroy)
        close_button.pack(side="right", padx=10)


    def check_for_updates(self):
        # --- CONFIGURATION ---
        # Paste the File ID of your version.txt from Google Drive here:
        VERSION_FILE_ID = "1tJHHeNJwJRf6WgZeiZJsHJrVqNgyDOpBhaXSVOxMnnM" 
        # ---------------------

        UPDATE_CHECK_URL = f"https://docs.google.com/document/d/{VERSION_FILE_ID}/export?format=txt"

        def run_check():
            try:
                response = requests.get(UPDATE_CHECK_URL, timeout=10)
                response.raise_for_status()
                
                if response.text.strip() == "N/A":
                    self.root.after(0, lambda: notification.notify(
                        title="Orion Update Check",
                        message="No updates available.",
                        app_name="Orion AI",
                        timeout=10
                    ))
                    return
                
                lines = response.text.strip().split('\n')
                latest_version = lines[0].strip() if lines else '0.0.0'
                download_url = lines[1].strip() if len(lines) > 1 else ''
                
                current_ver = self.parse_version(self.orion.model_version)
                latest_ver = self.parse_version(latest_version)
                
                if latest_ver > current_ver:
                    if download_url and download_url.lower() != "n/a" and download_url.startswith("http"):
                        self.root.after(0, lambda: notification.notify(
                            title="Orion Update Available",
                            message=f"Version {latest_version} is available. Downloading...",
                            app_name="Orion AI",
                            timeout=10
                        ))
                        self.download_and_install_update_zip(download_url)
                    else:
                        self.root.after(0, lambda: notification.notify(
                            title="Orion Update Check",
                            message=f"Version {latest_version} is listed but not available for download.",
                            app_name="Orion AI",
                            timeout=10
                        ))
                else:
                    self.root.after(0, lambda: notification.notify(
                        title="Orion Update Check",
                        message=f"You are running the latest version (v{self.orion.model_version}).",
                        app_name="Orion AI",
                        timeout=10
                    ))
            except Exception as e:
                self.root.after(0, lambda err=str(e): notification.notify(
                    title="Orion Update Error",
                    message=f"Failed to check for updates: {err}",
                    app_name="Orion AI",
                    timeout=10
                ))

        threading.Thread(target=run_check, daemon=True).start()

    def _xor_cipher(self, data):
        key = b"OrionEncryptedChatV1"
        key_len = len(key)
        return bytes([b ^ key[i % key_len] for i, b in enumerate(data)])

    def _load_chat_data(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "rb") as f:
            content = f.read()
        if content.startswith(b"ORION_ENC"):
            return pickle.loads(self._xor_cipher(content[9:]))
        return pickle.loads(content)

    def _save_chat_data(self, filename, data):
        filepath = os.path.join(self.data_dir, filename)
        serialized = pickle.dumps(data)
        encrypted = self._xor_cipher(serialized)
        with open(filepath, "wb") as f:
            f.write(b"ORION_ENC" + encrypted)

    def parse_version(self, version_str):
        try:
            # Extract just the numbers X.Y.Z from string
            clean_version = re.search(r'(\d+(?:\.\d+)+)', version_str)
            if clean_version:
                return tuple(map(int, clean_version.group(1).split('.')))
            return (0, 0, 0)
        except Exception:
            return (0, 0, 0)

    def download_and_install_update_zip(self, zip_url):
        # Downloads a zip, extracts it, checks for a newer MSI, and runs it.
        def update_thread():
            try:
                # Perform Backup
                self.root.after(0, lambda: self.add_to_history("System: Backing up chat history...\n"))
                self.root.after(0, lambda: self.thinking_label.configure(text="Backing up data..."))
                self.root.after(0, lambda: self.thinking_frame.pack(before=self.input_frame, pady=5))
                self.root.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
                self.root.after(0, self.progress_bar.start)

                try:
                    backup_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Orion Backups')
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    backup_path = os.path.join(backup_dir, f"orion_backup_{timestamp}")
                    
                    shutil.make_archive(backup_path, 'zip', self.data_dir)
                    self.root.after(0, lambda p=f"{backup_path}.zip": self.add_to_history(f"System: Backup created successfully at {p}\n"))
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self.add_to_history(f"System: Warning: Backup failed: {err}\n"))

                self.root.after(0, lambda: self.add_to_history("System: Downloading update package...\n"))
                
                # Show progress bar
                self.root.after(0, lambda: self.thinking_label.configure(text="Downloading update..."))
                self.root.after(0, self.progress_bar.stop)
                self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))
                self.root.after(0, lambda: self.progress_bar.set(0))
                
                # Create a temporary directory
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, "update.zip")
                
                # Download
                response = requests.get(zip_url, stream=True)
                response.raise_for_status()
                
                total_length = response.headers.get('content-length')
                
                with open(zip_path, 'wb') as f:
                    if total_length is None:
                        f.write(response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for chunk in response.iter_content(chunk_size=8192):
                            dl += len(chunk)
                            f.write(chunk)
                            progress = dl / total_length
                            self.root.after(0, lambda p=progress: self.progress_bar.set(p))
                
                self.root.after(0, lambda: self.add_to_history("System: Extracting update package...\n"))
                self.root.after(0, lambda: self.thinking_label.configure(text="Extracting..."))
                
                # Extract
                extract_path = os.path.join(temp_dir, "extracted")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Find MSI with newer version
                current_ver = self.parse_version(self.orion.model_version)
                newer_msi = None
                
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if file.lower().endswith('.msi'):
                            # Check version in filename (e.g., Orion_1.3.4.msi)
                            file_ver = self.parse_version(file)
                            if file_ver > current_ver:
                                newer_msi = os.path.join(root, file)
                                break # Found a newer one
                
                if newer_msi:
                    self.root.after(0, lambda: self.add_to_history(f"System: Found newer version installer: {os.path.basename(newer_msi)}\n"))
                    self.root.after(0, lambda: self.add_to_history("System: Launching installer...\n"))
                    # Launch installer
                    os.startfile(newer_msi)
                    # We don't delete temp_dir here so the installer can run
                    self.root.after(0, lambda: self.thinking_frame.pack_forget())
                else:
                    self.root.after(0, lambda: self.add_to_history("System: No newer MSI version found in the update package.\n"))
                    self.root.after(0, lambda: self.thinking_frame.pack_forget())
                    # Cleanup
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                    
            except Exception as e:
                self.root.after(0, lambda: self.thinking_frame.pack_forget())
                self.root.after(0, lambda err=str(e): self.add_to_history(f"System: Update error: {err}\n"))

        threading.Thread(target=update_thread, daemon=True).start()

    def refresh_installed_models(self):
        # Clear list
        for widget in self.models_list_frame.winfo_children():
            widget.destroy()

        # 1. Models in .orion/models
        ctk.CTkLabel(self.models_list_frame, text="Custom Models (.orion):", font=("Arial", 14, "bold"), text_color="#00ffcc").pack(pady=(5,2), anchor="w")

        models_dir = os.path.join(self.data_dir, 'models')
        found_local = False
        if os.path.exists(models_dir):
            items = os.listdir(models_dir)
            for item in items:
                # Filter out hidden files/dirs like .cache
                if item.startswith('.'):
                    continue
                    
                path = os.path.join(models_dir, item)
                if os.path.isdir(path):
                    found_local = True
                    row = ctk.CTkFrame(self.models_list_frame)
                    row.pack(fill="x", pady=2)
                    
                    display_name = item.replace("--", "/")
                    is_active = (self.current_model == path) or (self.current_model == display_name)
                    
                    name_label = ctk.CTkLabel(row, text=display_name)
                    name_label.pack(side="left", padx=5)
                    
                    if is_active:
                        status_badge = ctk.CTkLabel(row, text="● ACTIVE", text_color="#28a745", font=("Arial", 10, "bold"))
                        status_badge.pack(side="left", padx=10)
                        name_label.configure(text_color="#28a745")
                    else:
                        status_badge = ctk.CTkLabel(row, text="○ UNLOADED", text_color="gray", font=("Arial", 10))
                        status_badge.pack(side="left", padx=10)

                    # Pass full path to loader
                    load_btn = ctk.CTkButton(row, text="Load", width=60, command=lambda p=path: self.load_local_model(p))
                    load_btn.pack(side="right", padx=5)
                    if is_active:
                        load_btn.configure(state="disabled", text="Active", fg_color="#2b2b2b")
                        
                    # Delete button for custom models
                    ctk.CTkButton(row, text="Delete", width=60, fg_color="#ff4444", hover_color="#cc0000", command=lambda p=path, n=display_name: self.delete_model_dialog(p, n)).pack(side="right", padx=5)
        
        if not found_local:
            ctk.CTkLabel(self.models_list_frame, text="No custom models found.").pack(pady=2, anchor="w", padx=10)

        # 2. Models in Hugging Face Cache
        ctk.CTkLabel(self.models_list_frame, text="Cached Models (Hugging Face):", font=("Arial", 14, "bold"), text_color="#00ffcc").pack(pady=(15,2), anchor="w")
        
        try:
            cache_info = scan_cache_dir()
            found_cache = False
            for repo in cache_info.repos:
                if repo.repo_type == "model":
                    found_cache = True
                    row = ctk.CTkFrame(self.models_list_frame)
                    row.pack(fill="x", pady=2)
                    
                    # Use Repo ID
                    is_active = (self.current_model == repo.repo_id)
                    
                    name_label = ctk.CTkLabel(row, text=repo.repo_id)
                    name_label.pack(side="left", padx=5)
                    
                    if is_active:
                        status_badge = ctk.CTkLabel(row, text="● ACTIVE", text_color="#28a745", font=("Arial", 10, "bold"))
                        status_badge.pack(side="left", padx=10)
                        name_label.configure(text_color="#28a745")
                    else:
                        status_badge = ctk.CTkLabel(row, text="○ UNLOADED", text_color="gray", font=("Arial", 10))
                        status_badge.pack(side="left", padx=10)

                    load_btn = ctk.CTkButton(row, text="Load", width=60, command=lambda mid=repo.repo_id: self.load_local_model(mid))
                    load_btn.pack(side="right", padx=5)
                    if is_active:
                        load_btn.configure(state="disabled", text="Active", fg_color="#2b2b2b")
                    
                    if hasattr(repo, 'repo_path'):
                         ctk.CTkButton(row, text="Uninstall", width=70, fg_color="#ff4444", hover_color="#cc0000", 
                                     command=lambda p=repo.repo_path, n=repo.repo_id: self.delete_model_dialog(p, n)).pack(side="right", padx=5)
            
            if not found_cache:
                ctk.CTkLabel(self.models_list_frame, text="No cached models found.").pack(pady=2, anchor="w", padx=10)
                
        except Exception as e:
            ctk.CTkLabel(self.models_list_frame, text=f"Error scanning cache: {e}").pack(pady=2)

    def delete_model_dialog(self, path, name):
        # Confirm delete
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Delete {name}?")
        dialog.geometry("350x150")
        
        ctk.CTkLabel(dialog, text=f"Permanently delete {name}?", font=("Arial", 12, "bold")).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="Delete", fg_color="#ff4444", hover_color="#cc0000", command=lambda: confirm()).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=10)
        
        def confirm():
            dialog.destroy()
            threading.Thread(target=self._perform_delete, args=(path, name)).start()

    def _perform_delete(self, path, name):
         try:
            # Check if active (simple heuristic)
            path_str = str(path)
            if self.current_model:
                clean_current = self.current_model.replace("/", "--")
                if clean_current in path_str:
                     self.root.after(0, lambda: self.add_to_history(f"System: Cannot delete active model {name}. Load another model first.\n"))
                     return

            if os.path.exists(path):
                # Helper for windows read-only files
                def remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                    
                shutil.rmtree(path, onerror=remove_readonly)
                self.root.after(0, lambda: self.add_to_history(f"System: Deleted model {name}.\n"))
                self.root.after(0, self.refresh_installed_models)
            else:
                 self.root.after(0, lambda: self.add_to_history(f"System: Path not found: {path}\n"))

         except Exception as e:
                err_text = f"System: Failed to delete model: {e}\n"
                self.root.after(0, lambda: self.add_to_history(err_text))

    def quick_search(self, query):
        self.model_search_entry.delete(0, 'end')
        self.model_search_entry.insert(0, query)
        self.search_models(query)

    def search_models(self, query=None):
        if query is None:
            query = self.model_search_entry.get().strip()
        
        # Sort logic
        sort_map = {
            "Most Downloaded": ("downloads", -1),
            "Best Rated": ("likes", -1),
            "Newest": ("lastModified", -1),
            "Oldest": ("lastModified", 1)
        }
        sort_key, sort_dir = sort_map.get(self.model_sort_var.get(), ("downloads", -1))
        
        # Clear list
        for widget in self.models_list_frame.winfo_children():
            widget.destroy()
            
        header = f"Results for '{query}'" if query else "Trending Models"
        header += f" ({self.model_sort_var.get()})"
        ctk.CTkLabel(self.models_list_frame, text=header, font=("Arial", 14, "bold")).pack(pady=5, anchor="w")
        
        def run_search():
            try:
                api = HfApi()
                # Search for text-generation models
                models = api.list_models(
                    filter="text-generation", 
                    search=query if query else None, 
                    limit=15, 
                    sort=sort_key, 
                    direction=sort_dir
                )
                
                self.root.after(0, lambda: self.display_search_results(models))
            except Exception as e:
                err_text = f"Error: {e}"
                self.root.after(0, lambda t=err_text: ctk.CTkLabel(self.models_list_frame, text=t).pack(pady=5))

        threading.Thread(target=run_search, daemon=True).start()

    def display_search_results(self, models):
        # Callback to display results on main thread
        for model in models:
            row = ctk.CTkFrame(self.models_list_frame)
            row.pack(fill="x", pady=2)
            
            # Simple layout: Model ID
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            is_active = (self.current_model == model.id)
            name_text = f"● {model.id}" if is_active else model.id
            name_color = "#28a745" if is_active else None
            
            ctk.CTkLabel(info_frame, text=name_text, font=("Arial", 12, "bold"), anchor="w", text_color=name_color).pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"Downloads: {model.downloads} | Likes: {model.likes}", font=("Arial", 10), text_color="gray", anchor="w").pack(fill="x")
            
            # Buttons frame
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=5)
            
            # Info button (i)
            ctk.CTkButton(btns, text="ⓘ", width=30, fg_color="#3b3b3b", hover_color="#4b4b4b", command=lambda mid=model.id: self.show_model_info(mid)).pack(side="left", padx=2)
            
            # Install button
            install_btn = ctk.CTkButton(btns, text="Install", width=80, command=lambda mid=model.id: self.install_model_dialog(mid))
            install_btn.pack(side="left", padx=2)
            
            if is_active:
                install_btn.configure(state="disabled", text="Active", fg_color="#2b2b2b")

    def show_model_info(self, repo_id):
        # Fetch detailed info
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Model Info: {repo_id}")
        dialog.geometry("500x400")
        
        loading_label = ctk.CTkLabel(dialog, text="Fetching info from Hugging Face...")
        loading_label.pack(pady=50)
        
        def run_fetch():
            try:
                api = HfApi()
                info = api.model_info(repo_id)
                
                # Estimate size
                size_str = "Unknown"
                if info.siblings:
                    total_bytes = sum(s.size for s in info.siblings if s.size)
                    if total_bytes:
                        size_str = f"{total_bytes / (1024**3):.2f} GB"
                
                tags = ", ".join(info.tags[:10]) if info.tags else "None"
                
                details = f"ID: {info.id}\n"
                details += f"Author: {info.author}\n"
                details += f"Downloads: {info.downloads}\n"
                details += f"Likes: {info.likes}\n"
                details += f"Estimated Size: {size_str}\n"
                details += f"Last Modified: {info.lastModified}\n\n"
                details += f"Tags: {tags}\n"
                
                self.root.after(0, lambda: self._display_info(dialog, loading_label, details))
            except Exception as e:
                self.root.after(0, lambda: loading_label.configure(text=f"Error: {e}"))

        threading.Thread(target=run_fetch, daemon=True).start()

    def _display_info(self, dialog, loading_label, details):
        loading_label.destroy()
        
        txt = ctk.CTkTextbox(dialog, width=460, height=300)
        txt.pack(pady=10, padx=10)
        txt.insert("0.0", details)
        txt.configure(state="disabled")
        
        ctk.CTkButton(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def install_model_dialog(self, repo_id):
        # Confirm install
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Install {repo_id}")
        dialog.geometry("400x200")
        
        ctk.CTkLabel(dialog, text=f"Install {repo_id}?", font=("Arial", 12, "bold")).pack(pady=20)
        ctk.CTkLabel(dialog, text="This will download the full model repository.\nEnsure you have enough disk space.", text_color="orange").pack(pady=5)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Install", command=lambda: start_install()).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="red", command=dialog.destroy).pack(side="left", padx=10)
        
        def start_install():
            dialog.destroy()
            self.install_model(repo_id)

    def install_model(self, repo_id):
        # Create progress popup
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("Downloading Model")
        progress_window.geometry("400x150")
        progress_window.attributes('-topmost', True)
        
        ctk.CTkLabel(progress_window, text=f"Downloading {repo_id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        p_bar = ctk.CTkProgressBar(progress_window, width=350)
        p_bar.pack(pady=10)
        p_bar.set(0)
        
        status_label = ctk.CTkLabel(progress_window, text="Starting download...")
        status_label.pack(pady=5)

        # Background install
        def run_install():
            try:
                models_dir = os.path.join(self.data_dir, 'models')
                folder_name = repo_id.replace("/", "--")
                target_dir = os.path.join(models_dir, folder_name)
                
                # Mock progress since snapshot_download doesn't have a simple hook
                # We'll use a thread that checks folder size vs estimated size? 
                # Better: Just pulse the bar for now or use a custom tqdm
                
                p_bar.configure(mode="indeterminate")
                p_bar.start()
                
                snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
                
                p_bar.stop()
                p_bar.configure(mode="determinate")
                p_bar.set(1.0)
                
                self.root.after(0, lambda: status_label.configure(text="Download Complete!"))
                self.root.after(0, lambda: self.add_to_history(f"System: Successfully installed {repo_id}.\n"))
                time.sleep(1)
                self.root.after(0, progress_window.destroy)
                self.root.after(0, self.refresh_installed_models)
            except Exception as e:
                p_bar.stop()
                err_text = f"System: Install failed: {e}\n"
                self.root.after(0, lambda: self.add_to_history(err_text))
                self.root.after(0, lambda: status_label.configure(text="Error occurred!"))

        threading.Thread(target=run_install, daemon=True).start()

    def load_local_model(self, path_or_id):
        self.add_to_history(f"System: Switching to model {path_or_id}...\n")
        
        def switch():
            # Pass directly to Orion's load_model which handles both paths and IDs
            success = self.orion.load_model(path_or_id)
            if success:
                self.root.after(0, lambda: self.add_to_history(f"System: Loaded successfully.\n"))
                self.current_model = path_or_id
            else:
                 self.root.after(0, lambda: self.add_to_history(f"System: Failed to load.\n"))
                 
        threading.Thread(target=switch, daemon=True).start()

    def import_local_folder(self):
        source_dir = filedialog.askdirectory(title="Select Transformers Model Folder")
        if not source_dir:
            return
            
        # Basic check for model files
        if not os.path.exists(os.path.join(source_dir, "config.json")):
            self.add_to_history("System: Selected folder does not appear to be a Transformers model (missing config.json).\n")
            return
            
        # Target folder name
        folder_name = os.path.basename(source_dir)
        target_dir = os.path.join(self.data_dir, 'models', folder_name)
        
        if os.path.exists(target_dir):
            self.add_to_history(f"System: Model '{folder_name}' already exists in .orion/models.\n")
            return
            
        self.add_to_history(f"System: Importing {folder_name}... (This may take a moment)\n")
        
        def run_copy():
            try:
                import shutil
                shutil.copytree(source_dir, target_dir)
                self.root.after(0, lambda: self.add_to_history(f"System: Successfully imported {folder_name}.\n"))
                self.root.after(0, self.refresh_installed_models)
            except Exception as e:
                err_text = f"System: Import failed: {e}\n"
                self.root.after(0, lambda: self.add_to_history(err_text))
        
        threading.Thread(target=run_copy, daemon=True).start()

    def send_message(self):
        user_input = self.input_field.get().strip()
        if user_input:
            # Create new chat if none exists
            if self.current_chat_id is None:
                self.create_new_chat()

            self.add_to_history(f"You: {user_input}\n")
            self.input_field.delete(0, "end")

            # Generate auto-title if this is the first user message
            user_msg_count = sum(1 for msg in self.chat_history_data if msg.startswith("You: "))
            if user_msg_count == 1:
                threading.Thread(target=self.generate_auto_title, args=(self.current_chat_id, user_input), daemon=True).start()

            # Capture screen if vision enabled
            image_data = None
            if self.orion.vision_enabled:
                try:
                    screenshot = ImageGrab.grab()
                    buffered = BytesIO()
                    screenshot.save(buffered, format="PNG")
                    image_data = buffered.getvalue()
                    self.add_to_history("System: Screen captured for vision analysis.\n")
                except Exception as e:
                    err_text = f"System: Failed to capture screen: {e}\n"
                    self.add_to_history(err_text)

            # Show thinking frame if enabled
            if self.thinking_var.get():
                self.thinking_frame.pack(before=self.input_frame, pady=5)
                self.progress_bar.set(0)

            # Disable input while processing
            self.input_field.configure(state="disabled")
            
            # Change Send button to Cancel
            self.send_button.configure(text="Cancel", command=self.cancel_generation, fg_color="red")
            self.generation_cancelled = False

            # Start response generation in a thread
            threading.Thread(target=self.generate_response, args=(user_input, image_data), daemon=True).start()

    def generate_auto_title(self, chat_id, user_text):
        title = self.orion.generate_title(user_text)

        if title:
            try:
                # Update chat file
                # Wait briefly to ensure file is created/accessible
                time.sleep(1)
                
                filepath = os.path.join(self.data_dir, f"chat_{chat_id}.dat")
                if os.path.exists(filepath):
                    chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
                    
                    chat_data['custom_title'] = title
                    
                    self._save_chat_data(f"chat_{chat_id}.dat", chat_data)
                    
                    self.root.after(0, self.refresh_chat_list)
            except Exception as e:
                print(f"Title saving failed: {e}")

    def cancel_generation(self):
        self.generation_cancelled = True
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.thinking_frame.pack_forget()
        self.input_field.configure(state="normal")
        self.send_button.configure(text="Send", command=self.send_message, fg_color=["#3B8ED0", "#1F6AA5"])
        self.input_field.focus()
        self.add_to_history("System: Generation cancelled.\n")

    def add_to_history(self, text, animate=False):
        # Determine if it's user or Orion message
        if text.startswith("You: "):
            sender = "user"
            message = text[5:].strip()
        elif text.startswith("Orion: "):
            sender = "orion"
            message = text[7:].strip()
        else:
            sender = "system"
            message = text.strip()

        # Store in history data first to get index
        index = len(self.chat_history_data)
        self.chat_history_data.append(text)

        # Create message bubble with index
        self.create_message_bubble(sender, message, index, animate)

    def create_message_bubble(self, sender, message, index, animate=False):
        # Create a frame for the bubble
        bubble_frame = ctk.CTkFrame(self.chat_history, fg_color="transparent")
        bubble_frame.pack(fill="x", padx=10, pady=5)

        # Check if message contains image URL
        if sender == "orion" and message.startswith("IMAGE_URL: "):
            # Extract URL and display image
            image_url = message[11:].strip()  # Remove "IMAGE_URL: " prefix
            self.display_image_bubble(bubble_frame, image_url, index)
        else:
            # Create the message label
            if sender == "user":
                # User message: right-aligned, blue background
                msg_label = ctk.CTkLabel(bubble_frame, text=message, fg_color="#0078D4", text_color="white", corner_radius=10, wraplength=400, justify="left")
                msg_label.pack(side="right", padx=10, pady=5)
                # Bind right-click to show context menu
                msg_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))
            elif sender == "orion":
                # Orion message: left-aligned, gray background
                msg_label = ctk.CTkLabel(bubble_frame, text="" if animate else message, fg_color="#E1E1E1", text_color="black", corner_radius=10, wraplength=400, justify="left")
                msg_label.pack(side="left", padx=10, pady=5)
                # Bind right-click to show context menu
                msg_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))

                if animate:
                    # Store animation state and full text on the label widget itself
                    msg_label.is_animating = True
                    msg_label.full_text = message
                    # Bind left-click to stop the animation
                    msg_label.bind("<Button-1>", lambda event, label=msg_label: self.stop_animation(label))
                    self.animate_typing(msg_label, message)
            else:
                # System message: centered, light gray
                msg_label = ctk.CTkLabel(bubble_frame, text=message, fg_color="#F3F3F3", text_color="gray", corner_radius=5, wraplength=400, justify="center")
                msg_label.pack(anchor="center", padx=10, pady=5)
                # Bind right-click to show context menu
                msg_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))

    def animate_typing(self, label, text, index=0):
        try:
            # Stop if the widget is destroyed or the animation flag is set to False
            if not label.winfo_exists() or not getattr(label, 'is_animating', False):
                return

            if index < len(text):
                # Dynamic chunk size for speed
                chunk = 1
                if len(text) > 200: 
                    chunk = 3
                if len(text) > 500: 
                    chunk = 5

                next_index = min(index + chunk, len(text))
                current_text = text[:next_index]

                label.configure(text=current_text + "█")
                self.root.after(self.typing_speed_var.get(), lambda: self.animate_typing(label, text, next_index))
            else:
                # Animation finished
                label.configure(text=text)
                if hasattr(label, 'is_animating'):
                    label.is_animating = False
                label.unbind("<Button-1>")  # Unbind click once done
        except Exception:
            # This can happen if the window is closed during animation
            pass

    def stop_animation(self, label):
        # Check if the label is still animating
        if hasattr(label, 'is_animating') and label.is_animating:
            label.is_animating = False  # Set flag to stop the 'after' loop
            label.configure(text=label.full_text)  # Set the full text immediately
            label.unbind("<Button-1>")  # Unbind the click event

    def display_image_bubble(self, bubble_frame, image_url, index):
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Open image with PIL
            image = Image.open(BytesIO(response.content))

            # Resize image to fit in chat (max width 400, maintain aspect ratio)
            max_width = 400
            width, height = image.size
            if width > max_width:
                ratio = max_width / width
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                new_width = width
                new_height = height

            # Create CTkImage
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(new_width, new_height))

            # Create label with image
            image_label = ctk.CTkLabel(bubble_frame, image=ctk_image, text="")
            image_label.pack(side="left", padx=10, pady=5)

            # Add URL as text below image
            url_label = ctk.CTkLabel(bubble_frame, text=f"Image: {image_url}", fg_color="#E1E1E1", text_color="blue", corner_radius=5, wraplength=400, justify="left", cursor="hand2")
            url_label.pack(side="left", padx=10, pady=(0, 5))

            # Make URL clickable
            url_label.bind("<Button-1>", lambda e: webbrowser.open(image_url))

            # Bind right-click to show context menu on image
            image_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))
            url_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))

        except Exception as e:
            # If image fails to load, show error message
            error_label = ctk.CTkLabel(bubble_frame, text=f"Failed to load image: {str(e)}", fg_color="#E1E1E1", text_color="red", corner_radius=10, wraplength=400, justify="left")
            error_label.pack(side="left", padx=10, pady=5)
            # Bind right-click to show context menu
            error_label.bind("<Button-3>", lambda event, idx=index: self.show_message_context_menu(event, idx))

    def generate_response(self, user_input, image_data=None):
        # Check for cold start (Ollama keeps models for 5 mins by default)
        current_time = time.time()
        if current_time - self.last_interaction_time > 300:  # 5 minutes
            self.root.after(0, lambda: self.thinking_label.configure(text="Warming up AI... (This may take a moment)"))
        else:
            self.root.after(0, lambda: self.thinking_label.configure(text="Orion is thinking..."))

        # Start indeterminate animation to fix freezing UI
        self.root.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
        self.root.after(0, self.progress_bar.start)

        # Update system prompt in Orion instance
        self.orion.system_prompt = self.system_prompt

        # Update Ollama model in Orion instance
        self.orion.ollama_model = self.ollama_model_var.get()

        # Get response with current model
        response = self.orion.get_response(user_input, self.current_model, image_data)

        if self.generation_cancelled:
            return

        # Use after() to update UI from the main thread
        self.root.after(0, lambda: self.show_response(response))

    def toggle_sidebar(self):
        if self.sidebar_collapsed:
            # Expand sidebar
            self.sidebar_frame.pack(side="left", fill="y", padx=(0, 5))
            self.sidebar_toggle.configure(text="☰")
            self.sidebar_collapsed = False
        else:
            # Collapse sidebar
            self.sidebar_frame.pack_forget()
            self.sidebar_toggle.configure(text="☰")
            self.sidebar_collapsed = True

    def load_chat(self, chat_id):
        # Load chat from file
        try:
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
            self.current_chat_id = chat_id
            self.chat_history_data = chat_data['history']

            # Clear existing bubbles
            for widget in self.chat_history.winfo_children():
                widget.destroy()

            # Recreate bubbles from history without duplicating data
            for index, message_text in enumerate(self.chat_history_data):
                # Determine sender and message
                if message_text.startswith("You: "):
                    sender = "user"
                    message = message_text[5:].strip()
                elif message_text.startswith("Orion: "):
                    sender = "orion"
                    message = message_text[7:].strip()
                else:
                    sender = "system"
                    message = message_text.strip()

                # Create message bubble with correct index
                self.create_message_bubble(sender, message, index)
        except FileNotFoundError:
            self.add_to_history(f"Orion: Chat {chat_id} not found.\n")

    def show_response(self, response):
        # Hide thinking frame and show response
        if self.thinking_var.get():
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.thinking_frame.pack_forget()
            
        self.last_interaction_time = time.time()
            
        # Handle special commands
        if response == "Chat history cleared.":
            # Clear existing bubbles
            for widget in self.chat_history.winfo_children():
                widget.destroy()
            self.chat_history_data = []
            self.add_to_history("Orion: Chat history cleared.\n")
        elif response == "Exiting...":
            self.root.destroy()
        else:
            self.add_to_history(f"Orion: {response}\n", animate=self.thinking_var.get())

        # Play sound notification if enabled
        if self.sound_var.get():
            winsound.Beep(800, 200)  # Frequency 800Hz, duration 200ms

        # Save chat automatically
        if self.current_chat_id is not None:
            self.save_chat()

        # Re-enable input
        self.input_field.configure(state="normal")
        self.send_button.configure(state="normal", text="Send", command=self.send_message, fg_color=["#3B8ED0", "#1F6AA5"])
        self.input_field.focus()

    def create_new_chat(self):
        # Clear search so new chat is visible
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, "end")
        # Generate new chat ID
        chat_id = int(time.time())
        self.current_chat_id = chat_id
        self.chat_history_data = []
        # Clear existing bubbles
        for widget in self.chat_history.winfo_children():
            widget.destroy()
        # Add initial message
        self.add_to_history(f"Orion: {self.startup_greeting_var.get()}\n")
        # Refresh chat list
        self.refresh_chat_list()

    def share_chat(self, chat_id):
        try:
            # Load chat data
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".orion",
                filetypes=[("Orion Chat File", "*.orion")],
                title="Share Chat (Orion Format)"
            )
            
            if filename:
                # Create export structure with magic header
                export_data = {
                    "magic": "ORION_CHAT_EXPORT",
                    "version": self.orion.model_version,
                    "timestamp": time.time(),
                    "data": chat_data
                }
                
                with open(filename, "wb") as f:
                    pickle.dump(export_data, f)
                
                self.add_to_history(f"System: Chat shared to {os.path.basename(filename)}\n")
        except Exception as e:
            self.add_to_history(f"System: Error sharing chat: {str(e)}\n")

    def import_chat_file(self):
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("Orion Chat File", "*.orion")],
                title="Import Orion Chat"
            )
            
            if filename:
                self.import_chat_from_path(filename)
        except Exception as e:
            self.add_to_history(f"System: Error importing chat: {str(e)}\n")

    def import_chat_from_path(self, filename):
        try:
            with open(filename, "rb") as f:
                export_data = pickle.load(f)
            
            # Verify magic header
            if isinstance(export_data, dict) and export_data.get("magic") == "ORION_CHAT_EXPORT":
                chat_data = export_data["data"]
                
                # Create new chat ID
                new_chat_id = int(time.time())
                
                # Clear search so imported chat is visible
                if hasattr(self, 'search_entry'):
                    self.search_entry.delete(0, "end")

                # Save as local chat
                self._save_chat_data(f"chat_{new_chat_id}.dat", chat_data)
                
                self.refresh_chat_list()
                self.load_chat(new_chat_id)
                self.add_to_history("System: Chat imported successfully.\n")
            else:
                self.add_to_history("System: Invalid Orion chat file format.\n")
        except Exception as e:
            self.add_to_history(f"System: Error importing chat: {str(e)}\n")

    def save_chat(self):
        if self.current_chat_id is not None:
            # Try to load existing data to preserve metadata (title, pinned status)
            try:
                existing_data = self._load_chat_data(f"chat_{self.current_chat_id}.dat")
            except Exception:
                existing_data = {}

            chat_data = {
                'history': self.chat_history_data,
                'model': self.current_model,
                'timestamp': time.time(),
                'custom_title': existing_data.get('custom_title'),
                'pinned': existing_data.get('pinned', False)
            }
            # Clean up None values if keys didn't exist
            if chat_data['custom_title'] is None:
                del chat_data['custom_title']

            self._save_chat_data(f"chat_{self.current_chat_id}.dat", chat_data)

    def refresh_chat_list(self):
        # Get filter text
        filter_text = self.search_entry.get().lower() if hasattr(self, 'search_entry') else ""

        # Clear existing buttons
        for widget in self.chat_list.winfo_children():
            widget.destroy()

        # Find all chat files
        chat_files = [f for f in os.listdir(self.data_dir) if f.startswith('chat_') and f.endswith('.dat')]
        
        # Load chat metadata for sorting
        chats = []
        for chat_file in chat_files:
            chat_id = int(chat_file.split('_')[1].split('.')[0])
            try:
                chat_data = self._load_chat_data(chat_file)
                chats.append({'id': chat_id, 'data': chat_data})
            except Exception:
                pass

        # Sort: Pinned first (True > False), then by timestamp (descending)
        chats.sort(key=lambda x: (x['data'].get('pinned', False), x['data'].get('timestamp', 0)), reverse=True)

        for chat in chats:
            chat_id = chat['id']
            chat_data = chat['data']
            try:
                # Get title - use custom title if available, otherwise first user message
                title = chat_data.get('custom_title', "New Chat")
                if title == "New Chat":
                    for msg in chat_data['history']:
                        if msg.startswith("You: "):
                            title = msg[5:].strip()[:30] + "..." if len(msg[5:].strip()) > 30 else msg[5:].strip()
                            break
                
                # Filter by title
                if filter_text and filter_text not in title.lower():
                    continue

                # Add pin indicator
                if chat_data.get('pinned', False):
                    title = "📌 " + title

                chat_button = ctk.CTkButton(self.chat_list, text=title, command=lambda cid=chat_id: self.load_chat(cid))
                chat_button.pack(fill="x", pady=2)

                # Bind right-click to show context menu
                chat_button.bind("<Button-3>", lambda event, cid=chat_id: self.show_chat_context_menu(event, cid))

                # Bind double-click to rename
                chat_button.bind("<Double-Button-1>", lambda event, cid=chat_id: self.rename_chat(cid))
            except Exception:
                pass  # Skip corrupted files

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme.lower())
        self.add_to_history(f"Orion: Theme changed to {theme}.\n")

    def adjust_font_size(self, delta):
        new_size = self.font_size_var.get() + delta
        if 8 <= new_size <= 24:
            self.font_size_var.set(new_size)
            # Apply font size to chat history (simplified - would need more work for full implementation)
            self.add_to_history(f"Orion: Font size changed to {new_size}.\n")

    def export_chat_history(self):
        try:
            # Create export file
            export_file = f"chat_export_{int(time.time())}.txt"
            with open(export_file, "w") as f:
                f.write("Orion Chat History Export\n")
                f.write("=" * 50 + "\n\n")

                chat_files = [f for f in os.listdir(self.data_dir) if f.startswith('chat_') and f.endswith('.dat')]
                for chat_file in chat_files:
                    try:
                        chat_data = self._load_chat_data(chat_file)
                        f.write(f"Chat ID: {chat_file}\n")
                        f.write(f"Model: {chat_data.get('model', 'Unknown')}\n")
                        f.write(f"Timestamp: {time.ctime(chat_data.get('timestamp', 0))}\n")
                        f.write("-" * 30 + "\n")
                        for msg in chat_data['history']:
                            f.write(msg)
                        f.write("\n\n")
                    except Exception:
                        continue

            self.add_to_history(f"Orion: Chat history exported to {export_file}.\n")
        except Exception as e:
            self.add_to_history(f"Orion: Error exporting chat history: {str(e)}\n")

    def clear_all_chats(self):
        # Confirmation dialog would be better, but for simplicity:
        chat_files = [f for f in os.listdir(self.data_dir) if f.startswith('chat_') and f.endswith('.dat')]
        deleted_count = 0
        for chat_file in chat_files:
            try:
                os.remove(os.path.join(self.data_dir, chat_file))
                deleted_count += 1
            except Exception:
                pass

        self.refresh_chat_list()
        self.add_to_history(f"Orion: Cleared {deleted_count} chat files.\n")

    def check_model_status(self):
        self.model_status_label.configure(text="Checking...", text_color="orange")
        threading.Thread(target=self._check_models_thread, daemon=True).start()

    def _check_models_thread(self):
        import ollama
        models = ['gemma3:1b', 'llama3', 'llama2', 'mistral', 'codellama', 'wizardlm2:latest', 'tinyllama', 'qwen:0.5b']
        available_models = []
        unavailable_models = []

        try:
            # Check if Ollama is running
            ollama.list()
        except Exception:
            def show_error():
                try:
                    if self.model_status_label.winfo_exists():
                        self.model_status_label.configure(text="Error: Ollama is not running.\nPlease start the Ollama app.", text_color="red")
                        self.install_button.configure(state="disabled")
                except Exception:
                    pass
            self.root.after(0, show_error)
            return

        for model in models:
            try:
                # Quick test - just check if model exists
                ollama.show(model)
                available_models.append(model)
            except Exception:
                unavailable_models.append(model)

        self.root.after(0, lambda: self._update_model_status_ui(available_models, unavailable_models))

    def _update_model_status_ui(self, available_models, unavailable_models):
        try:
            if not self.model_status_label.winfo_exists():
                return
        except Exception:
            return

        # Update status label
        if available_models:
            status_text = f"Available: {', '.join(available_models)}"
            if unavailable_models:
                status_text += f"\nNot installed: {', '.join(unavailable_models)}"
            self.model_status_label.configure(text=status_text, text_color="green")
        else:
            self.model_status_label.configure(text="No models available", text_color="red")

        # Update model selector to only show available models
        if available_models:
            if self.ollama_model_var.get() not in available_models:
                self.ollama_model_var.set(available_models[0])  # Set to first available model

        # Enable/disable install button based on unavailable models
        if unavailable_models:
            self.install_button.configure(state="normal")
            self.unavailable_models = unavailable_models  # Store for install function
        else:
            self.install_button.configure(state="disabled")
            self.unavailable_models = []

    def install_missing_models(self):
        if not hasattr(self, 'unavailable_models') or not self.unavailable_models:
            self.add_to_history("Orion: No missing models to install.\n")
            return

        # Create selection window
        selection_window = ctk.CTkToplevel(self.root)
        selection_window.title("Select Models")
        selection_window.geometry("350x400")
        selection_window.resizable(False, False)
        selection_window.transient(self.root)
        selection_window.grab_set()

        ctk.CTkLabel(selection_window, text="Select models to install:", font=("Arial", 14, "bold")).pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(selection_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        check_vars = {}
        for model in self.unavailable_models:
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(scroll_frame, text=model, variable=var).pack(anchor="w", pady=5)
            check_vars[model] = var

        def on_confirm():
            selected = [m for m, v in check_vars.items() if v.get()]
            selection_window.destroy()
            if selected:
                self._perform_model_installation(selected)

        btn_frame = ctk.CTkFrame(selection_window)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="Install", command=on_confirm).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(btn_frame, text="Cancel", command=selection_window.destroy, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right", padx=5, expand=True)

    def _perform_model_installation(self, models_to_install):
        # Ask user to select installation directory
        install_path = filedialog.askdirectory(title="Select Installation Directory for Models")

        if not install_path:
            self.add_to_history("Orion: Installation cancelled.\n")
            return

        # Save original button color
        self.original_button_color = self.install_button.cget("fg_color")

        # Setup cancellation flag
        self.install_cancelled = False

        # Configure button for cancellation
        self.install_button.configure(state="normal", text="Cancel Installation", command=self.cancel_installation, fg_color="red")

        # Install models in a thread to avoid blocking UI
        def install_thread():
            import ollama
            # Set custom models directory
            original_models_env = os.environ.get('OLLAMA_MODELS')
            os.environ['OLLAMA_MODELS'] = install_path

            installed = []
            failed = []

            try:
                for model in models_to_install:
                    if self.install_cancelled:
                        break

                    try:
                        self.root.after(0, lambda m=model: self.add_to_history(f"Orion: Installing {m} to {install_path}...\n"))
                        
                        # Use stream=True to get progress
                        for progress in ollama.pull(model, stream=True):
                            if self.install_cancelled:
                                raise Exception("Installation cancelled by user")
                            
                            status = progress.get('status', '')
                            
                            # Update progress if downloading
                            if 'total' in progress and 'completed' in progress:
                                total = progress['total']
                                completed = progress['completed']
                                percent = (completed / total) * 100
                                
                                # Format size
                                total_gb = total / (1024**3)
                                completed_gb = completed / (1024**3)
                                
                                status_msg = f"Installing {model}: {status} - {percent:.1f}% ({completed_gb:.2f}GB / {total_gb:.2f}GB)"
                                self.root.after(0, lambda msg=status_msg: self.model_status_label.configure(text=msg, text_color="blue"))
                            else:
                                self.root.after(0, lambda msg=f"Installing {model}: {status}": self.model_status_label.configure(text=msg, text_color="blue"))

                        installed.append(model)
                        self.root.after(0, lambda m=model: self.add_to_history(f"Orion: Successfully installed {m}.\n"))
                    except Exception as e:
                        if str(e) == "Installation cancelled by user":
                            self.root.after(0, lambda: self.add_to_history("Orion: Installation cancelled by user.\n"))
                            break
                        failed.append(model)
                        self.root.after(0, lambda m=model, e=str(e): self.add_to_history(f"Orion: Failed to install {m}: {e}\n"))
            finally:
                # Restore original environment
                if original_models_env is not None:
                    os.environ['OLLAMA_MODELS'] = original_models_env
                else:
                    os.environ.pop('OLLAMA_MODELS', None)

            # Update UI after installation
            def restore_ui():
                self.install_button.configure(state="normal", text="Install Missing Models", command=self.install_missing_models, fg_color=self.original_button_color)
                self.check_model_status()

            self.root.after(0, restore_ui)

            if installed:
                self.root.after(0, lambda: self.add_to_history(f"Orion: Installed {len(installed)} model(s) to {install_path}. Re-check status to update.\n"))
            if failed and not self.install_cancelled:
                self.root.after(0, lambda: self.add_to_history(f"Orion: Failed to install {len(failed)} model(s).\n"))

        threading.Thread(target=install_thread, daemon=True).start()

    def cancel_installation(self):
        self.install_cancelled = True
        self.install_button.configure(state="disabled", text="Cancelling...")

    def save_settings(self):
        # UI settings only now
        settings = {
            'current_model': self.current_model,
            'theme': ctk.get_appearance_mode(),
            'font_size': self.font_size_var.get(),
            'auto_save': self.auto_save_var.get(),
            'sound_notifications': self.sound_var.get(),
            'thinking_animation': self.thinking_var.get(),
            'typing_speed': self.typing_speed_var.get(),
            'strict_mode': self.strict_mode_var.get(),
            'startup_greeting': self.startup_greeting_var.get()
        }

        # Apply settings immediately
        self.orion.strict_mode = self.strict_mode_var.get()

        try:
            with open(os.path.join(self.data_dir, 'orion_settings.json'), 'w') as f:
                json.dump(settings, f, indent=4)
            self.add_to_history(f"Orion: Settings saved.\n"
                                f"• Interface: {self.current_model}\n"
                                f"• Speed: {self.typing_speed_var.get()}ms\n"
                                f"• Animation: {'On' if self.thinking_var.get() else 'Off'}\n")
        except Exception as e:
            self.add_to_history(f"Orion: Error saving settings: {str(e)}\n")

    def show_chat_context_menu(self, event, chat_id):
        # Create context menu
        context_menu = Menu(self.root, tearoff=0)

        # Check pinned status
        is_pinned = False
        try:
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
            is_pinned = chat_data.get('pinned', False)
        except Exception:
            pass

        # Pin/Unpin option
        context_menu.add_command(label="Unpin" if is_pinned else "Pin", command=lambda: self.toggle_pin(chat_id))

        # Share option
        context_menu.add_command(label="Share", command=lambda: self.share_chat(chat_id))

        # Export option
        context_menu.add_command(label="Export", command=lambda: self.export_single_chat(chat_id))

        # Rename option
        context_menu.add_command(label="Rename", command=lambda: self.rename_chat(chat_id))

        # Delete option
        context_menu.add_command(label="Delete", command=lambda: self.delete_chat(chat_id))

        # Show menu at mouse position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def toggle_pin(self, chat_id):
        try:
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
            chat_data['pinned'] = not chat_data.get('pinned', False)
            self._save_chat_data(f"chat_{chat_id}.dat", chat_data)
            self.refresh_chat_list()
        except Exception as e:
            self.add_to_history(f"System: Error toggling pin: {str(e)}\n")

    def export_single_chat(self, chat_id):
        try:
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")

            # Create export file
            export_file = f"chat_export_{chat_id}_{int(time.time())}.txt"
            with open(export_file, "w") as f:
                f.write("Orion Chat Export\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Chat ID: {chat_id}\n")
                f.write(f"Model: {chat_data.get('model', 'Unknown')}\n")
                f.write(f"Timestamp: {time.ctime(chat_data.get('timestamp', 0))}\n")
                f.write("-" * 30 + "\n")
                for msg in chat_data['history']:
                    f.write(msg)
                f.write("\n")

            self.add_to_history(f"Orion: Chat exported to {export_file}.\n")
        except Exception as e:
            self.add_to_history(f"Orion: Error exporting chat: {str(e)}\n")

    def rename_chat(self, chat_id):
        # Create a simple dialog for renaming
        rename_window = ctk.CTkToplevel(self.root)
        rename_window.title("Rename Chat")
        rename_window.geometry("300x150")
        rename_window.resizable(False, False)

        # Get current title
        try:
            chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
            current_title = chat_data.get('custom_title', "New Chat")
            if current_title == "New Chat":
                for msg in chat_data['history']:
                    if msg.startswith("You: "):
                        current_title = msg[5:].strip()[:30] + "..." if len(msg[5:].strip()) > 30 else msg[5:].strip()
                        break
        except Exception:
            current_title = "New Chat"

        label = ctk.CTkLabel(rename_window, text="Enter new chat name:")
        label.pack(pady=10)

        entry = ctk.CTkEntry(rename_window, width=250)
        entry.insert(0, current_title)
        entry.pack(pady=5)

        def save_rename():
            new_title = entry.get().strip()
            if new_title:
                try:
                    chat_data = self._load_chat_data(f"chat_{chat_id}.dat")
                    chat_data['custom_title'] = new_title
                    self._save_chat_data(f"chat_{chat_id}.dat", chat_data)
                    self.refresh_chat_list()
                    self.add_to_history(f"Orion: Chat renamed to '{new_title}'.\n")
                except Exception as e:
                    self.add_to_history(f"Orion: Error renaming chat: {str(e)}\n")
            rename_window.destroy()

        button_frame = ctk.CTkFrame(rename_window)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=save_rename)
        save_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=rename_window.destroy)
        cancel_button.pack(side="right", padx=5)

    def delete_chat(self, chat_id):
        # Confirmation dialog
        confirm_window = ctk.CTkToplevel(self.root)
        confirm_window.title("Delete Chat")
        confirm_window.geometry("300x120")
        confirm_window.resizable(False, False)

        label = ctk.CTkLabel(confirm_window, text="Are you sure you want to delete this chat?")
        label.pack(pady=20)

        button_frame = ctk.CTkFrame(confirm_window)
        button_frame.pack(pady=10)

        def confirm_delete():
            try:
                os.remove(os.path.join(self.data_dir, f"chat_{chat_id}.dat"))
                # If this was the current chat, clear it
                if self.current_chat_id == chat_id:
                    self.current_chat_id = None
                    self.chat_history_data = []
                    # Clear all message bubbles from the scrollable frame
                    for widget in self.chat_history.winfo_children():
                        widget.destroy()
                self.refresh_chat_list()
                self.add_to_history("Orion: Chat deleted.\n")
            except Exception as e:
                self.add_to_history(f"Orion: Error deleting chat: {str(e)}\n")
            confirm_window.destroy()

        yes_button = ctk.CTkButton(button_frame, text="Yes", fg_color="red", command=confirm_delete)
        yes_button.pack(side="left", padx=5)

        no_button = ctk.CTkButton(button_frame, text="No", command=confirm_window.destroy)
        no_button.pack(side="right", padx=5)

    def load_settings(self):
        try:
            with open(os.path.join(self.data_dir, 'orion_settings.json'), 'r') as f:
                settings = json.load(f)

            # Apply loaded settings with validation
            if isinstance(settings, dict):
                self.current_model = settings.get('current_model', "Basic (1.3)")
                ctk.set_appearance_mode(settings.get('theme', 'System'))
                self.font_size_var.set(max(8, min(24, settings.get('font_size', 12))))
                self.ollama_model_var.set(settings.get('ollama_model', 'gemma3:1b'))
                self.temp_var.set(max(0.0, min(1.0, settings.get('temperature', 0.7))))
                self.tokens_var.set(max(100, min(2000, settings.get('max_tokens', 500))))
                self.auto_save_var.set(bool(settings.get('auto_save', True)))
                self.sound_var.set(bool(settings.get('sound_notifications', False)))
                self.thinking_var.set(bool(settings.get('thinking_animation', True)))
                self.typing_speed_var.set(int(settings.get('typing_speed', 15)))
                self.strict_mode_var.set(bool(settings.get('strict_mode', False)))
                self.startup_greeting_var.set(settings.get('startup_greeting', "Hello! I am Orion, an AI chatbot created by OmniNode. How can I help you today?"))
                self.system_prompt = settings.get('system_prompt', "")
                
                # Sync with Orion instance
                self.orion.ollama_model = self.ollama_model_var.get()
                self.orion.strict_mode = self.strict_mode_var.get()
            else:
                raise ValueError("Invalid settings format")

        except FileNotFoundError:
            # No settings file exists, use defaults
            pass
        except Exception as e:
            self.add_to_history(f"Orion: Error loading settings: {str(e)}\n")

    def show_message_context_menu(self, event, index):
        # Create context menu for messages
        context_menu = Menu(self.root, tearoff=0)

        # Copy option
        context_menu.add_command(label="Copy", command=lambda: self.copy_message(index))

        # Edit option (only for user messages)
        if self.chat_history_data[index].startswith("You: "):
            context_menu.add_command(label="Edit", command=lambda: self.edit_message(index))

        # Delete option
        context_menu.add_command(label="Delete", command=lambda: self.delete_message(index))

        # Show menu at mouse position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_message(self, index):
        # Copy message text to clipboard
        message = self.chat_history_data[index]
        if message.startswith("You: "):
            text = message[5:].strip()
        elif message.startswith("Orion: "):
            text = message[7:].strip()
        else:
            text = message.strip()

        # Use tkinter's clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.add_to_history("Orion: Message copied to clipboard.\n")

    def edit_message(self, index):
        # Only allow editing user messages
        if not self.chat_history_data[index].startswith("You: "):
            return

        # Create edit dialog
        edit_window = ctk.CTkToplevel(self.root)
        edit_window.title("Edit Message")
        edit_window.geometry("500x300")
        edit_window.resizable(False, False)

        label = ctk.CTkLabel(edit_window, text="Edit your message:")
        label.pack(pady=10)

        # Get current message text
        current_text = self.chat_history_data[index][5:].strip()

        text_box = ctk.CTkTextbox(edit_window, width=450, height=150)
        text_box.pack(pady=5)
        text_box.insert("1.0", current_text)

        def save_edit():
            new_text = text_box.get("1.0", "end").strip()
            if new_text and new_text != current_text:
                # Update message in history
                self.chat_history_data[index] = f"You: {new_text}\n"
                # Clear and recreate chat history
                for widget in self.chat_history.winfo_children():
                    widget.destroy()
                for idx, message_text in enumerate(self.chat_history_data):
                    if message_text.startswith("You: "):
                        sender = "user"
                        message = message_text[5:].strip()
                    elif message_text.startswith("Orion: "):
                        sender = "orion"
                        message = message_text[7:].strip()
                    else:
                        sender = "system"
                        message = message_text.strip()
                    self.create_message_bubble(sender, message, idx)
                # Save chat
                if self.current_chat_id is not None:
                    self.save_chat()
                self.add_to_history("Orion: Message edited.\n")
            edit_window.destroy()

        button_frame = ctk.CTkFrame(edit_window)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=save_edit)
        save_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=edit_window.destroy)
        cancel_button.pack(side="right", padx=5)

    def delete_message(self, index):
        # Confirmation dialog
        confirm_window = ctk.CTkToplevel(self.root)
        confirm_window.title("Delete Message")
        confirm_window.geometry("300x120")
        confirm_window.resizable(False, False)

        label = ctk.CTkLabel(confirm_window, text="Are you sure you want to delete this message?")
        label.pack(pady=20)

        button_frame = ctk.CTkFrame(confirm_window)
        button_frame.pack(pady=10)

        def confirm_delete():
            # Remove message from history
            del self.chat_history_data[index]

            # Clear and recreate chat history
            for widget in self.chat_history.winfo_children():
                widget.destroy()

            for message in self.chat_history_data:
                self.add_to_history(message)

            # Save chat
            if self.current_chat_id is not None:
                self.save_chat()

            self.add_to_history("Orion: Message deleted.\n")
            confirm_window.destroy()

        yes_button = ctk.CTkButton(button_frame, text="Yes", fg_color="red", command=confirm_delete)
        yes_button.pack(side="left", padx=5)

        no_button = ctk.CTkButton(button_frame, text="No", command=confirm_window.destroy)
        no_button.pack(side="right", padx=5)

    def toggle_vision(self):
        # Toggle vision state
        self.orion.vision_enabled = not self.orion.vision_enabled
        if self.orion.vision_enabled:
            self.vision_button.configure(fg_color="green", text="👁️")
            self.add_to_history("Orion: Vision enabled. I can now see your screen!\n")
        else:
            self.vision_button.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="👁️")
            self.add_to_history("Orion: Vision disabled.\n")

    def delete_orion_folder(self):
        # Confirmation dialog
        confirm_window = ctk.CTkToplevel(self.root)
        confirm_window.title("Delete Data Folder")
        confirm_window.geometry("300x150")
        confirm_window.resizable(False, False)
        
        label = ctk.CTkLabel(confirm_window, text="Are you sure you want to delete\nthe entire .orion data folder?\nThis will delete all chats and settings.", justify="center")
        label.pack(pady=10)
        
        def confirm_delete():
            try:
                shutil.rmtree(self.data_dir)
                if not os.path.exists(self.data_dir):
                    os.makedirs(self.data_dir)
                
                # Reset state
                self.current_chat_id = None
                self.chat_history_data = []
                for widget in self.chat_history.winfo_children():
                    widget.destroy()
                self.refresh_chat_list()
                self.load_settings() # Reload defaults since file is gone
                self.add_to_history("System: .orion folder deleted and reset.\n")
            except Exception as e:
                self.add_to_history(f"System: Error deleting folder: {str(e)}\n")
            confirm_window.destroy()

        button_frame = ctk.CTkFrame(confirm_window)
        button_frame.pack(pady=10)
        
        yes_button = ctk.CTkButton(button_frame, text="Yes, Delete", fg_color="red", command=confirm_delete)
        yes_button.pack(side="left", padx=5)
        
        no_button = ctk.CTkButton(button_frame, text="Cancel", command=confirm_window.destroy)
        no_button.pack(side="right", padx=5)

    def run(self):
        self.root.mainloop()

    def start_memory_status_check(self):
        def check_loop():
            while self.running:
                self._check_memory_status()
                time.sleep(2)
        
        threading.Thread(target=check_loop, daemon=True).start()

    def manual_retry_connection(self):
        threading.Thread(target=self._check_memory_status, daemon=True).start()

    def _check_memory_status(self):
        try:
            if not self.running or not self.root.winfo_exists():
                return
            
            is_loaded = False
            connection_error = False
            current_model = self.orion.ollama_model
            ram_usage = ""
            
            try:
                response = requests.get('http://localhost:11434/api/ps', timeout=0.5)
                if response.status_code == 200:
                    data = response.json()
                    # Get full model objects
                    models = data.get('models', [])
                    for model_obj in models:
                        model = model_obj.get('name', '')
                        if current_model in model or model in current_model:
                            is_loaded = True
                            size_bytes = model_obj.get('size', 0)
                            if size_bytes > 0:
                                size_gb = size_bytes / (1024**3)
                                ram_usage = f"({size_gb:.2f} GB)"
                            break
            except Exception:
                connection_error = True

            def update_ui():
                if self.running and self.memory_status_indicator.winfo_exists():
                    if connection_error:
                        self.memory_status_indicator.configure(text="🔴 Connection Failed", text_color="red")
                        self.ram_usage_label.configure(text="")
                        if not self.retry_button.winfo_ismapped():
                            self.retry_button.pack(side="right", padx=2)
                    else:
                        if self.retry_button.winfo_ismapped():
                            self.retry_button.pack_forget()
                            
                        if is_loaded:
                            self.memory_status_indicator.configure(text="🟢 Model Loaded", text_color="green")
                            self.ram_usage_label.configure(text=ram_usage)
                        else:
                            self.memory_status_indicator.configure(text="⚫ Model Unloaded", text_color="gray")
                            self.ram_usage_label.configure(text="")
            
            self.root.after(0, update_ui)
        except Exception:
            pass

    def start_internet_check(self):
        def check_loop():
            while self.running:
                self._check_internet()
                time.sleep(10)
        
        threading.Thread(target=check_loop, daemon=True).start()

    def _check_internet(self):
        try:
            if not self.running or not self.root.winfo_exists():
                return
            
            try:
                requests.get("https://www.google.com", timeout=3)
                if self.running:
                    self.root.after(0, lambda: self.internet_status_indicator.configure(text="🌐 Online", text_color="green"))
            except Exception:
                if self.running:
                    self.root.after(0, lambda: self.internet_status_indicator.configure(text="🌐 Offline", text_color="red"))
        except Exception:
            pass

if __name__ == "__main__":
    # --- Splash Screen ---
    try:
        splash = ctk.CTk()
        splash.overrideredirect(True) # Borderless window
        
        # Center splash on screen
        width = 300
        height = 300
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f'{width}x{height}+{x}+{y}')
        
        # Display Logo
        if os.path.exists("logo.png"):
            logo_img = ctk.CTkImage(Image.open("logo.png"), size=(150, 150))
            ctk.CTkLabel(splash, image=logo_img, text="").pack(expand=True, pady=(20, 0))
        
        ctk.CTkLabel(splash, text="Orion AI", font=("Arial", 24, "bold")).pack(pady=(10, 5))
        ctk.CTkLabel(splash, text="Loading...", font=("Arial", 12)).pack(pady=(0, 20))
        
        splash.update()
        time.sleep(2) # Display splash for 2 seconds
        splash.destroy()
    except Exception as e:
        print(f"Splash screen error: {e}")
    # ---------------------

    gui = OrionGUI()
    # Check if opened via file association (argument passed)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path) and file_path.endswith(".orion"):
            # Schedule import shortly after startup
            gui.root.after(500, lambda: gui.import_chat_from_path(file_path))
    gui.run()
