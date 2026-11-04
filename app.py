#!/usr/bin/env python3
"""
PDF Fingerprint & Metadata Cloner
GUI and CLI application for forensic-level PDF metadata & trailer ID transplanting.
"""

import sys
import os
import argparse
import threading
import subprocess
from typing import Optional, Dict, Any

from engine import extract_pdf_fingerprint, transplant_fingerprint


# ==========================================
# CLI Handler
# ==========================================

def run_cli(args):
    print("=" * 60)
    print("PDF Fingerprint & Metadata Cloner (CLI Mode)")
    print("=" * 60)
    print(f"Оригинал (донор): {args.orig}")
    print(f"Целевой (контент): {args.target}")
    print(f"Выходной файл:    {args.output}")
    print(f"Режим:            {args.mode}")
    print("-" * 60)

    def cli_progress(msg: str, percent: int):
        print(f"[{percent:3d}%] {msg}")

    success, msg = transplant_fingerprint(
        original_pdf_path=args.orig,
        target_pdf_path=args.target,
        output_pdf_path=args.output,
        mode=args.mode,
        copy_trailer_id=not args.no_id,
        copy_xmp=not args.no_xmp,
        copy_info=not args.no_info,
        copy_catalog_attrs=not args.no_catalog,
        sync_page_boxes=args.sync_boxes,
        progress_callback=cli_progress,
    )

    print("-" * 60)
    if success:
        print(f" УСПЕХ: {msg}")
        # Print comparison
        orig_fp = extract_pdf_fingerprint(args.orig)
        out_fp = extract_pdf_fingerprint(args.output)
        print("\nПроверка отпечатков:")
        print(f" - Trailer ID (Perm): {out_fp['trailer_id_permanent']}")
        print(f" - Match Orig ID:     {out_fp['trailer_id_permanent'] == orig_fp['trailer_id_permanent']}")
        print(f" - Producer:          {out_fp['producer']}")
        print(f" - Match Producer:    {out_fp['producer'] == orig_fp['producer']}")
        print(f" - XMP DocID:         {out_fp['xmp_doc_id']}")
        print(f" - Match XMP DocID:   {out_fp['xmp_doc_id'] == orig_fp['xmp_doc_id']}")
        sys.exit(0)
    else:
        print(f" ОШИБКА: {msg}")
        sys.exit(1)


# ==========================================
# GUI Implementation (Tkinter + TTK)
# ==========================================

