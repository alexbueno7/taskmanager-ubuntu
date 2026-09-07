# taskmanager-ubuntu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir app Tkinter lista/mata processos usuário e empacotar .deb instalável Ubuntu 26.04.

**Architecture:** Núcleo coletor psutil puro testável sem GUI + UI Tkinter ttk.Treeview com refresh `after(2000)` + pacote .deb via `dpkg-deb` com Depends sistema.

**Tech Stack:** Python3 (>=3.10), Tkinter (python3-tk), psutil (>=5.9, usa 7.1.0 sistema), dpkg-deb, git.

**Spec:** `docs/superpowers/specs/2026-09-07-taskmanager-design.md`

## Global Constraints

- Ubuntu 26.04 LTS alvo, Python 3.14 sistema.
- Só processos do usuário atual (`getpass.getuser()`), sem pkexec/root.
- Depends .deb exato: `python3, python3-tk, python3-psutil`.
- Package: `taskmanager-ubuntu`, Version `1.0.0-1`, Architecture `all`.
- Comando instalado: `/usr/bin/taskmanager-ubuntu` chmod 755.
- .desktop em `/usr/share/applications/taskmanager-ubuntu.desktop`.
- Refresh padrão 2000ms, Kill via SIGTERM depois SIGKILL com confirmação.
- AccessDenied/NoSuchProcess nunca derrubam app.

---

## File Structure

- `src/collector.py` — coleta/filtro/kill puro, sem tkinter. Funções: `get_process_list() -> list[dict]`, `kill_process(pid:int, force:bool) -> str`, `get_totals() -> dict`.
- `src/app.py` — UI Tkinter, importa collector. Classe `TaskManagerApp(tk.Tk)` com métodos `refresh()`, `apply_filter()`, `on_kill(force)`, `show_details()`.
- `src/__main__.py` — `from .app import main; main()` para `python3 -m`.
- `packaging/DEBIAN/control` — metadados .deb.
- `packaging/usr-share-applications/taskmanager-ubuntu.desktop` — entrada menu (fonte, copiada no build).
- `build-deb.sh` — monta `build/taskmanager-ubuntu_1.0.0-1_all/` e roda `dpkg-deb --build`.
- `tests/test_collector.py` — pytest só collector (sem display).
- `README.md` — install/uso/dev.
- `.gitignore` — `__pycache__/`, `build/`, `*.deb`, `.pytest_cache/`.

---

### Task 1: Núcleo coletor psutil (testável)

**Files:**
- Create: `src/collector.py`
- Create: `src/__init__.py`
- Test: `tests/test_collector.py`

**Interfaces:**
- Consumes: `psutil`, `getpass`, `os`, `signal` (stdlib + psutil).
- Produces: `get_process_list() -> list[dict{pid:int,name:str,username:str,cpu:float,mem_mb:float,mem_pct:float,status:str}]`, `kill_process(pid:int, force:bool=False) -> str ('terminated'|'killed'|'gone'|'denied')`, `get_totals() -> dict{cpu:float,mem_pct:float}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_collector.py
from src import collector

def test_get_process_list_returns_current_user_only():
    import getpass
    me = getpass.getuser()
    procs = collector.get_process_list()
    assert isinstance(procs, list) and len(procs) > 0
    assert all(p["username"] == me for p in procs)
    assert all({"pid","name","cpu","mem_mb"}.issubset(p.keys()) for p in procs)

def test_kill_process_gone_pid():
    assert collector.kill_process(999999999, force=False) in ("gone","denied")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_collector.py -v`
Expected: FAIL with "No module named 'src.collector'" / file not found.

- [ ] **Step 3: Write minimal implementation**

