import tkinter as tk
from tkinter import messagebox, ttk

from . import collector

COLS = ("pid", "name", "cpu", "mem_pct", "mem_mb", "status")


def main():
    app = TaskManagerApp()
    app.mainloop()


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Tarefas")
        self.geometry("860x540")
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        self.search = tk.StringVar()
        ttk.Entry(top, textvariable=self.search, width=30).pack(
            side="left", padx=(0, 6)
        )
        self.search.trace_add("write", self.apply_filter)
        self.totals = ttk.Label(top, text="CPU -- | MEM --")
        self.totals.pack(side="left", padx=8)
        ttk.Button(top, text="Atualizar", command=self.refresh).pack(side="right")
        ttk.Button(top, text="Forçar", command=lambda: self.on_kill(True)).pack(
            side="right", padx=4
        )
        ttk.Button(top, text="Encerrar", command=lambda: self.on_kill(False)).pack(
            side="right", padx=4
        )
        self.tree = ttk.Treeview(self, columns=COLS, show="headings")
        widths = {
            "pid": 80,
            "name": 260,
            "cpu": 80,
            "mem_pct": 80,
            "mem_mb": 90,
            "status": 120,
        }
        for c in COLS:
            self.tree.heading(c, text=c.upper(), command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=widths[c], anchor="w" if c == "name" else "center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.bind("<Double-1>", self.show_details)
        self._rows = []
        self._sort = ("cpu", True)
        collector.get_process_list()
        self.refresh()

    def sort_by(self, col):
        rev = not (self._sort[0] == col and self._sort[1])
        self._sort = (col, rev)
        self.apply_filter()

    def refresh(self):
        try:
            self._rows = collector.get_process_list()
            t = collector.get_totals()
            self.totals.config(text=f"CPU {t['cpu']}% | MEM {t['mem_pct']}%")
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
        for r in rows:
            if q and q not in f"{r['name']} {r['pid']}".lower():
                continue
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
