import getpass

import psutil


def get_process_list():
    me = getpass.getuser()
    out = []
    for p in psutil.process_iter(
        ["pid", "name", "username", "memory_info", "memory_percent", "status"]
    ):
        try:
            info = p.info
            if info.get("username") != me:
                continue
            try:
                cpu = p.cpu_percent(interval=0.0)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cpu = 0.0
            mem = info.get("memory_info")
            try:
                cmd = p.cmdline()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cmd = []
            out.append(
                {
                    "pid": info["pid"],
                    "name": info.get("name") or "?",
                    "username": info.get("username") or me,
                    "cpu": round(float(cpu or 0.0), 1),
                    "mem_mb": round((mem.rss if mem else 0) / 1024 / 1024, 1),
                    "mem_pct": round(float(info.get("memory_percent") or 0.0), 1),
                    "status": str(info.get("status") or "?"),
                    "cmdline": " ".join((cmd or [])[:3]),
                }
            )
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
    return {
        "cpu": round(psutil.cpu_percent(interval=0.1), 1),
        "mem_pct": round(psutil.virtual_memory().percent, 1),
    }