def run_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("PDF Fingerprint & Metadata Cloner (v1.0 Windows)")
            self.geometry("860x780")
            self.minsize(800, 720)
            self.configure(bg="#181825")

            self.orig_fp: Optional[Dict[str, Any]] = None
            self.target_fp: Optional[Dict[str, Any]] = None
            self.out_fp: Optional[Dict[str, Any]] = None

            self.setup_styles()
            self.build_ui()

        def setup_styles(self):
            style = ttk.Style(self)
            style.theme_use("clam")

            # General
            style.configure(".", background="#181825", foreground="#cdd6f4", font=("Segoe UI", 10))

            # Frames
            style.configure("Card.TFrame", background="#1e1e2e", relief="flat")
            style.configure("Header.TFrame", background="#11111b")

            # Labels
            style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#89b4fa", background="#11111b")
            style.configure("Subtitle.TLabel", font=("Segoe UI", 9), foreground="#a6adc8", background="#11111b")
            style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), foreground="#b4befe", background="#1e1e2e")
            style.configure("Badge.TLabel", font=("Consolas", 8), foreground="#94e2d5", background="#313244", padding=4)
            style.configure("Muted.TLabel", font=("Segoe UI", 9), foreground="#6c7086", background="#1e1e2e")
            style.configure("Card.TLabel", background="#1e1e2e", foreground="#cdd6f4")

            # Buttons
            style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background="#89b4fa", foreground="#11111b", borderwidth=0, padding=10)
            style.map("Primary.TButton", background=[("active", "#74c7ec"), ("disabled", "#45475a")])

            style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#313244", foreground="#cdd6f4", borderwidth=0, padding=6)
            style.map("Secondary.TButton", background=[("active", "#45475a")])

            style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), background="#a6e3a1", foreground="#11111b", borderwidth=0, padding=6)
            style.map("Action.TButton", background=[("active", "#94e2d5")])

            # Entry
            style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", borderwidth=0, insertcolor="#cdd6f4")

            # Progressbar
            style.configure("Horizontal.TProgressbar", background="#89b4fa", troughcolor="#313244", borderwidth=0)

            # Radio & Checkbutton
            style.configure("Card.TRadiobutton", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9, "bold"))
            style.configure("Card.TCheckbutton", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9))

            # Treeview (Comparison table)
            style.configure("Treeview", background="#1e1e2e", fieldbackground="#1e1e2e", foreground="#cdd6f4", rowheight=24, borderwidth=0)
            style.configure("Treeview.Heading", background="#313244", foreground="#b4befe", font=("Segoe UI", 9, "bold"))
            style.map("Treeview", background=[("selected", "#45475a")])

        def build_ui(self):
            # 1. Header
            header_frame = ttk.Frame(self, style="Header.TFrame", padding=(20, 14))
            header_frame.pack(fill=tk.X)

            title_lbl = ttk.Label(header_frame, text="🛡️ PDF Fingerprint & Metadata Cloner", style="Title.TLabel")
            title_lbl.pack(anchor=tk.W)
            sub_lbl = ttk.Label(
                header_frame,
                text="Полный перенос Trailer ID, XMP-отпечатков, словаря Info и структуры оригинала с сохранением вашего текста.",
                style="Subtitle.TLabel"
            )
            sub_lbl.pack(anchor=tk.W, pady=(2, 0))

            # Main scrollable or container
            main_container = ttk.Frame(self, padding=(18, 12))
            main_container.pack(fill=tk.BOTH, expand=True)

            # 2. File Selection Card
            files_card = ttk.Frame(main_container, style="Card.TFrame", padding=14)
            files_card.pack(fill=tk.X, pady=(0, 10))

            # --- Row 1: Original PDF ---
            ttk.Label(files_card, text="1. Оригинальный PDF (Донор отпечатков и метаданных):", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
            self.orig_path_var = tk.StringVar()
            self.orig_entry = ttk.Entry(files_card, textvariable=self.orig_path_var)
            self.orig_entry.grid(row=1, column=0, sticky=tk.EW, padx=(0, 8), pady=2)
            ttk.Button(files_card, text="Обзор...", style="Secondary.TButton", command=self.browse_orig).grid(row=1, column=1, pady=2)

            self.orig_badge_var = tk.StringVar(value="Файл не выбран")
            self.orig_badge = ttk.Label(files_card, textvariable=self.orig_badge_var, style="Badge.TLabel")
            self.orig_badge.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(2, 10))

            # --- Row 2: Target PDF ---
            ttk.Label(files_card, text="2. Ваш измененный PDF (Содержит нужный текст и вёрстку):", style="Section.TLabel").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
            self.target_path_var = tk.StringVar()
            self.target_entry = ttk.Entry(files_card, textvariable=self.target_path_var)
            self.target_entry.grid(row=4, column=0, sticky=tk.EW, padx=(0, 8), pady=2)
            ttk.Button(files_card, text="Обзор...", style="Secondary.TButton", command=self.browse_target).grid(row=4, column=1, pady=2)

            self.target_badge_var = tk.StringVar(value="Файл не выбран")
            self.target_badge = ttk.Label(files_card, textvariable=self.target_badge_var, style="Badge.TLabel")
            self.target_badge.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(2, 10))

            # --- Row 3: Output PDF ---
            ttk.Label(files_card, text="3. Куда сохранить результат:", style="Section.TLabel").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
            self.out_path_var = tk.StringVar()
            self.out_entry = ttk.Entry(files_card, textvariable=self.out_path_var)
            self.out_entry.grid(row=7, column=0, sticky=tk.EW, padx=(0, 8), pady=2)
            ttk.Button(files_card, text="Выбрать...", style="Secondary.TButton", command=self.browse_output).grid(row=7, column=1, pady=2)

            files_card.columnconfigure(0, weight=1)

            # 3. Settings Card
            opts_card = ttk.Frame(main_container, style="Card.TFrame", padding=14)
            opts_card.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(opts_card, text="Режим и параметры переноса:", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 6))

            # Mode selection
            mode_frame = ttk.Frame(opts_card, style="Card.TFrame")
            mode_frame.pack(fill=tk.X, pady=(0, 6))

            self.mode_var = tk.StringVar(value="injection")
            r1 = ttk.Radiobutton(
                mode_frame,
                text="🟢 Умная инъекция (Smart Injection) — берет ваш PDF с текстом и внедряет 100% отпечатков оригинала",
                value="injection",
                variable=self.mode_var,
                style="Card.TRadiobutton"
            )
            r1.pack(anchor=tk.W, pady=2)

            r2 = ttk.Radiobutton(
                mode_frame,
                text="🔵 Вживление в контейнер (Container Grafting) — берет оригинальный PDF и заменяет страницы вашим текстом",
                value="grafting",
                variable=self.mode_var,
                style="Card.TRadiobutton"
            )
            r2.pack(anchor=tk.W, pady=2)

            # Checkbox options
            chk_frame = ttk.Frame(opts_card, style="Card.TFrame")
            chk_frame.pack(fill=tk.X, pady=(4, 0))

            self.opt_id = tk.BooleanVar(value=True)
            self.opt_xmp = tk.BooleanVar(value=True)
            self.opt_info = tk.BooleanVar(value=True)
            self.opt_catalog = tk.BooleanVar(value=True)
            self.opt_sync_boxes = tk.BooleanVar(value=False)

            c1 = ttk.Checkbutton(chk_frame, text="Trailer ID (/ID [perm, mod])", variable=self.opt_id, style="Card.TCheckbutton")
            c2 = ttk.Checkbutton(chk_frame, text="XMP XML поток (DocumentID, InstanceID)", variable=self.opt_xmp, style="Card.TCheckbutton")
            c3 = ttk.Checkbutton(chk_frame, text="Info словарь (Producer, Creator, Даты)", variable=self.opt_info, style="Card.TCheckbutton")
            c4 = ttk.Checkbutton(chk_frame, text="Настройки каталога (/ViewerPreferences)", variable=self.opt_catalog, style="Card.TCheckbutton")
            c5 = ttk.Checkbutton(chk_frame, text="Синхронизировать размеры страниц (MediaBox)", variable=self.opt_sync_boxes, style="Card.TCheckbutton")

            c1.grid(row=0, column=0, sticky=tk.W, padx=(0, 15), pady=2)
            c2.grid(row=0, column=1, sticky=tk.W, pady=2)
            c3.grid(row=1, column=0, sticky=tk.W, padx=(0, 15), pady=2)
            c4.grid(row=1, column=1, sticky=tk.W, pady=2)
            c5.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

            # 4. Live Inspector / Comparison Table
            table_card = ttk.Frame(main_container, style="Card.TFrame", padding=14)
            table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            ttk.Label(table_card, text="Инспектор цифровых отпечатков (Сравнение До и После):", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 6))

            columns = ("property", "original", "target", "result")
            self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=5)
            self.tree.heading("property", text="Параметр / Отпечаток")
            self.tree.heading("original", text="Оригинал (Донор)")
            self.tree.heading("target", text="Ваш PDF (До)")
            self.tree.heading("result", text="Результат (После)")

            self.tree.column("property", width=160, anchor=tk.W)
            self.tree.column("original", width=220, anchor=tk.W)
            self.tree.column("target", width=220, anchor=tk.W)
            self.tree.column("result", width=220, anchor=tk.W)

            self.tree.pack(fill=tk.BOTH, expand=True)
            self.init_comparison_table()

            # 5. Action & Progress Bar
            action_frame = ttk.Frame(main_container, style="Card.TFrame", padding=10)
            action_frame.pack(fill=tk.X)

            self.progress_bar = ttk.Progressbar(action_frame, orient=tk.HORIZONTAL, mode="determinate", style="Horizontal.TProgressbar")
            self.progress_bar.pack(fill=tk.X, pady=(0, 6))

            self.status_var = tk.StringVar(value="Готов к работе. Выберите файлы для начала.")
            self.status_lbl = ttk.Label(action_frame, textvariable=self.status_var, style="Muted.TLabel")
            self.status_lbl.pack(anchor=tk.W, pady=(0, 8))

            btn_row = ttk.Frame(action_frame, style="Card.TFrame")
            btn_row.pack(fill=tk.X)

            self.run_btn = ttk.Button(btn_row, text="🚀 ВЫПОЛНИТЬ ПЕРЕНОС ОТПЕЧАТКОВ", style="Primary.TButton", command=self.start_process)
            self.run_btn.pack(side=tk.LEFT, padx=(0, 10))

            self.open_file_btn = ttk.Button(btn_row, text="📄 Открыть PDF", style="Action.TButton", command=self.open_output_file, state=tk.DISABLED)
            self.open_file_btn.pack(side=tk.LEFT, padx=(0, 6))

            self.open_folder_btn = ttk.Button(btn_row, text="📂 Открыть папку", style="Secondary.TButton", command=self.open_output_folder, state=tk.DISABLED)
            self.open_folder_btn.pack(side=tk.LEFT)

        def init_comparison_table(self):
            for item in self.tree.get_children():
                self.tree.delete(item)

            rows = [
                ("Trailer ID (Permanent)", "—", "—", "—"),
                ("Producer", "—", "—", "—"),
                ("Creator", "—", "—", "—"),
                ("XMP DocumentID", "—", "—", "—"),
                ("PDF Version Header", "—", "—", "—"),
                ("Creation Date", "—", "—", "—"),
            ]
            for r in rows:
                self.tree.insert("", tk.END, values=r)

        def update_table_views(self):
            rows = [
                (
                    "Trailer ID (Permanent)",
                    (self.orig_fp["trailer_id_permanent"][:16] + "...") if self.orig_fp and self.orig_fp["trailer_id_permanent"] != "None" else "—",
                    (self.target_fp["trailer_id_permanent"][:16] + "...") if self.target_fp and self.target_fp["trailer_id_permanent"] != "None" else "—",
                    (self.out_fp["trailer_id_permanent"][:16] + "...") if self.out_fp and self.out_fp["trailer_id_permanent"] != "None" else "—",
                ),
                (
                    "Producer",
                    (self.orig_fp.get("producer") or "—") if self.orig_fp else "—",
                    (self.target_fp.get("producer") or "—") if self.target_fp else "—",
                    (self.out_fp.get("producer") or "—") if self.out_fp else "—",
                ),
                (
                    "Creator",
                    (self.orig_fp.get("creator") or "—") if self.orig_fp else "—",
                    (self.target_fp.get("creator") or "—") if self.target_fp else "—",
                    (self.out_fp.get("creator") or "—") if self.out_fp else "—",
                ),
                (
                    "XMP DocumentID",
                    (self.orig_fp.get("xmp_doc_id") or "—") if self.orig_fp else "—",
                    (self.target_fp.get("xmp_doc_id") or "—") if self.target_fp else "—",
                    (self.out_fp.get("xmp_doc_id") or "—") if self.out_fp else "—",
                ),
                (
                    "PDF Version Header",
                    f"%PDF-{self.orig_fp.get('pdf_version')}" if self.orig_fp else "—",
                    f"%PDF-{self.target_fp.get('pdf_version')}" if self.target_fp else "—",
                    f"%PDF-{self.out_fp.get('pdf_version')}" if self.out_fp else "—",
                ),
                (
                    "Creation Date",
                    (self.orig_fp.get("creation_date") or "—") if self.orig_fp else "—",
                    (self.target_fp.get("creation_date") or "—") if self.target_fp else "—",
                    (self.out_fp.get("creation_date") or "—") if self.out_fp else "—",
                ),
            ]
            for item in self.tree.get_children():
                self.tree.delete(item)
            for r in rows:
                self.tree.insert("", tk.END, values=r)

        def browse_orig(self):
            path = filedialog.askopenfilename(
                title="Выберите оригинальный PDF (донор метаданных)",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if path:
                self.orig_path_var.set(path)
                try:
                    self.orig_fp = extract_pdf_fingerprint(path)
                    id_short = self.orig_fp["trailer_id_permanent"][:14] if self.orig_fp["trailer_id_permanent"] != "None" else "отсутствует"
                    self.orig_badge_var.set(
                        f"Страниц: {self.orig_fp['page_count']} | Версия: {self.orig_fp['pdf_version']} | "
                        f"Producer: {self.orig_fp['producer'][:25]} | Trailer ID: {id_short}..."
                    )
                    self.update_table_views()
                except Exception as e:
                    self.orig_badge_var.set(f"Ошибка чтения: {e}")

        def browse_target(self):
            path = filedialog.askopenfilename(
                title="Выберите ваш PDF (с новым текстом)",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if path:
                self.target_path_var.set(path)
                try:
                    self.target_fp = extract_pdf_fingerprint(path)
                    self.target_badge_var.set(
                        f"Страниц: {self.target_fp['page_count']} | Версия: {self.target_fp['pdf_version']} | "
                        f"Текущий Creator: {self.target_fp['creator'][:25]}"
                    )
                    self.update_table_views()
                    # Suggest default output path
                    base, ext = os.path.splitext(path)
                    suggested = f"{base}_cloned.pdf"
                    self.out_path_var.set(suggested)
                except Exception as e:
                    self.target_badge_var.set(f"Ошибка чтения: {e}")

        def browse_output(self):
            path = filedialog.asksaveasfilename(
                title="Куда сохранить результат",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if path:
                self.out_path_var.set(path)

        def start_process(self):
            orig_p = self.orig_path_var.get().strip()
            target_p = self.target_path_var.get().strip()
            out_p = self.out_path_var.get().strip()

            if not orig_p or not os.path.exists(orig_p):
                messagebox.showerror("Ошибка", "Укажите существующий оригинальный PDF (донор)!")
                return
            if not target_p or not os.path.exists(target_p):
                messagebox.showerror("Ошибка", "Укажите существующий целевой PDF (с вашим текстом)!")
                return
            if not out_p:
                messagebox.showerror("Ошибка", "Укажите путь для сохранения готового PDF!")
                return

            self.run_btn.config(state=tk.DISABLED)
            self.open_file_btn.config(state=tk.DISABLED)
            self.open_folder_btn.config(state=tk.DISABLED)
            self.progress_bar["value"] = 5

            mode = self.mode_var.get()
            copy_id = self.opt_id.get()
            copy_xmp = self.opt_xmp.get()
            copy_info = self.opt_info.get()
            copy_cat = self.opt_catalog.get()
            sync_boxes = self.opt_sync_boxes.get()

            def progress_cb(msg: str, percent: int):
                self.after(0, lambda: self._on_progress(msg, percent))

            def worker():
                success, msg = transplant_fingerprint(
                    original_pdf_path=orig_p,
                    target_pdf_path=target_p,
                    output_pdf_path=out_p,
                    mode=mode,
                    copy_trailer_id=copy_id,
                    copy_xmp=copy_xmp,
                    copy_info=copy_info,
                    copy_catalog_attrs=copy_cat,
                    sync_page_boxes=sync_boxes,
                    progress_callback=progress_cb,
                )
                self.after(0, lambda: self._on_finish(success, msg, out_p))

            threading.Thread(target=worker, daemon=True).start()

        def _on_progress(self, msg: str, percent: int):
            self.progress_bar["value"] = percent
            self.status_var.set(f"[{percent}%] {msg}")

        def _on_finish(self, success: bool, msg: str, out_p: str):
            self.run_btn.config(state=tk.NORMAL)
            if success:
                self.progress_bar["value"] = 100
                self.status_var.set(" ГОТОВО! Все отпечатки успешно перенесены.")
                self.open_file_btn.config(state=tk.NORMAL)
                self.open_folder_btn.config(state=tk.NORMAL)
                try:
                    self.out_fp = extract_pdf_fingerprint(out_p)
                    self.update_table_views()
                except Exception:
                    pass
                messagebox.showinfo("Успех", f"{msg}\n\nФайл сохранен: {out_p}")
            else:
                self.status_var.set(f" Ошибка: {msg}")
                messagebox.showerror("Ошибка обработки", msg)

        def open_output_file(self):
            path = self.out_path_var.get().strip()
            if path and os.path.exists(path):
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path])
                else:
                    subprocess.run(["xdg-open", path])

        def open_output_folder(self):
            path = self.out_path_var.get().strip()
            if path and os.path.exists(path):
                folder = os.path.dirname(os.path.abspath(path))
                if sys.platform == "win32":
                    subprocess.run(["explorer", folder])
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder])
                else:
                    subprocess.run(["xdg-open", folder])

    app = App()
    app.mainloop()


