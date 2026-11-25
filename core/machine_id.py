import hashlib
import subprocess


def _reg(path, name):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except Exception:
        return ""


def _wmi(query, prop):
    try:
        out = subprocess.check_output(
            ["wmic"] + query.split() + ["get", prop],
            stderr=subprocess.DEVNULL, text=True, timeout=8)
        lines = [l.strip() for l in out.splitlines() if l.strip() and prop.lower() not in l.lower()]
        return lines[0] if lines else ""
    except Exception:
        return ""


def get_machine_id() -> str:
    parts = [
        _reg(r"SOFTWARE\Microsoft\Cryptography", "MachineGuid"),
        _wmi("bios", "SerialNumber"),
        _wmi("csproduct", "UUID"),
        _wmi("cpu", "ProcessorId"),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


if __name__ == "__main__":
    print(get_machine_id())