import tkinter as tk
from tkinter import font, messagebox, ttk

from . import collector

COLS = ("pid", "name", "cpu", "mem_pct", "mem_mb", "status")

BG = "#242424"
PANEL = "#2e2e2e"
FIELD = "#1e1e1e"
FG = "#ededed"
MUTED = "#9a9a9a"
BORDER = "#3d3d3d"
ACCENT = "#3584e4"
ACCENT_ACTIVE = "#2b6fc4"
DANGER = "#c01c28"
DANGER_ACTIVE = "#a0131e"
OK = "#57e389"
WARN = "#e5a50a"
CRIT = "#ff6655"
ROW_ALT = "#2a2a2a"


def main():
    app = TaskManagerApp()
    app.mainloop()


def cpu_state(value: float) -> str:
    if value >= 85:
        return "crit"
    if value >= 50:
        return "warn"
    return "ok"


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Tarefas")
        self.geometry("900x560")
        self.configure(bg=BG)
        self._build_style()
        self._build_header()
        self._build_table()
        self._rows = []
        self._sort = ("cpu", True)
        collector.get_process_list()
        self.refresh()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10)
        style.configure(".", background=BG, foreground=FG, font=default_font)
        style.configure("Toolbar.TFrame", background=PANEL)
        style.configure(
            "Title.TLabel", background=PANEL, foreground=FG, font=("", 12, "bold")
        )
        style.configure("Toolbar.TLabel", background=PANEL, foreground=MUTED)
        style.configure(
            "TEntry",
            fieldbackground=FIELD,
            foreground=FG,
            insertcolor=FG,
            bordercolor=BORDER,
        )
        style.configure(
            "TButton", background="#3d3d3d", foreground=FG, borderwidth=1, padding=6
        )
        style.map(
            "TButton",
            background=[("active", "#4d4d4d"), ("pressed", "#2b2b2b")],
        )
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map(
            "Accent.TButton",
            background=[("active", ACCENT_ACTIVE), ("pressed", "#1f5fa8")],
            foreground=[("disabled", MUTED)],
        )
        style.configure("Danger.TButton", background=DANGER, foreground="white")
        style.map(
            "Danger.TButton",
            background=[("active", DANGER_ACTIVE), ("pressed", "#7d0f16")],
            foreground=[("disabled", MUTED)],
        )
        style.configure(
            "Treeview",
            background=BG,
            fieldbackground=BG,
            foreground=FG,
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=PANEL,
            foreground=FG,
            relief="flat",
            padding=4,
        )
        style.map(
            "Treeview.Heading", background=[("active", "#3d3d3d")]
        )
        style.map(
            "Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=PANEL,
            troughcolor=BG,
            borderwidth=0,
            arrowsize=0,
        )
        for name, color in (
            ("BarOk", OK),
            ("BarWarn", WARN),
            ("BarCrit", CRIT),
        ):
            style.configure(
                f"{name}.Horizontal.TProgressbar",
                background=color,
                troughcolor=BORDER,
                thickness=6,
                borderwidth=0,
            )

    def _build_header(self):
        top = ttk.Frame(self, style="Toolbar.TFrame", padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="Gerenciador de Tarefas", style="Title.TLabel").pack(
            side="left", padx=(0, 12)
        )
        self.search = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search, width=24)
        entry.pack(side="left")
        self.search.trace_add("write", self.apply_filter)
        ttk.Button(top, text="Atualizar", command=self.refresh).pack(
            side="right", padx=(4, 0)
        )
        ttk.Button(
            top, text="Forçar", style="Danger.TButton", command=lambda: self.on_kill(True)
        ).pack(side="right", padx=4)
        ttk.Button(
            top,
            text="Encerrar",
            style="Accent.TButton",
            command=lambda: self.on_kill(False),
        ).pack(side="right", padx=4)
        bars = ttk.Frame(top, style="Toolbar.TFrame")
        bars.pack(side="right", padx=12)
        self.cpu_bar = ttk.Progressbar(
            bars, style="BarOk.Horizontal.TProgressbar", length=110, maximum=100
        )
        self.cpu_bar.pack(side="left", padx=2)
        self.cpu_label = ttk.Label(bars, text="CPU --", style="Toolbar.TLabel", width=9)
        self.cpu_label.pack(side="left", padx=(2, 8))
        self.mem_bar = ttk.Progressbar(
            bars, style="BarOk.Horizontal.TProgressbar", length=110, maximum=100
        )
        self.mem_bar.pack(side="left", padx=2)
        self.mem_label = ttk.Label(bars, text="MEM --", style="Toolbar.TLabel", width=9)
        self.mem_label.pack(side="left", padx=2)

    def _build_table(self):
        self.tree = ttk.Treeview(self, columns=COLS, show="headings")
        widths = {
            "pid": 80,
            "name": 300,
            "cpu": 90,
            "mem_pct": 90,
            "mem_mb": 100,
            "status": 130,
        }
        for c in COLS:
            self.tree.heading(c, text=c.upper(), command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=widths[c], anchor="w" if c == "name" else "center")
        self.tree.tag_configure("even", background=BG, foreground=FG)
        self.tree.tag_configure("odd", background=ROW_ALT, foreground=FG)
        self.tree.tag_configure("ok", foreground=FG)
        self.tree.tag_configure("warn", foreground=WARN)
        self.tree.tag_configure("crit", foreground=CRIT)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.show_details)

    def sort_by(self, col):
        rev = not (self._sort[0] == col and self._sort[1])
        self._sort = (col, rev)
        self.apply_filter()

    def _set_bar(self, bar, label, prefix, value):
        state = cpu_state(value)
        bar.configure(value=value)
        bar.configure(style=f"Bar{state.capitalize()}.Horizontal.TProgressbar")
        label.configure(text=f"{prefix} {value}%")

    def refresh(self):
        try:
            self._rows = collector.get_process_list()
            t = collector.get_totals()
            self._set_bar(self.cpu_bar, self.cpu_label, "CPU", t["cpu"])
            self._set_bar(self.mem_bar, self.mem_label, "MEM", t["mem_pct"])
            self.apply_filter()
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            self.after(2000, self.refresh)

    def apply_filter(self, *a):
        q = self.search.get().lower()
        col, rev = self._sort
        rows = sorted(self._rows, key=lambda d: d.get(col, 0), reverse=rev)
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            if q and q not in f"{r['name']} {r['pid']}".lower():
                continue
            stripe = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                iid=str(r["pid"]),
                values=(
                    r["pid"],
                    r["name"][:40],
                    f"{r['cpu']}%",
                    f"{r['mem_pct']}%",
                    r["mem_mb"],
                    r["status"],
                ),
                tags=(stripe, cpu_state(r["cpu"])),
            )

    def on_kill(self, force):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nada", "Selecione um processo.")
            return
        pid = int(sel[0])
        if not messagebox.askyesno(
            "Confirmar",
            f"{'Forçar (SIGKILL)' if force else 'Encerrar (SIGTERM)'} PID {pid}?",
        ):
            return
        res = collector.kill_process(pid, force)
        msg = {
            "terminated": "SIGTERM enviado.",
            "killed": "SIGKILL enviado.",
            "gone": "Processo já saiu.",
            "denied": "Sem permissão.",
        }[res]
        messagebox.showinfo("Kill", msg)

    def show_details(self, event):
        sel = self.tree.selection()
        if sel:
            messagebox.showinfo(
                f"PID {sel[0]}",
                "\n".join(str(v) for v in self.tree.item(sel[0])["values"]),
            )
