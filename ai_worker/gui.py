import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Ensure workspace directory is in python path
workspace_dir = str(Path(__file__).parent.resolve())
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from pipeline import run_extraction_pipeline
import broker
from tasks import extract_pdf_metadata

class CrownbirdExtractorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CrownBird Research Bridge — AI Extraction Engine")
        self.geometry("850x700")
        self.minsize(750, 550)

        self._create_widgets()

    def _create_widgets(self):
        # Header Frame
        header = ttk.Frame(self, padding=12)
        header.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header,
            text="Research Bridge PDF Metadata Extraction",
            font=("Segoe UI", 16, "bold")
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            header,
            text="Extracts Title, Subject Keywords, and Abstract using PyMuPDF / PaddleOCR + Gemini via Redis & Dramatiq",
            font=("Segoe UI", 10)
        )
        subtitle_lbl.pack(anchor=tk.W)

        # File Selection Frame
        file_frame = ttk.LabelFrame(self, text=" 1. Document Selection ", padding=10)
        file_frame.pack(fill=tk.X, padx=12, pady=6)

        self.path_var = tk.StringVar()
        entry = ttk.Entry(file_frame, textvariable=self.path_var, font=("Segoe UI", 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        browse_btn = ttk.Button(file_frame, text="Browse PDF...", command=self._browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # Options Frame
        opts_frame = ttk.LabelFrame(self, text=" 2. Processing Configuration ", padding=10)
        opts_frame.pack(fill=tk.X, padx=12, pady=6)

        # Mode Selection
        ttk.Label(opts_frame, text="Extraction Mode:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.mode_var = tk.StringVar(value="auto")
        mode_cb = ttk.Combobox(
            opts_frame,
            textvariable=self.mode_var,
            values=["auto", "digital", "scanned"],
            state="readonly",
            width=12
        )
        mode_cb.grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        # Max Pages
        ttk.Label(opts_frame, text="Max Pages:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=4)
        self.max_pages_var = tk.IntVar(value=15)
        pages_spin = ttk.Spinbox(opts_frame, from_=1, to=100, textvariable=self.max_pages_var, width=6)
        pages_spin.grid(row=0, column=3, sticky=tk.W, padx=6, pady=4)

        # Execution Method
        ttk.Label(opts_frame, text="Queue Engine:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.engine_var = tk.StringVar(value="dramatiq")
        engine_cb = ttk.Combobox(
            opts_frame,
            textvariable=self.engine_var,
            values=["dramatiq", "direct"],
            state="readonly",
            width=12
        )
        engine_cb.grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        # Gemini API Key
        ttk.Label(opts_frame, text="Gemini API Key:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=4)
        self.api_key_var = tk.StringVar(value=os.getenv("GEMINI_API_KEY", ""))
        key_entry = ttk.Entry(opts_frame, textvariable=self.api_key_var, show="*", width=30)
        key_entry.grid(row=1, column=3, sticky=tk.W, padx=6, pady=4)

        # Action Button Frame
        action_frame = ttk.Frame(self, padding=8)
        action_frame.pack(fill=tk.X, padx=12)

        self.run_btn = ttk.Button(
            action_frame,
            text="Start Metadata Extraction",
            command=self._start_extraction
        )
        self.run_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)

        self.status_lbl = ttk.Label(action_frame, text="Ready", font=("Segoe UI", 10, "italic"))
        self.status_lbl.pack(side=tk.LEFT, padx=16)

        # Output / Results Display Notebook
        nb_frame = ttk.Frame(self, padding=12)
        nb_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(nb_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Structured Fields
        fields_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(fields_tab, text="Extracted Candidate Metadata")

        ttk.Label(fields_tab, text="Title:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.title_txt = tk.Text(fields_tab, height=2, wrap=tk.WORD, font=("Segoe UI", 10))
        self.title_txt.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(fields_tab, text="Subject Keywords:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.keywords_txt = tk.Text(fields_tab, height=2, wrap=tk.WORD, font=("Segoe UI", 10))
        self.keywords_txt.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(fields_tab, text="Abstract:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.abstract_txt = tk.Text(fields_tab, height=8, wrap=tk.WORD, font=("Segoe UI", 10))
        self.abstract_txt.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Raw Logs & JSON
        raw_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(raw_tab, text="Raw JSON Result & Logs")

        self.log_txt = tk.Text(raw_tab, wrap=tk.WORD, font=("Consolas", 9))
        self.log_txt.pack(fill=tk.BOTH, expand=True)

    def _browse_file(self):
        selected = filedialog.askopenfilename(
            title="Select PDF document",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        if selected:
            self.path_var.set(selected)

    def _start_extraction(self):
        pdf_path = self.path_var.get().strip()
        if not pdf_path or not Path(pdf_path).exists():
            messagebox.showerror("Invalid File", "Please select a valid PDF file.")
            return

        api_key = self.api_key_var.get().strip()
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        self.run_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Processing extraction...")
        self.log_txt.delete("1.0", tk.END)
        self.title_txt.delete("1.0", tk.END)
        self.keywords_txt.delete("1.0", tk.END)
        self.abstract_txt.delete("1.0", tk.END)

        threading.Thread(target=self._run_task_thread, args=(pdf_path,), daemon=True).start()

    def _run_task_thread(self, pdf_path: str):
        mode = self.mode_var.get()
        max_pages = self.max_pages_var.get()
        engine = self.engine_var.get()

        try:
            if engine == "dramatiq":
                self._log("Submitting task to Redis queue via Dramatiq...")
                msg = extract_pdf_metadata.send(
                    file_path=pdf_path,
                    mode=mode,
                    max_pages=max_pages
                )
                self._log(f"Enqueued. Message ID: {msg.message_id}")
                self._log("Waiting for worker result from Redis...")
                result = msg.get_result(block=True, timeout=120000)
            else:
                self._log("Executing pipeline directly...")
                res_obj = run_extraction_pipeline(
                    file_path=pdf_path,
                    mode=mode,
                    max_pages=max_pages
                )
                result = res_obj.model_dump()

            self._update_ui_with_result(result)
        except Exception as e:
            self._log(f"Error during execution: {e}")
            self.status_lbl.config(text="Execution Failed")
        finally:
            self.run_btn.config(state=tk.NORMAL)

    def _log(self, text: str):
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)

    def _update_ui_with_result(self, result: dict):
        status = result.get("status")
        self.status_lbl.config(text=f"Status: {status}")
        self._log("\n" + json.dumps(result, indent=2))

        candidate = result.get("candidate_metadata")
        if candidate:
            self.title_txt.insert(tk.END, candidate.get("title", ""))
            self.keywords_txt.insert(tk.END, ", ".join(candidate.get("subject_keywords", [])))
            self.abstract_txt.insert(tk.END, candidate.get("abstract", ""))
        else:
            err = result.get("error_message") or "Extraction stalled (no usable metadata)."
            self.title_txt.insert(tk.END, f"[{status}] {err}")

if __name__ == "__main__":
    app = CrownbirdExtractorGUI()
    app.mainloop()

