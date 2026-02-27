import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from shared_utils_app import get_gemini_client
from query_app import ask_my_notes
import os
import json
import markdown2
import fitz 
from loader_app import process_files_to_db
import re
from tkinter import Toplevel
from PIL import Image, ImageTk
import pyperclip


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StudyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Study Assistant")
        self.geometry("1100x750")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AI Study Assistant", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # API Key
        self.api_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Gemini API Key...", show="*")
        self.api_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.api_entry.bind("<Return>", lambda e: self.start_model_fetch())
        
        self.api_status = ctk.CTkLabel(self.sidebar_frame, text="Press Enter to connect", font=ctk.CTkFont(size=10))
        self.api_status.grid(row=2, column=0, padx=20, pady=0)

        # Model Select
        self.model_menu = ctk.CTkComboBox(self.sidebar_frame, values=["gemini-2.0-flash"])
        self.model_menu.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # DB Path
        self.path_display = ctk.CTkEntry(self.sidebar_frame, placeholder_text="No DB Selected", state="disabled")
        self.path_display.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        self.browse_btn = ctk.CTkButton(self.sidebar_frame, text="📁 Select Database", command=self.select_path)
        self.browse_btn.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # Upload
        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="📤 Upload Notes", fg_color="#2c7a5d", command=self.start_upload)
        self.upload_btn.grid(row=6, column=0, padx=20, pady=15, sticky="ew")

        # Manager
        self.manage_btn = ctk.CTkButton(self.sidebar_frame, text="⚙️ Manage Files", command=self.open_file_manager)
        self.manage_btn.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        # Progress
        self.progress_label = ctk.CTkLabel(self.sidebar_frame, text="System Idle", font=ctk.CTkFont(size=10))
        self.progress_label.grid(row=8, column=0, padx=20, pady=(10,0))
        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame)
        self.progress_bar.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        # Clear Chat Button (Memory Wipe)
        self.clear_chat_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="🧹 Clear Conversation", 
            fg_color="#4a4a4a", 
            command=self.clear_chat_action
        )
        self.clear_chat_btn.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # Reset (Bottom)
        self.reset_btn = ctk.CTkButton(self.sidebar_frame, text="Nuclear Reset", fg_color="red", command=self.confirm_reset)
        self.reset_btn.grid(row=11, column=0, padx=20, pady=20, sticky="s")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # --- Chat Area ---
        self.chat_container = ctk.CTkFrame(self)
        self.chat_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.chat_container.grid_rowconfigure(0, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)

        self.scrollable_chat = ctk.CTkScrollableFrame(self.chat_container, fg_color="transparent")
        self.scrollable_chat.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.chat_input = ctk.CTkEntry(self.chat_container, placeholder_text="Ask about your lectures...")
        self.chat_input.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.chat_input.bind("<Return>", lambda e: self.send_message())
        
        # Chat history will be stored as a list of dicts with 'role' and 'content' for better session management
        self.chat_history = [] # This will store our session memory
        
        self.load_settings()
        
        

    # --- Methods ---
    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_display.configure(state="normal")
            self.path_display.delete(0, "end")
            self.path_display.insert(0, path)
            self.path_display.configure(state="disabled")
            self.save_settings()

    def start_model_fetch(self):
        key = self.api_entry.get().strip()
        self.api_status.configure(text="Connecting...", text_color="white")
        threading.Thread(target=self.fetch_models_task, args=(key,), daemon=True).start()

    def fetch_models_task(self, api_key):
        try:
            client = get_gemini_client(api_key)
            models = [m.name.replace("models/", "") for m in client.models.list() if 'generateContent' in m.supported_actions]
            self.after(0, lambda: self.update_model_menu(models))
        except Exception:
            self.after(0, lambda: self.api_status.configure(text="Invalid Key", text_color="red"))

    def update_model_menu(self, models):
        self.model_menu.configure(values=models)
        self.model_menu.set(models[0])
        self.api_status.configure(text="Connected ✅", text_color="green")
        self.save_settings()

    def send_message(self):
        query = self.chat_input.get().strip()
        api_key = self.api_entry.get()
        db_path = self.path_display.get()
        if query and api_key and "No DB" not in db_path:
            self.add_message("User", query)
            self.chat_input.delete(0, "end")
            self.add_message("Assistant", "Thinking...")
            threading.Thread(target=self.ai_worker_task, args=(query, api_key, db_path, self.model_menu.get()), daemon=True).start()

    def ai_worker_task(self, query, key, path, model):
        try:
            # 1. Ask the AI (using your updated query_app.py)
            answer = ask_my_notes(query, key, path, model, history=self.chat_history)
            
            # 2. FIX: Append using the correct dictionary structure
            self.chat_history.append({
                "role": "user", 
                "parts": [{"text": query}] # Must be a list of dictionaries
            })
            self.chat_history.append({
                "role": "model", 
                "parts": [{"text": answer}] # Must be a list of dictionaries
            })
            
            self.after(0, lambda: self.add_message("Assistant", answer))
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.add_message("Assistant", f"Error: {error_msg}"))
            
    def start_upload(self):
        """Opens file dialog with expanded types for Vision support."""
        files = filedialog.askopenfilenames(
            filetypes=[
                ("All Supported Docs", "*.pdf *.pptx *.txt *.jpg *.png *.jpeg"),
                ("Documents", "*.pdf *.pptx *.txt"), 
                ("Images", "*.jpg *.png *.jpeg")
            ]
        )
        if files:
            # Ensure the bar is visible and reset before starting
            self.progress_bar.set(0)
            self.progress_label.configure(text="Initializing Extraction...")
            threading.Thread(target=self.upload_worker, args=(files,), daemon=True).start()

    def upload_worker(self, files):
        """Handles heavy OCR and image extraction without freezing the UI."""
        from loader_app import process_files_to_db
        
        def up(txt, p):
            # The 'up' callback now handles the 'Analyzing/OCR' status updates
            self.after(0, lambda: self.progress_label.configure(text=txt))
            self.after(0, lambda: self.progress_bar.set(p))
        
        api_key = self.api_entry.get()
        db_path = self.path_display.get()
        
        # We wrap this in a try-block for extra safety on the background thread
        try:
            res = process_files_to_db(files, api_key, db_path, "university_notes", up)
        except Exception as e:
            res = f"Fatal Error during processing: {str(e)}"
            
        self.after(0, lambda: self.finish_upload(res))

    def finish_upload(self, result_message):
        """Resets the UI elements and reports the detailed result."""
        self.progress_bar.set(0)
        self.progress_label.configure(text="System Idle")
        
        # Use appropriate icons based on the outcome of the OCR/Extraction
        if "Success" in result_message:
            messagebox.showinfo("Upload Complete", result_message)
        else:
            messagebox.showerror("Upload Error", result_message)

    def open_file_manager(self):
        from loader_app import get_unique_sources
        manager = ctk.CTkToplevel(self)
        manager.title("File Manager")
        manager.geometry("400x500")
        manager.attributes("-topmost", True)
        
        scroll = ctk.CTkScrollableFrame(manager, label_text="Database Contents")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        client = get_gemini_client(self.api_entry.get())
        files = get_unique_sources(client, self.path_display.get())
        
        for f in files:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f).pack(side="left", padx=5)
            ctk.CTkButton(row, text="🗑️", width=30, fg_color="red", command=lambda n=f: self.delete_file_action(n, manager)).pack(side="right")

    def delete_file_action(self, filename, window):
        if messagebox.askyesno("Confirm", f"Delete {filename}?"):
            from loader_app import delete_source_from_db
            client = get_gemini_client(self.api_entry.get())
            delete_source_from_db(client, self.path_display.get(), filename)
            window.destroy()
            self.open_file_manager()

    def confirm_reset(self):
        if messagebox.askyesno("Nuclear Reset", "Wipe EVERYTHING?"):
            db_path = self.path_display.get()
            import shutil
            import gc
            import time

            # 1. Force release of DB handles
            self.chat_history = []
            # If you have a reference to the collection/client in your class:
            if hasattr(self, 'current_collection'):
                self.current_collection = None
            
            # Trigger garbage collection to close open file handles
            gc.collect()
            time.sleep(1) # Give OneDrive/Windows a second to breathe

            # 2. Wipe the ChromaDB folder
            if os.path.exists(db_path):
                try:
                    shutil.rmtree(db_path)
                    os.makedirs(db_path)
                except Exception as e:
                    # If it still fails, it's a hard lock
                    print(f"DB Wipe Error: {e}")
                    messagebox.showerror("Reset Error", f"OneDrive is locking your files.\n\nError: {e}")
                    return

            # 3. Wipe the images folder
            image_dir = "data/images"
            if os.path.exists(image_dir):
                try:
                    shutil.rmtree(image_dir)
                    os.makedirs(image_dir)
                except: pass

            self.clear_chat_action()
            messagebox.showinfo("Reset", "Everything wiped clean.")
            
    def save_settings(self):
        """Saves current API Key and DB Path to a local JSON file."""
        config = {
            "api_key": self.api_entry.get(),
            "db_path": self.path_display.get(),
            "last_model": self.model_menu.get()
        }
        with open("config_app.json", "w") as f:
            json.dump(config, f)

    def load_settings(self):
        """Loads settings on startup if the file exists."""
        try:
            with open("config_app.json", "r") as f:
                config = json.load(f)
                # Fill the UI fields
                self.api_entry.insert(0, config.get("api_key", ""))
                self.path_display.configure(state="normal")
                self.path_display.insert(0, config.get("db_path", ""))
                self.path_display.configure(state="disabled")
                if "last_model" in config:
                    self.model_menu.set(config["last_model"])
                # Automatically trigger a connection check
                self.start_model_fetch()
        except FileNotFoundError:
            pass # First time running the app
        
   
    def add_message(self, role, text):
        bg_color = "#1f538d" if role == "User" else "#333333"
        frame = ctk.CTkFrame(self.scrollable_chat, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        bubble_frame = ctk.CTkFrame(frame, fg_color=bg_color, corner_radius=15)
        bubble_frame.pack(side="right" if role == "User" else "left", padx=10)

        # --- CODE BLOCK PARSING ---
        # Split text by triple backticks
        parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
        
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                # This is a Code Block
                code_content = part.strip("`").strip()
                
                # Container for code + copy button
                code_container = ctk.CTkFrame(bubble_frame, fg_color="#1a1a1a", corner_radius=8)
                code_container.pack(padx=10, pady=5, fill="x")
                
                code_box = ctk.CTkTextbox(
                    code_container, height=100, width=500,
                    font=ctk.CTkFont(family="Consolas", size=12),
                    fg_color="transparent", border_width=0, activate_scrollbars=False
                )
                code_box.insert("0.0", code_content)
                code_box.configure(state="disabled")
                code_box.pack(padx=10, pady=(10, 5))
                
                # Copy Button
                copy_btn = ctk.CTkButton(
                    code_container, text="📋 Copy Code", width=80, height=20,
                    font=ctk.CTkFont(size=10), fg_color="#444444",
                    command=lambda c=code_content: self.copy_to_clipboard(c)
                )
                copy_btn.pack(side="right", padx=10, pady=5)
            else:
                # Regular Text
                if not part.strip(): continue
                display_text = part.replace("**", "")
                display_text = re.sub(r"^\*\s", "• ", display_text, flags=re.MULTILINE)
                
                lbl = ctk.CTkLabel(
                    bubble_frame, text=display_text, font=ctk.CTkFont(size=13),
                    justify="left", wraplength=550, anchor="w"
                )
                lbl.pack(padx=15, pady=5)

        # --- VISION LOGIC (Kept exactly as before) ---
        citation_match = re.search(r"SOURCE:\s*(.*?),\s*PAGE/SLIDE:\s*(\d+)", text)
        if citation_match and role == "Assistant":
            fname = citation_match.group(1).strip()
            pnum = citation_match.group(2).strip()
            img_path = os.path.join("data/images", f"{fname}_page{pnum}_img1.png")
            if not os.path.exists(img_path):
                img_path = os.path.join("data/images", f"{fname}_slide{pnum}_img1.png")

            if os.path.exists(img_path):
                btn = ctk.CTkButton(
                    bubble_frame, text="🖼️ View Diagram", width=120, height=24,
                    fg_color="#444444", hover_color="#555555",
                    command=lambda p=img_path: self.show_image_popup(p)
                )
                btn.pack(padx=15, pady=(0, 10))

        self.scrollable_chat._parent_canvas.yview_moveto(1.0)

    def copy_to_clipboard(self, text):
        pyperclip.copy(text)
        # Optional: Change button text temporarily to "Copied!"

        def show_image_popup(self, img_path):
            """Opens a HighDPI-compatible window to show the diagram."""
            popup = Toplevel(self)
            popup.title("Diagram Reference")
            
            # Load the image using PIL
            pil_img = Image.open(img_path)
            
            # Calculate a reasonable display size (max 800px wide)
            w, h = pil_img.size
            display_w = 800
            display_h = int(h * (display_w / w))
            
            # Wrap the PIL image in a CTkImage for scaling support
            ctk_img = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=(display_w, display_h)
            )
            
            # Apply to the label
            label = ctk.CTkLabel(popup, image=ctk_img, text="")
            label.image = ctk_img # Keep a reference to prevent garbage collection
            label.pack(padx=20, pady=20)

    def apply_basic_markdown(self, textbox):
        """Refined parser to clean up markdown markers and format bullets."""
        import re
        
        # 1. First, replace the raw markdown bullets with a cleaner symbol
        raw_content = textbox.get("1.0", "end")
        # This regex looks for an asterisk at the start of a line
        cleaned_content = re.sub(r"^\*\s", "• ", raw_content, flags=re.MULTILINE)
        
        # Update the textbox with cleaned content before applying styles
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", cleaned_content.strip())
        
        # 2. Configure our highlight tag
        textbox.tag_config("bold_highlight", foreground="#3b8ed0") 
        
        content = textbox.get("1.0", "end")
        
        # 3. Find matches for bold text (e.g., **Database System**)
        # We use a pattern that captures the text INSIDE the asterisks
        for match in re.finditer(r"\*\*(.*?)\*\*", content):
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            
            # Apply the highlight color
            textbox.tag_add("bold_highlight", start_idx, end_idx)
            
            # OPTIONAL: To truly hide the '**', we can create a 'hidden' tag
            # that makes the text color match the bubble background
            textbox.tag_config("hidden", foreground=textbox.cget("fg_color"))
            
            # Hide the first two asterisks
            textbox.tag_add("hidden", start_idx, f"{start_idx} + 2 chars")
            # Hide the last two asterisks
            textbox.tag_add("hidden", f"{end_idx} - 2 chars", end_idx)

        textbox.configure(state="disabled")
            
    def clear_chat_action(self):
        """Wipes the UI bubbles and the AI's short-term memory."""
        # Wipe the Python list holding the conversation
        self.chat_history = [] 
        
        # Clear the UI widgets
        for widget in self.scrollable_chat.winfo_children():
            widget.destroy()
        
        self.add_message("Assistant", "Memory cleared. What shall we study now?")

if __name__ == "__main__":
    app = StudyApp()
    app.mainloop()