```python
# src/__init__.py
"""taskmanager-ubuntu core."""
# src/collector.py
import getpass
import psutil

def get_process_list():
    me = getpass.getuser()
    out = []
    for p in psutil.process_iter(["pid","name","username","memory_info","memory_percent","status"]):
        try:
            info = p.info
            if info.get("username") != me:
                continue
            try:
                cpu = p.cpu_percent(interval=0.0)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cpu = 0.0
            mem = info.get("memory_info")
            out.append({
                "pid": info["pid"],
                "name": info.get("name") or "?",
                "username": info.get("username") or me,
                "cpu": round(float(cpu or 0.0), 1),
                "mem_mb": round((mem.rss if mem else 0) / 1024 / 1024, 1),
                "mem_pct": round(float(info.get("memory_percent") or 0.0), 1),
                "status": str(info.get("status") or "?"),
                "cmdline": " ".join((p.cmdline() or [])[:3]) if True else "",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(out, key=lambda d: d["cpu"], reverse=True)

def kill_process(pid: int, force: bool = False) -> str:
    try:
        proc = psutil.Process(int(pid))
    except psutil.NoSuchProcess:
        return "gone"
    except psutil.AccessDenied:
        return "denied"
    try:
        (proc.kill if force else proc.terminate)()
        return "killed" if force else "terminated"
    except psutil.NoSuchProcess:
        return "gone"
    except psutil.AccessDenied:
        return "denied"

def get_totals() -> dict:
    return {"cpu": round(psutil.cpu_percent(interval=0.1), 1), "mem_pct": round(psutil.virtual_memory().percent, 1)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_collector.py -v`
Expected: PASS (2 passed). Se headless ok, collector não precisa display.

- [ ] **Step 5: Warm-up CPU sanity**

Run: `python3 -c "from src import collector; collector.get_process_list(); import time; time.sleep(0.3); r=collector.get_process_list()[:3]; print(r)"`
Expected: lista 3 dicts usuário atual, sem traceback.

- [ ] **Step 6: Commit**

```bash
git add src/collector.py src/__init__.py tests/test_collector.py
git commit -m "feat: adiciona coletor psutil filtrado por usuário"
```

---

### Task 2: UI Tkinter tipo Gerenciador Tarefas

**Files:**
- Create: `src/app.py`
- Create: `src/__main__.py`
- Modify: `tests/test_collector.py` (sem mudança UI; teste UI é manual)

**Interfaces:**
- Consumes: `src.collector.get_process_list, kill_process, get_totals`.
- Produces: `TaskManagerApp(tk.Tk)` com `refresh()`, `apply_filter(*a)`, `on_kill(force:bool)`, `show_details(event)`; `main() -> None`.

- [ ] **Step 1: Write manual smoke expectation (sem pytest GUI)**

```text
SMOKE: `python3 -m src` abre janela "Gerenciador de Tarefas",
tabela com colunas PID/Nome/CPU%/MEM%/MEM MB/Estado,
barra topo com busca + label "CPU x% | MEM y%" atualizando 2s,
botões Encerrar/Forçar/Atualizar funcionam.
```

- [ ] **Step 2: Implement minimal UI**

