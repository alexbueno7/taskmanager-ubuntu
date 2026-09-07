from src import collector


def test_get_process_list_returns_current_user_only():
    import getpass

    me = getpass.getuser()
    procs = collector.get_process_list()
    assert isinstance(procs, list) and len(procs) > 0
    assert all(p["username"] == me for p in procs)
    assert all({"pid", "name", "cpu", "mem_mb"}.issubset(p.keys()) for p in procs)


def test_kill_process_gone_pid():
    assert collector.kill_process(999999999, force=False) in ("gone", "denied")
