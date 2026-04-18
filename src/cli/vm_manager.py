# -*- coding: utf-8 -*-
"""
VMware 靶机自动管理模块

功能：
- 启动 / 停止 VMware 虚拟机
- 自动检测靶机 IP（扫描 DHCP 网段 + ARP）
- 自动注入网络配置（通过 vmrun runScriptInGuest）
- 向 ClawAI scan 命令提供"开箱即用"的靶机 IP

设计原则：
- 无需手动操作 VMware 控制台
- 支持从 VirtualBox 转换的靶机（interfaces 静态 IP 问题）
- 注入策略：优先 dhclient，失败则 ip addr add + service restart
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# 持久化 IP 缓存文件
_IP_CACHE_FILE = Path.home() / ".codebuddy" / "vm_ip_cache.json"

# ── 常量 ──────────────────────────────────────────────────────────

# vmrun / vmware 路径（Windows 默认安装位置）
_VMRUN_CANDIDATES = [
    r"E:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe",
    r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe",
    r"C:\Program Files\VMware\VMware Workstation\vmrun.exe",
]

# VMware NAT 和 Host-Only 网段（按优先级）
_VMWARE_SUBNETS = [
    "192.168.23",    # VMnet8 NAT（默认）
    "192.168.184",   # VMnet1 Host-Only
    "192.168.56",    # VirtualBox Host-Only（兼容）
    "192.168.1",     # 普通局域网
]

# 扫描的 IP 范围（DHCP 通常从 128 开始）
_SCAN_RANGE_START = 100
_SCAN_RANGE_END   = 254

# 靶机常用账户（按优先级）
_DEFAULT_CREDENTIALS = [
    ("jangow01",  "abygurl69"),
    ("root",      "toor"),
    ("root",      "root"),
    ("ubuntu",    "ubuntu"),
    ("kali",      "kali"),
    ("vagrant",   "vagrant"),
    ("user",      "user"),
]

# 注入 IP 时使用的候选地址（避免冲突）
_INJECT_IP_CANDIDATES = [
    ("192.168.23.150",  "192.168.23.0/24"),
    ("192.168.23.151",  "192.168.23.0/24"),
    ("192.168.184.150", "192.168.184.0/24"),
]

# 启动后等待时间（秒）
_BOOT_WAIT = 45
_DHCP_WAIT = 8


# ── 数据类 ─────────────────────────────────────────────────────────

@dataclass
class VMInfo:
    """虚拟机信息"""
    vmx_path: str
    name: str = ""
    ip: str = ""
    running: bool = False
    username: str = ""
    password: str = ""
    network_injected: bool = False  # True 表示 IP 是手动注入的（非 DHCP）


# ── 核心类 ─────────────────────────────────────────────────────────

class VMManager:
    """
    VMware 靶机生命周期管理器

    用法：
        mgr = VMManager()
        ip = mgr.ensure_running("E:/VMs/Jangow/Jangow.vmx")
        # ip 就是靶机可用的地址，可直接传给 scan
    """

    def __init__(self, vmrun_path: str = ""):
        self.vmrun = vmrun_path or self._find_vmrun()
        self._vm_cache: dict[str, VMInfo] = {}

    # ── 公开接口 ──────────────────────────────────────────────────

    def ensure_running(self, vmx_path: str,
                       boot_wait: int = _BOOT_WAIT) -> Optional[str]:
        """
        确保 VM 运行且网络可达，返回 IP 地址。
        这是 scan 命令的主要入口。
        """
        vmx_path = str(Path(vmx_path).resolve())

        print(f"[vm] 检查靶机: {Path(vmx_path).stem}")

        # 1. 如果没有运行，先启动
        if not self._is_running(vmx_path):
            print("[vm] 靶机未运行，正在启动...")
            if not self._start(vmx_path):
                print("[vm] 启动失败")
                return None
            print(f"[vm] 等待系统启动 ({boot_wait}s)...")
            time.sleep(boot_wait)
        else:
            print("[vm] 靶机已在运行")

        # 2. 等待 VMware Tools 就绪
        cred = self._wait_for_tools(vmx_path, timeout=30)
        if not cred:
            print("[vm] VMware Tools 未就绪，尝试直接扫描 IP...")
        else:
            print(f"[vm] VMware Tools 就绪 (账户: {cred[0]})")

        # 3. 优先检查持久化缓存（用户之前手动注册的 IP）
        saved_ip = self._load_ip_cache().get(vmx_path)
        if saved_ip and self._verify_http(saved_ip):
            print(f"[vm] 使用缓存 IP: {saved_ip}")
            return saved_ip

        # 4. 动态探测 IP
        ip = self._get_ip(vmx_path, cred)
        if ip:
            print(f"[vm] 靶机 IP: {ip}")
            self._vm_cache[vmx_path] = VMInfo(vmx_path, ip=ip,
                                               running=True,
                                               username=cred[0] if cred else "",
                                               password=cred[1] if cred else "")
            return ip

        # 4. IP 获取失败 → 自动注入网络配置
        print("[vm] 未检测到 IP，尝试自动注入网络配置...")
        if cred:
            ip = self._inject_network(vmx_path, cred)

        if ip:
            print(f"[vm] 网络注入成功，IP: {ip}")
            info = VMInfo(vmx_path, ip=ip, running=True,
                          username=cred[0] if cred else "",
                          password=cred[1] if cred else "",
                          network_injected=True)
            self._vm_cache[vmx_path] = info
            return ip

        print("[vm] 自动配网失败。请在 VMware 控制台执行：sudo dhclient ens33")
        print("[vm] 获取 IP 后运行: clawai vm register <vmx路径> <IP地址>")
        return None

    def start(self, vmx_path: str) -> bool:
        """启动 VM"""
        return self._start(str(Path(vmx_path).resolve()))

    def stop(self, vmx_path: str, hard: bool = False) -> bool:
        """停止 VM"""
        mode = "hard" if hard else "soft"
        ret = self._vmrun("stop", vmx_path, mode)
        return ret == 0

    def list_running(self) -> List[str]:
        """返回正在运行的 VM 列表（vmx 路径）"""
        try:
            out = subprocess.check_output(
                [self.vmrun, "list"], text=True, timeout=10
            )
            lines = out.strip().splitlines()
            return [l.strip() for l in lines if l.strip().endswith(".vmx")]
        except Exception:
            return []

    def get_ip_for(self, vmx_path: str) -> Optional[str]:
        """获取已运行 VM 的 IP（不做任何启动操作）"""
        vmx_key = str(Path(vmx_path).resolve())
        # 1. 内存缓存
        cached = self._vm_cache.get(vmx_key)
        if cached and cached.ip:
            return cached.ip
        # 2. 持久化缓存（用户手动注册的 IP）
        saved = self._load_ip_cache().get(vmx_key)
        if saved:
            if self._verify_http(saved):
                return saved
        # 3. 动态探测
        cred = self._find_valid_credential(vmx_path)
        return self._get_ip(vmx_path, cred)

    def register_ip(self, vmx_path: str, ip: str) -> None:
        """
        手动注册靶机 IP 到持久化缓存。
        用于靶机网络不能自动配置的情况，用户手动提供 IP 后系统记住。
        """
        vmx_key = str(Path(vmx_path).resolve())
        cache = self._load_ip_cache()
        cache[vmx_key] = ip
        self._save_ip_cache(cache)
        # 同步到内存缓存
        self._vm_cache[vmx_key] = VMInfo(vmx_path, ip=ip, running=True)
        print(f"[vm] 已记住 {Path(vmx_path).stem} 的 IP: {ip}")

    def _load_ip_cache(self) -> dict:
        """加载持久化 IP 缓存"""
        try:
            if _IP_CACHE_FILE.exists():
                return json.loads(_IP_CACHE_FILE.read_text())
        except Exception as e:
            logger.warning(f"加载 IP 缓存失败: {e}")
        return {}

    def _save_ip_cache(self, cache: dict) -> None:
        """保存持久化 IP 缓存"""
        try:
            _IP_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _IP_CACHE_FILE.write_text(json.dumps(cache, indent=2))
        except Exception as e:
            logger.error(f"保存 IP 缓存失败: {e}")

    # ── 内部：vmrun 封装 ──────────────────────────────────────────

    def _find_vmrun(self) -> str:
        """自动查找 vmrun.exe"""
        for p in _VMRUN_CANDIDATES:
            if os.path.exists(p):
                return p
        found = shutil.which("vmrun")
        if found:
            return found
        raise FileNotFoundError(
            "未找到 vmrun.exe，请安装 VMware Workstation 或指定路径"
        )

    def _vmrun(self, *args, timeout: int = 30) -> int:
        """执行 vmrun 命令，返回退出码"""
        if not self.vmrun:
            return -1
        cmd = [self.vmrun] + list(args)
        try:
            result = subprocess.run(cmd, timeout=timeout,
                                    capture_output=True, text=True)
            return result.returncode
        except subprocess.TimeoutExpired:
            return -1
        except Exception:
            return -1

    def _vmrun_with_cred(self, gu: str, gp: str, subcmd: str,
                          vmx: str, *extra, timeout: int = 30) -> Tuple[int, str]:
        """带用户凭据的 vmrun 调用，返回 (exit_code, stdout)"""
        cmd = [self.vmrun, "-gu", gu, "-gp", gp, subcmd, vmx] + list(extra)
        try:
            result = subprocess.run(cmd, timeout=timeout,
                                    capture_output=True, text=True)
            return result.returncode, result.stdout
        except subprocess.TimeoutExpired:
            return -1, ""
        except Exception:
            return -1, ""

    def _is_running(self, vmx_path: str) -> bool:
        """检查 VM 是否已在运行"""
        running = self.list_running()
        vmx_norm = str(Path(vmx_path)).lower()
        return any(str(Path(p)).lower() == vmx_norm for p in running)

    def _start(self, vmx_path: str) -> bool:
        """启动 VM（nogui 模式）"""
        return self._vmrun("start", vmx_path, "nogui") == 0

    # ── 内部：凭据探测 ────────────────────────────────────────────

    def _wait_for_tools(self, vmx_path: str,
                         timeout: int = 30) -> Optional[Tuple[str, str]]:
        """等待 VMware Tools 就绪，返回有效凭据"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            cred = self._find_valid_credential(vmx_path)
            if cred:
                return cred
            time.sleep(3)
        return None

    def _find_valid_credential(self, vmx_path: str) -> Optional[Tuple[str, str]]:
        """尝试所有预设凭据，返回第一个有效的"""
        for gu, gp in _DEFAULT_CREDENTIALS:
            code, out = self._vmrun_with_cred(
                gu, gp, "listProcessesInGuest", vmx_path, timeout=10
            )
            if code == 0 and "Process list:" in out:
                return (gu, gp)
        return None

    # ── 内部：IP 探测 ─────────────────────────────────────────────

    def _get_ip(self, vmx_path: str,
                cred: Optional[Tuple[str, str]]) -> Optional[str]:
        """
        多策略 IP 探测：
        1. 通过 vmrun 读取靶机内部 ip addr（如果 cred 有效）
        2. 扫描 VMware 各网段（ping sweep）
        3. ARP 表查询靶机 MAC
        """
        # 策略1：vmrun 内部读取
        if cred:
            ip = self._get_ip_via_vmrun(vmx_path, cred)
            if ip:
                return ip

        # 策略2：ping sweep（VMware 网段）
        mac = self._get_vm_mac(vmx_path)
        ip = self._ping_sweep_find(mac)
        if ip:
            return ip

        return None

    def _get_ip_via_vmrun(self, vmx_path: str,
                           cred: Tuple[str, str]) -> Optional[str]:
        """
        通过 runScriptInGuest 让靶机 ping 宿主机，
        使宿主机 ARP 表更新，然后通过 MAC 查询精确 IP。
        """
        gu, gp = cred
        mac = self._get_vm_mac(vmx_path)

        # 让靶机向宿主机各网关 ping 一次，目的是触发 ARP 更新
        host_gateways = " ".join(
            f"192.168.{x}.1" for x in ["23", "184", "56"]
        )
        script = f"for gw in {host_gateways}; do ping -c1 -W1 $gw 2>/dev/null; done"
        self._vmrun_with_cred(
            gu, gp, "runScriptInGuest", vmx_path, "", script, timeout=15
        )
        time.sleep(2)

        # 现在通过 ARP 表查找靶机 IP
        if mac:
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True, timeout=5
            )
            arp_out = result.stdout.lower()
            mac_clean = mac.replace(":", "").replace("-", "").lower()
            for line in arp_out.splitlines():
                line_clean = line.replace(":", "").replace("-", "")
                if mac_clean in line_clean:
                    ip_m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if ip_m:
                        return ip_m.group(1)
        return None  # 由 ping sweep 接力

    def _get_vm_mac(self, vmx_path: str) -> Optional[str]:
        """从 VMX 文件读取网卡 MAC 地址"""
        try:
            with open(vmx_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            m = re.search(r'ethernet0\.generatedAddress\s*=\s*"([^"]+)"', content)
            if m:
                return m.group(1).lower()
        except Exception:
            pass
        return None

    def _ping_sweep_find(self, mac: Optional[str] = None) -> Optional[str]:
        """
        对 VMware 网段做 ping sweep，找到靶机 IP。
        如果知道 MAC，通过 ARP 精确匹配；否则返回新增的活跃 IP。
        """
        for subnet in _VMWARE_SUBNETS:
            ip = self._sweep_subnet(subnet, mac)
            if ip:
                return ip
        return None

    def _sweep_subnet(self, subnet: str,
                       target_mac: Optional[str] = None) -> Optional[str]:
        """ping 扫描一个 /24 子网"""
        active = []
        for i in range(_SCAN_RANGE_START, _SCAN_RANGE_END + 1):
            ip = f"{subnet}.{i}"
            if self._ping_once(ip):
                active.append(ip)

        if not active:
            return None

        if target_mac:
            # 通过 ARP 表找 MAC 匹配的 IP（精确匹配，不猜测）
            arp_ip = self._arp_lookup(target_mac, active)
            if arp_ip:
                return arp_ip
            # 有 MAC 但没匹配到：靶机可能还没响应 ARP，返回 None
            return None

        # 没有 MAC 信息时才做 fallback（返回排除网关后的最后一个活跃 IP）
        known_gw = {f"{subnet}.1", f"{subnet}.2"}
        candidates = [ip for ip in active if ip not in known_gw]
        return candidates[-1] if candidates else None

    def _ping_once(self, ip: str, timeout_ms: int = 500) -> bool:
        """单次 ping 检测"""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", str(timeout_ms), ip],
                    capture_output=True, timeout=2
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip],
                    capture_output=True, timeout=2
                )
            return result.returncode == 0
        except Exception:
            return False

    def _arp_lookup(self, mac: str, candidates: List[str]) -> Optional[str]:
        """查询 ARP 表，找 MAC 对应的 IP（同时处理冒号/连字符格式）"""
        try:
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True, timeout=5
            )
            arp_out = result.stdout.lower()
            # 统一为无分隔符形式进行匹配
            mac_clean = mac.replace(":", "").replace("-", "").lower()
            for line in arp_out.splitlines():
                # 去掉分隔符后检查 MAC 是否在这一行
                line_clean = line.replace(":", "").replace("-", "")
                if mac_clean in line_clean:
                    # 从原始行提取 IP
                    ip_m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if ip_m:
                        found_ip = ip_m.group(1)
                        # 必须在 candidates 内（限定在扫描的子网中）
                        if found_ip in candidates or not candidates:
                            return found_ip
        except Exception:
            pass
        return None

    # ── 内部：网络注入 ────────────────────────────────────────────

    def _inject_network(self, vmx_path: str,
                         cred: Tuple[str, str]) -> Optional[str]:
        """
        自动为靶机注入网络配置。
        策略（按成功率排序）：
        1. 给 VMX 添加第二张 NAT 网卡（eth1/ens34），重启后 DHCP 自动获取
        2. runScriptInGuest 尝试 dhclient ens33（setuid 环境可能有效）
        3. 扫描所有子网，包括 VirtualBox 静态地址段
        """
        gu, gp = cred
        vmx_net_type = self._get_vmx_network_type(vmx_path)
        target_subnet = "192.168.23" if vmx_net_type == "nat" else "192.168.184"

        # ── 策略1：在 VMX 中添加第二张 NAT 网卡 ──
        eth1_added = self._add_second_nic(vmx_path)
        if eth1_added:
            print("[vm] 已添加第二张 NAT 网卡，重启靶机以使网卡生效...")
            self._vmrun("reset", vmx_path, "soft")
            time.sleep(30)  # 等待系统重启

            # 重启后重新获取凭据
            new_cred = self._wait_for_tools(vmx_path, timeout=40)
            if new_cred:
                gu, gp = new_cred
                # 让第二张网卡 DHCP
                script2 = (
                    "dhclient ens34 2>/dev/null; "
                    "dhclient eth1 2>/dev/null; "
                    "sleep 3"
                )
                self._vmrun_with_cred(gu, gp, "runScriptInGuest",
                                       vmx_path, "", script2, timeout=15)
                time.sleep(5)

        # ── 策略2：runScript 尝试 dhclient ens33 ──
        script = (
            "dhclient ens33 2>/dev/null; "
            "dhclient eth0 2>/dev/null; "
            "sleep 4; "
            "sudo -n dhclient ens33 2>/dev/null; "
            "sudo -n service apache2 restart 2>/dev/null"
        )
        self._vmrun_with_cred(
            gu, gp, "runScriptInGuest", vmx_path, "", script, timeout=20
        )

        # 等待网络稳定
        time.sleep(_DHCP_WAIT)

        # ── 策略3：扫描所有可能子网（含 VirtualBox 段）──
        mac = self._get_vm_mac(vmx_path)
        for subnet in [target_subnet, "192.168.184", "192.168.23", "192.168.56"]:
            ip = self._sweep_subnet(subnet, mac)
            if ip:
                if self._verify_http(ip):
                    return ip
                return ip

        return None

    def _add_second_nic(self, vmx_path: str) -> bool:
        """
        在 VMX 文件中添加第二张 NAT 网卡（ethernet1）。
        靶机重启后 Linux 会自动识别为 ens34/eth1，可 DHCP 获取 VMware NAT IP。
        只有在 ethernet1 不存在时才添加。
        """
        try:
            with open(vmx_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 已经有 ethernet1，不重复添加
            if "ethernet1.present" in content.lower():
                return False

            nic2_config = (
                '\nethernet1.present = "TRUE"\n'
                'ethernet1.virtualDev = "e1000"\n'
                'ethernet1.connectionType = "nat"\n'
                'ethernet1.startConnected = "TRUE"\n'
                'ethernet1.addressType = "generated"\n'
            )
            with open(vmx_path, "a", encoding="utf-8") as f:
                f.write(nic2_config)

            print("[vm] ethernet1 (NAT) 已写入 VMX")
            return True

        except Exception as e:
            print(f"[vm] 添加第二张网卡失败: {e}")
            return False

    def _get_vmx_network_type(self, vmx_path: str) -> str:
        """从 VMX 读取网络类型"""
        try:
            with open(vmx_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            m = re.search(r'ethernet0\.connectionType\s*=\s*"([^"]+)"', content)
            if m:
                return m.group(1).lower()
        except Exception:
            pass
        return "nat"

    def _verify_http(self, ip: str, port: int = 80, timeout: int = 4) -> bool:
        """快速检查靶机 HTTP 端口是否可达"""
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
            return True
        except Exception:
            return False


# ── 单例 ──────────────────────────────────────────────────────────

_manager: Optional[VMManager] = None


def get_vm_manager() -> VMManager:
    global _manager
    if _manager is None:
        try:
            _manager = VMManager()
        except FileNotFoundError:
            _manager = VMManager.__new__(VMManager)
            _manager.vmrun = ""
            _manager._vm_cache = {}
    return _manager