```python
# src/app.py (essencial, completo no commit)
import tkinter as tk
from tkinter import ttk, messagebox
from . import collector

COLS = ("pid","name","cpu","mem_pct","mem_mb","status")

def main():
    app = TaskManagerApp()
    app.mainloop()

class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Tarefas")
        self.geometry("860x540")
        top = ttk.Frame(self); top.pack(fill="x", padx=8, pady=6)
        self.search = tk.StringVar()
        ttk.Entry(top, textvariable=self.search, width=30).pack(side="left", padx=(0,6))
        self.search.trace_add("write", self.apply_filter)
        self.totals = ttk.Label(top, text="CPU -- | MEM --"); self.totals.pack(side="left", padx=8)
        ttk.Button(top, text="Atualizar", command=self.refresh).pack(side="right")
        ttk.Button(top, text="Forçar", command=lambda: self.on_kill(True)).pack(side="right", padx=4)
        ttk.Button(top, text="Encerrar", command=lambda: self.on_kill(False)).pack(side="right", padx=4)
        self.tree = ttk.Treeview(self, columns=COLS, show="headings")
        for c, w in (("pid",80),("name",260),("cpu",80),("mem_pct",80),("mem_mb",90),("status",120)):
            self.tree.heading(c, text=c.upper(), command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=w, anchor="w" if c=="name" else "center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.bind("<Double-1>", self.show_details)
        self._rows = []
        self._sort = ("cpu", True)
        collector.get_process_list()
        self.refresh()

    def sort_by(self, col):
        rev = not (self._sort[0]==col and self._sort[1])
        self._sort = (col, rev); self.apply_filter()

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
            self.tree.insert("", "end", iid=str(r["pid"]),
                values=(r["pid"], r["name"][:40], f"{r['cpu']}%", f"{r['mem_pct']}%", r["mem_mb"], r["status"]))

    def on_kill(self, force):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nada", "Selecione um processo."); return
        pid = int(sel[0])
        if not messagebox.askyesno("Confirmar", f"{'Forçar (SIGKILL)' if force else 'Encerrar (SIGTERM)'} PID {pid}?"):
            return
        res = collector.kill_process(pid, force)
        msg = {"terminated":"SIGTERM enviado.","killed":"SIGKILL enviado.","gone":"Processo já saiu.","denied":"Sem permissão."}[res]
        messagebox.showinfo("Kill", msg)

    def show_details(self, event):
        sel = self.tree.selection()
        if sel:
            messagebox.showinfo(f"PID {sel[0]}", "\n".join(str(v) for v in self.tree.item(sel[0])["values"]))
```

