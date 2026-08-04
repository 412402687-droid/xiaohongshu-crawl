"""
VPN 控制模块 — 管理 Sakurucat VPN 的启动和关闭

使用:
    from utils.vpn import start_vpn, stop_vpn

    start_vpn()   # 启动 VPN
    stop_vpn()    # 关闭 VPN

注意事项:
    - 仅在 Windows 桌面环境使用，GitHub Actions / Linux 下自动跳过
    - 需要 administrator 权限才能结束 VPN 进程
"""

import json
import os
import subprocess
import sys
import time
import platform
import signal


# ── 默认配置 ──────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vpn_config.json")
DEFAULT_CONFIG = {
    "enabled": True,
    "executable": "sakurucat.exe",
    "process_name": "sakurucat",
    "startup_wait": 5,          # VPN 启动后等待秒数
    "shutdown_wait": 2,         # VPN 关闭后等待秒数
}


def _load_config() -> dict:
    """加载 VPN 配置。"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # 合并默认值
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
    return DEFAULT_CONFIG.copy()


def _is_ci() -> bool:
    """检测是否运行在 CI 环境（GitHub Actions / Travis / Jenkins）。"""
    return any(os.getenv(v) for v in ["CI", "GITHUB_ACTIONS", "TRAVIS", "JENKINS_HOME"])


def _is_windows() -> bool:
    return platform.system() == "Windows"


def start_vpn() -> bool:
    """
    启动 Sakurucat VPN。

    返回:
        True  - VPN 成功启动 / 已在运行 / CI 环境跳过
        False - VPN 启动失败
    """
    # CI 环境自动跳过
    if _is_ci():
        print("[VPN] GitHub Actions 环境，跳过 VPN 启动")
        return True

    if not _is_windows():
        print("[VPN] 非 Windows 系统，跳过 VPN 启动")
        return True

    cfg = _load_config()

    if not cfg.get("enabled", True):
        print("[VPN] VPN 已禁用（vpn_config.enabled = false）")
        return True

    executable = cfg.get("executable", "sakurucat.exe")
    process_name = cfg.get("process_name", "sakurucat")

    # 检查是否已在运行
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}.exe"],
            capture_output=True, text=True, timeout=10
        )
        if process_name.lower() in result.stdout.lower():
            print(f"[VPN] Sakurucat 已在运行，跳过启动")
            return True
    except Exception:
        pass

    # 启动 VPN
    print(f"[VPN] 正在启动 Sakurucat: {executable}")
    try:
        subprocess.Popen(
            [executable],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print(f"[VPN] 找不到可执行文件: {executable}")
        print(f"[VPN] 请确认 vpn_config.json 中 executable 路径正确")
        return False
    except Exception as exc:
        print(f"[VPN] 启动失败: {exc}")
        return False

    # 等待 VPN 连接建立
    wait = cfg.get("startup_wait", 5)
    print(f"[VPN] 等待 {wait} 秒建立连接...")
    time.sleep(wait)

    print(f"[VPN] Sakurucat 已启动")
    return True


def stop_vpn() -> bool:
    """
    关闭 Sakurucat VPN。

    返回:
        True  - VPN 成功关闭 / 未运行 / CI 环境跳过
        False - VPN 关闭失败
    """
    if _is_ci():
        print("[VPN] GitHub Actions 环境，跳过 VPN 关闭")
        return True

    if not _is_windows():
        print("[VPN] 非 Windows 系统，跳过 VPN 关闭")
        return True

    cfg = _load_config()

    if not cfg.get("enabled", True):
        return True

    process_name = cfg.get("process_name", "sakurucat")

    print(f"[VPN] 正在关闭 Sakurucat...")
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", f"{process_name}.exe"],
            capture_output=True, timeout=15
        )
    except Exception as exc:
        print(f"[VPN] 关闭进程出错: {exc}")
        return False

    wait = cfg.get("shutdown_wait", 2)
    time.sleep(wait)

    print(f"[VPN] Sakurucat 已关闭")
    return True


# ── 命令行测试 ────────────────────────────────────────
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action == "start":
        start_vpn()
    elif action == "stop":
        stop_vpn()
    elif action == "config":
        cfg = _load_config()
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
    else:
        print(f"用法: python vpn.py [start|stop|config]")
