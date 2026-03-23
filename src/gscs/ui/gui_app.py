"""
Tkinter GUI application (stdlib - no external deps).
Loaded lazily only when 'gscs gui' is called.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from gscs.core.config import load_config
from gscs.core.models import Category, Language, Script
from gscs.services import registry
from gscs.services.search_engine import SearchFilter, search


class GscsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GS-CYBERsecu — Script Manager")
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.cfg = load_config()
        self._build_ui()
        self._refresh_scripts()

    # ─── UI Layout ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self, padding=4)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=4)
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self._search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=4)
        search_entry.bind("<Return>", lambda _: self._on_search())

        ttk.Label(toolbar, text="Category:").pack(side=tk.LEFT, padx=4)
        self._cat_var = tk.StringVar(value="all")
        cat_combo = ttk.Combobox(
            toolbar,
            textvariable=self._cat_var,
            values=["all"] + self.cfg.categories,
            width=14,
            state="readonly",
        )
        cat_combo.pack(side=tk.LEFT, padx=4)
        cat_combo.bind("<<ComboboxSelected>>", lambda _: self._on_search())

        ttk.Button(toolbar, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Add Script", command=self._add_dialog).pack(side=tk.LEFT, padx=8)
        ttk.Button(toolbar, text="Refresh", command=self._refresh_scripts).pack(side=tk.LEFT)

        # Main pane: script list + detail panel
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Script list (left)
        list_frame = ttk.LabelFrame(pane, text="Scripts", padding=4)
        pane.add(list_frame, weight=3)

        cols = ("name", "category", "language", "description")
        self._tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        for col, width in zip(cols, (180, 110, 80, 280)):
            self._tree.heading(col, text=col.capitalize())
            self._tree.column(col, width=width, anchor=tk.W)
        self._tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail panel (right)
        detail_frame = ttk.LabelFrame(pane, text="Details", padding=8)
        pane.add(detail_frame, weight=2)

        self._detail_text = tk.Text(detail_frame, wrap=tk.WORD, state=tk.DISABLED, width=40)
        self._detail_text.pack(fill=tk.BOTH, expand=True)

        btn_row = ttk.Frame(detail_frame)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Run", command=self._run_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)

        # Status bar
        self._status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status, anchor=tk.W, relief=tk.SUNKEN).pack(
            fill=tk.X, side=tk.BOTTOM, padx=4, pady=2
        )

    # ─── Data operations ──────────────────────────────────────────────────────

    def _refresh_scripts(self) -> None:
        self._scripts: list[Script] = registry.list_scripts()
        self._populate_tree(self._scripts)
        self._status.set(f"{len(self._scripts)} script(s) loaded")

    def _populate_tree(self, scripts: list[Script]) -> None:
        for row in self._tree.get_children():
            self._tree.delete(row)
        for s in scripts:
            self._tree.insert("", tk.END, iid=str(s.id), values=(
                s.name, s.category, s.language, s.description[:60]
            ))

    def _on_search(self) -> None:
        kw = self._search_var.get().strip() or None
        cat = self._cat_var.get()
        f = SearchFilter(
            keyword=kw,
            category=cat if cat != "all" else None,
        )
        results = search(f)
        self._populate_tree(results)
        self._status.set(f"{len(results)} result(s)")

    def _on_select(self, _event=None) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        script_id = int(sel[0])
        script = next((s for s in registry.list_scripts() if s.id == script_id), None)
        if not script:
            return
        self._show_details(script)

    def _show_details(self, s: Script) -> None:
        text = (
            f"Name:         {s.name}\n"
            f"Category:     {s.category}\n"
            f"Language:     {s.language}\n"
            f"Author:       {s.author or '—'}\n"
            f"Version:      {s.version}\n"
            f"Created:      {s.created_at[:10]}\n"
            f"Path:         {s.path}\n\n"
            f"Description:\n{s.description or '—'}\n\n"
            f"Tags:         {s.tags or '—'}\n"
            f"Dependencies: {', '.join(s.get_dependencies()) or '—'}\n"
            f"SHA256:       {s.sha256[:16]}…" if s.sha256 else "SHA256: —"
        )
        self._detail_text.configure(state=tk.NORMAL)
        self._detail_text.delete("1.0", tk.END)
        self._detail_text.insert(tk.END, text)
        self._detail_text.configure(state=tk.DISABLED)
        self._selected_script = s

    def _run_selected(self) -> None:
        if not hasattr(self, "_selected_script"):
            messagebox.showinfo("No selection", "Select a script first.")
            return
        messagebox.showinfo(
            "Run",
            f"Use the CLI to run:\n\ngscs run {self._selected_script.name}",
        )

    def _delete_selected(self) -> None:
        if not hasattr(self, "_selected_script"):
            messagebox.showinfo("No selection", "Select a script first.")
            return
        name = self._selected_script.name
        if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
            registry.delete_script(name)
            self._refresh_scripts()
            self._status.set(f"Deleted '{name}'")

    # ─── Add script dialog ────────────────────────────────────────────────────

    def _add_dialog(self) -> None:
        dlg = tk.Toplevel(self)
        dlg.title("Add Script")
        dlg.geometry("500x380")
        dlg.grab_set()

        fields: dict[str, tk.Variable] = {}

        def row(label: str, var: tk.Variable, widget_cls=ttk.Entry, **kw) -> None:
            f = ttk.Frame(dlg, padding=(8, 2))
            f.pack(fill=tk.X)
            ttk.Label(f, text=label, width=14, anchor=tk.E).pack(side=tk.LEFT)
            widget_cls(f, textvariable=var, **kw).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
            fields[label] = var

        path_var = tk.StringVar()
        row("Path:", path_var)
        ttk.Button(
            dlg, text="Browse",
            command=lambda: path_var.set(filedialog.askopenfilename()),
        ).pack(anchor=tk.W, padx=80)

        name_var = tk.StringVar()
        row("Name:", name_var)

        cat_var = tk.StringVar(value="custom")
        row("Category:", cat_var, ttk.Combobox, values=self.cfg.categories, state="readonly", width=18)

        lang_var = tk.StringVar(value="other")
        row("Language:", lang_var, ttk.Combobox, values=Language.ALL, state="readonly", width=18)

        desc_var = tk.StringVar()
        row("Description:", desc_var)

        tags_var = tk.StringVar()
        row("Tags:", tags_var)

        deps_var = tk.StringVar()
        row("Dependencies:", deps_var)

        def _save() -> None:
            from gscs.utils.hash import compute_sha256
            from gscs.utils.validators import ValidationError, sanitize_script_name, validate_path
            try:
                p = validate_path(path_var.get())
                n = sanitize_script_name(name_var.get() or p.stem)
            except ValidationError as e:
                messagebox.showerror("Validation Error", str(e))
                return
            s = Script(
                name=n,
                category=cat_var.get(),
                path=str(p),
                description=desc_var.get(),
                language=lang_var.get(),
                author="",
                sha256=compute_sha256(p),
            )
            s.set_tags([t.strip() for t in tags_var.get().split(",") if t.strip()])
            s.set_dependencies([d.strip() for d in deps_var.get().split(",") if d.strip()])
            registry.add_script(s)
            self._refresh_scripts()
            self._status.set(f"Added '{n}'")
            dlg.destroy()

        ttk.Button(dlg, text="Save", command=_save).pack(pady=10)


def launch() -> None:
    app = GscsApp()
    app.mainloop()