```python
# src/__main__.py
from .app import main
if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Byte-compile sem display**

Run: `python3 -m py_compile src/app.py src/collector.py src/__main__.py && echo OK`
Expected: OK sem erro (não abre janela).

- [ ] **Step 4: Smoke GUI manual (pula se sem display)**

Run: `python3 -m src`
Expected: janela abre, lista preenche em 2s, busca filtra, Encerrar pede confirmação.

- [ ] **Step 5: Commit**

```bash
git add src/app.py src/__main__.py
git commit -m "feat: adiciona UI Tkinter com lista, busca e kill"
```

---

### Task 3: Empacotamento .deb + .desktop + build script

**Files:**
- Create: `packaging/DEBIAN/control`
- Create: `packaging/usr-share-applications/taskmanager-ubuntu.desktop`
- Create: `build-deb.sh`
- Create: `usr-bin-stub` (não; build copia `src/` para `/usr/share/taskmanager-ubuntu/` + wrapper `/usr/bin/taskmanager-ubuntu`)

**Interfaces:**
- Consumes: `src/*.py` das Tasks 1-2.
- Produces: `build/taskmanager-ubuntu_1.0.0-1_all.deb` instalável via `sudo dpkg -i`.

- [ ] **Step 1: Write control + desktop**

```
# packaging/DEBIAN/control
Package: taskmanager-ubuntu
Version: 1.0.0-1
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-tk, python3-psutil
Maintainer: voce <voce@example.com>
Description: Gerenciador de tarefas simples estilo Windows
 Lista processos do usuário com %CPU/%MEM e permite encerrar/forçar.
```

```
# packaging/usr-share-applications/taskmanager-ubuntu.desktop
[Desktop Entry]
Name=Gerenciador de Tarefas
Comment=Lista CPU/MEM e encerra processos
Exec=taskmanager-ubuntu
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=System;Monitor;
```

- [ ] **Step 2: Write build-deb.sh**

```bash
#!/bin/bash
set -e
VER=1.0.0-1
ROOT=build/taskmanager-ubuntu_${VER}_all
rm -rf build
mkdir -p "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/taskmanager-ubuntu" "$ROOT/usr/share/applications" "$ROOT/usr/share/doc/taskmanager-ubuntu"
cp packaging/DEBIAN/control "$ROOT/DEBIAN/"
cp -r src "$ROOT/usr/share/taskmanager-ubuntu/"
printf '#!/bin/sh\nexec python3 /usr/share/taskmanager-ubuntu/src/app.py "$@"\n' > "$ROOT/usr/bin/taskmanager-ubuntu"
chmod 755 "$ROOT/usr/bin/taskmanager-ubuntu"
cp packaging/usr-share-applications/taskmanager-ubuntu.desktop "$ROOT/usr/share/applications/"
echo "taskmanager-ubuntu ($VER) - changelog inicial" | gzip -9 -c > "$ROOT/usr/share/doc/taskmanager-ubuntu/changelog.gz"
dpkg-deb --build "$ROOT"
echo "OK: $ROOT.deb"
```

- [ ] **Step 3: Build**

Run: `bash build-deb.sh && ls -lh build/*.deb && dpkg-deb -c build/taskmanager-ubuntu_1.0.0-1_all.deb | head -n 20`
Expected: .deb existe, contém `usr/bin/taskmanager-ubuntu`, `usr/share/taskmanager-ubuntu/src/app.py`, `usr/share/applications/*.desktop`.

- [ ] **Step 4: Lint control**

Run: `dpkg-deb -f build/taskmanager-ubuntu_1.0.0-1_all.deb Package Version Depends`
Expected: `taskmanager-ubuntu / 1.0.0-1 / python3, python3-tk, python3-psutil`.

- [ ] **Step 5: Commit**

```bash
git add packaging/DEBIAN/control packaging/usr-share-applications/taskmanager-ubuntu.desktop build-deb.sh
git commit -m "feat: empacota .deb com desktop e build script"
```

---

### Task 4: Git + README + verificação install

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Modify: nenhum código

**Interfaces:**
- Consumes: .deb da Task 3.
- Produces: repo git inicial pronto p/ `gh repo create --public --push`, README com install/uso.

- [ ] **Step 1: README mínimo**

```markdown
# taskmanager-ubuntu
Gerenciador tarefas estilo Windows p/ Ubuntu. Tkinter + psutil. Mostra %CPU/%MEM, encerra/força processo usuário.
## Instalar
sudo dpkg -i build/taskmanager-ubuntu_1.0.0-1_all.deb
sudo apt -f install  # se faltar dep
## Usar
taskmanager-ubuntu  # ou menu "Gerenciador de Tarefas"
## Dev
python3 -m pytest -v
bash build-deb.sh
```

- [ ] **Step 2: .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
build/
*.deb
```

- [ ] **Step 3: Init git + commit inicial**

```bash
git init
git add -A
git commit -m "feat: v1 gerenciador tarefas com .deb"
git status --short
```

Expected: working tree clean, log mostra 3-4 commits (coletor, UI, deb, docs).

- [ ] **Step 4: Teste install real**

Run: `sudo dpkg -i build/taskmanager-ubuntu_1.0.0-1_all.deb && dpkg -l taskmanager-ubuntu && taskmanager-ubuntu & sleep 2; pkill -f taskmanager-ubuntu || true; sudo apt remove -y taskmanager-ubuntu`
Expected: instala sem erro (ou `apt -f` resolve), `dpkg -l` mostra `ii`, app abre, remove limpo.

- [ ] **Step 5: Push GitHub (manual, público)**

Run: `gh repo create taskmanager-ubuntu --public --source=. --push`
Expected: URL pública retornada. Se `gh` ausente, instruir push manual.

---

## Self-Review

- Spec coverage: lista CPU/MEM → Task1+2; encerrar/forçar por linha → Task1 kill + Task2 botões; buscar/ordenar/refresh → Task2; .deb instalável → Task3; git público → Task4. OK.
- Placeholder scan: sem TBD/TODO, comandos exatos, código colado, versões exatas. OK.
- Type consistency: `get_process_list()->list[dict]` usado igual Task1→Task2; `kill_process(pid,force)->str` mesmos literais; `_rows`/`_sort` internos só Task2. OK.