# ==========================================
# Main Entry Point
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="PDF Fingerprint & Metadata Cloner — клонирование цифровых отпечатков и метаданных PDF."
    )
    parser.add_argument("--orig", help="Путь к оригинальному PDF (донор отпечатков и метаданных)")
    parser.add_argument("--target", help="Путь к вашему измененному PDF (содержит нужный текст)")
    parser.add_argument("--output", help="Путь для сохранения результирующего PDF")
    parser.add_argument("--mode", choices=["injection", "grafting"], default="injection", help="Режим переноса (injection или grafting)")
    parser.add_argument("--sync-boxes", action="store_true", help="Синхронизировать размеры страниц (MediaBox/CropBox)")
    parser.add_argument("--no-id", action="store_true", help="Не копировать Trailer ID")
    parser.add_argument("--no-xmp", action="store_true", help="Не копировать XMP-поток")
    parser.add_argument("--no-info", action="store_true", help="Не копировать словарь Info")
    parser.add_argument("--no-catalog", action="store_true", help="Не копировать параметры каталога")

    # If args given for orig and target, run in CLI mode
    if len(sys.argv) > 1 and ("--orig" in sys.argv or "--target" in sys.argv):
        args = parser.parse_args()
        if not args.orig or not args.target or not args.output:
            parser.error("--orig, --target и --output обязательны в CLI режиме.")
        run_cli(args)
    else:
        # Launch GUI
        run_gui()


if __name__ == "__main__":
    main()
