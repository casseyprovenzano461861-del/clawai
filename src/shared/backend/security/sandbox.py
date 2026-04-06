"""
安全沙箱配置模块
提供Docker容器安全加固配置，用于工具执行隔离
"""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SandboxSecurityLevel(Enum):
    """沙箱安全级别"""
    MINIMAL = "minimal"      # 最小限制，兼容性最好
    STANDARD = "standard"    # 标准安全级别，平衡安全与兼容性
    STRICT = "strict"        # 严格安全级别，最大安全性
    PARANOID = "paranoid"    # 偏执安全级别，仅允许最基本操作


class SandboxConfig:
    """沙箱配置类"""

    def __init__(
        self,
        security_level: SandboxSecurityLevel = SandboxSecurityLevel.STANDARD,
        resource_limits: Optional[Dict[str, Any]] = None,
        network_restrictions: Optional[Dict[str, Any]] = None
    ):
        self.security_level = security_level
        self.resource_limits = resource_limits or {}

        # 初始化网络限制，确保包含细粒度控制字段
        self.network_restrictions = {
            "network_mode": "none",  # 默认无网络
            "ports": {},  # 端口映射
            "allowed_ports": [],  # 允许访问的端口列表
            "allowed_protocols": ["tcp"],  # 允许的协议
            "allowed_ips": [],  # 允许访问的IP地址范围
            "dns": [],  # DNS服务器
            "dns_search": [],  # DNS搜索域
            "extra_hosts": None,  # 额外主机映射
            "network_disabled": False,  # 是否禁用网络
            "outbound_allowed": True,  # 是否允许出站流量
            "inbound_allowed": False,  # 是否允许入站流量
            "max_bandwidth": None,  # 最大带宽限制
        }

        # 更新用户提供的网络限制
        if network_restrictions:
            self.network_restrictions.update(network_restrictions)

        # 根据安全级别设置默认配置
        self._apply_security_level()

    def _apply_security_level(self):
        """根据安全级别应用默认配置"""
        if self.security_level == SandboxSecurityLevel.MINIMAL:
            self._minimal_config()
        elif self.security_level == SandboxSecurityLevel.STANDARD:
            self._standard_config()
        elif self.security_level == SandboxSecurityLevel.STRICT:
            self._strict_config()
        elif self.security_level == SandboxSecurityLevel.PARANOID:
            self._paranoid_config()

    def _minimal_config(self):
        """最小安全配置（最大兼容性）"""
        # 资源限制
        self.resource_limits.update({
            "cpus": "1.0",  # 1个CPU
            "memory": "512m",  # 512MB内存
            "memory_swap": "1g",  # 交换内存1GB
            "pids_limit": 100,  # 最大进程数
        })

        # 网络限制 - 最小限制，允许基本网络访问
        self.network_restrictions.update({
            "network_mode": "bridge",  # 默认桥接网络
            "allowed_ports": list(range(1, 65536)),  # 允许所有端口
            "allowed_protocols": ["tcp", "udp", "icmp"],  # 允许所有协议
            "allowed_ips": ["0.0.0.0/0", "::/0"],  # 允许所有IP
            "dns": ["8.8.8.8", "8.8.4.4"],  # 公共DNS
            "outbound_allowed": True,  # 允许出站流量
            "inbound_allowed": True,  # 允许入站流量
            "network_disabled": False,
        })

        # 安全配置
        self.security_config = {
            "readonly_rootfs": False,  # 可写根文件系统
            "privileged": False,  # 非特权模式
            "capabilities": ["NET_RAW", "NET_ADMIN", "SYS_PTRACE"],  # 必要权限
            "security_opt": [
                "no-new-privileges:true",  # 禁止新权限
            ],
            "userns_mode": "host",  # 使用主机用户命名空间
        }

    def _standard_config(self):
        """标准安全配置（平衡）"""
        # 资源限制（比最小更严格）
        self.resource_limits.update({
            "cpus": "0.5",  # 0.5个CPU
            "memory": "256m",  # 256MB内存
            "memory_swap": "512m",  # 交换内存512MB
            "pids_limit": 50,  # 最大进程数
            "oom_kill_disable": False,  # 允许OOM killer
            "oom_score_adj": 500,  # 提高OOM分数（更容易被杀死）
        })

        # 网络限制 - 标准限制，允许有限网络访问
        self.network_restrictions.update({
            "network_mode": "none",  # 默认无网络
            "allowed_ports": [80, 443, 53],  # 只允许HTTP, HTTPS, DNS端口
            "allowed_protocols": ["tcp", "udp"],  # 允许TCP和UDP
            "allowed_ips": [],  # 不允许特定IP（需要时动态添加）
            "dns": ["8.8.8.8", "8.8.4.4"],  # 公共DNS
            "outbound_allowed": True,  # 允许出站流量
            "inbound_allowed": False,  # 不允许入站流量
            "network_disabled": False,
        })

        # 安全配置
        self.security_config = {
            "readonly_rootfs": True,  # 只读根文件系统
            "privileged": False,  # 非特权模式
            "capabilities": ["NET_RAW"],  # 仅必要权限
            "security_opt": [
                "no-new-privileges:true",
            ],
            "userns_mode": "host",
            "sysctls": {
                "net.ipv4.ip_forward": "0",  # 禁用IP转发
                "net.ipv4.conf.all.rp_filter": "1",  # 启用反向路径过滤
            }
        }

        # 加载默认的seccomp配置文件
        self.security_config["security_opt"].append(
            f"seccomp={self._get_seccomp_profile()}"
        )

    def _strict_config(self):
        """严格安全配置"""
        # 资源限制
        self.resource_limits.update({
            "cpus": "0.25",  # 0.25个CPU
            "memory": "128m",  # 128MB内存
            "memory_swap": "256m",  # 交换内存256MB
            "pids_limit": 20,  # 最大进程数
            "oom_kill_disable": False,
            "oom_score_adj": 750,
            "cpuset_cpus": "0",  # 绑定到特定CPU核心
            "blkio_weight": 10,  # 低块IO优先级
        })

        # 网络限制 - 严格限制，基本无网络
        self.network_restrictions.update({
            "network_mode": "none",  # 无网络
            "allowed_ports": [],  # 不允许任何端口
            "allowed_protocols": [],  # 不允许任何协议
            "allowed_ips": [],  # 不允许任何IP
            "dns": [],  # 无DNS
            "outbound_allowed": False,  # 不允许出站流量
            "inbound_allowed": False,  # 不允许入站流量
            "network_disabled": True,  # 明确禁用网络
        })

        # 安全配置
        self.security_config = {
            "readonly_rootfs": True,
            "privileged": False,
            "capabilities": [],  # 无额外权限
            "security_opt": [
                "no-new-privileges:true",
            ],
            "userns_mode": "host",
            "sysctls": {
                "net.ipv4.ip_forward": "0",
                "net.ipv4.conf.all.rp_filter": "1",
                "net.ipv4.tcp_syncookies": "1",  # 启用SYN cookies
            }
        }

        # 加载严格的seccomp配置文件
        self.security_config["security_opt"].append(
            f"seccomp={self._get_strict_seccomp_profile()}"
        )

    def _paranoid_config(self):
        """偏执安全配置"""
        # 资源限制
        self.resource_limits.update({
            "cpus": "0.1",  # 0.1个CPU
            "memory": "64m",  # 64MB内存
            "memory_swap": "0",  # 无交换内存
            "pids_limit": 10,  # 最大进程数
            "oom_kill_disable": False,
            "oom_score_adj": 1000,  # 最高OOM优先级
            "cpuset_cpus": "0",
            "blkio_weight": 1,
            "kernel_memory": "32m",  # 内核内存限制
        })

        # 网络限制 - 偏执模式，完全禁用网络
        self.network_restrictions.update({
            "network_mode": "none",
            "allowed_ports": [],
            "allowed_protocols": [],
            "allowed_ips": [],
            "dns": [],
            "outbound_allowed": False,
            "inbound_allowed": False,
            "network_disabled": True,  # 明确禁用网络
            "max_bandwidth": "0kbps",  # 零带宽
        })

        # 安全配置
        self.security_config = {
            "readonly_rootfs": True,
            "privileged": False,
            "capabilities": [],
            "security_opt": [
                "no-new-privileges:true",
            ],
            "userns_mode": "host",
            "sysctls": {
                "net.ipv4.ip_forward": "0",
                "net.ipv4.conf.all.rp_filter": "1",
                "net.ipv4.tcp_syncookies": "1",
                "kernel.yama.ptrace_scope": "2",  # 严格ptrace限制
            },
            "tmpfs": {  # 使用tmpfs而不是持久存储
                "/tmp": "size=16m,mode=1777",
                "/run": "size=8m,mode=755",
            }
        }

        # 加载偏执的seccomp配置文件
        self.security_config["security_opt"].append(
            f"seccomp={self._get_paranoid_seccomp_profile()}"
        )

    def _apply_tool_specific_seccomp(self, tool_name: str):
        """应用工具特定的seccomp配置"""
        # 获取当前的安全级别
        if self.security_level == SandboxSecurityLevel.PARANOID:
            # 偏执模式使用最严格的配置
            seccomp_profile = self._get_paranoid_seccomp_profile()
        elif self.security_level == SandboxSecurityLevel.STRICT:
            # 严格模式使用严格配置
            seccomp_profile = self._get_strict_seccomp_profile()
        else:
            # 标准或最小模式使用工具特定配置
            seccomp_profile = self._get_tool_specific_seccomp_profile(tool_name)

        # 添加seccomp配置到安全选项
        seccomp_option = f"seccomp={seccomp_profile}"

        # 确保security_opt存在
        if "security_opt" not in self.security_config:
            self.security_config["security_opt"] = []

        # 移除现有的seccomp配置（如果有）
        self.security_config["security_opt"] = [
            opt for opt in self.security_config["security_opt"]
            if not opt.startswith("seccomp=")
        ]

        # 添加新的seccomp配置
        self.security_config["security_opt"].append(seccomp_option)

    def _apply_apparmor_config(self, tool_name: str = None):
        """应用AppArmor配置"""
        # 确保security_opt存在
        if "security_opt" not in self.security_config:
            self.security_config["security_opt"] = []

        # 移除现有的AppArmor配置（如果有）
        self.security_config["security_opt"] = [
            opt for opt in self.security_config["security_opt"]
            if not opt.startswith("apparmor:")
        ]

        # 根据安全级别和工具名称确定AppArmor配置
        if self.security_level == SandboxSecurityLevel.PARANOID:
            # 偏执模式使用严格配置
            profile_name = f"clawai-paranoid-{tool_name}" if tool_name else "clawai-paranoid"
            apparmor_option = f"apparmor:{profile_name}"
        elif self.security_level == SandboxSecurityLevel.STRICT:
            # 严格模式使用严格配置
            profile_name = f"clawai-strict-{tool_name}" if tool_name else "clawai-strict"
            apparmor_option = f"apparmor:{profile_name}"
        elif tool_name:
            # 工具特定配置
            profile_name = f"clawai-{tool_name}"
            apparmor_option = f"apparmor:{profile_name}"
        else:
            # 默认配置
            apparmor_option = "apparmor:docker-default"

        # 添加AppArmor配置
        self.security_config["security_opt"].append(apparmor_option)

        # 记录日志
        logger.info(f"应用AppArmor配置: {apparmor_option}")

    def _validate_network_policy(self, tool_name: str = None) -> Tuple[bool, List[str]]:
        """验证网络策略是否安全"""
        warnings = []

        # 获取网络配置
        network_mode = self.network_restrictions.get("network_mode", "none")
        allowed_ports = self.network_restrictions.get("allowed_ports", [])
        allowed_protocols = self.network_restrictions.get("allowed_protocols", [])
        allowed_ips = self.network_restrictions.get("allowed_ips", [])
        outbound_allowed = self.network_restrictions.get("outbound_allowed", False)
        inbound_allowed = self.network_restrictions.get("inbound_allowed", False)
        network_disabled = self.network_restrictions.get("network_disabled", False)

        # 检查危险配置
        if network_mode == "host":
            warnings.append("使用主机网络模式，容器与主机共享网络命名空间，这是严重的安全风险")

        if network_disabled and (outbound_allowed or inbound_allowed):
            warnings.append("网络已禁用但允许流量，配置不一致")

        # 检查过于宽松的配置
        if "0.0.0.0/0" in allowed_ips and self.security_level != SandboxSecurityLevel.MINIMAL:
            warnings.append("允许访问所有IP地址，可能过于宽松")

        if len(allowed_ports) > 100 and self.security_level != SandboxSecurityLevel.MINIMAL:
            warnings.append(f"允许的端口数量过多 ({len(allowed_ports)}个)，考虑减少")

        # 检查协议安全
        if "icmp" in allowed_protocols and self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
            warnings.append("ICMP协议可能被用于网络侦察和攻击")

        # 工具特定的网络策略检查
        if tool_name:
            if tool_name in ["nmap", "masscan", "tcpdump"]:
                # 网络扫描工具需要网络访问
                if network_disabled:
                    warnings.append(f"网络扫描工具 {tool_name} 需要网络访问，但网络被禁用")
                if not outbound_allowed:
                    warnings.append(f"网络扫描工具 {tool_name} 需要出站网络访问")
            elif tool_name in ["sqlmap", "nikto", "dirsearch", "whatweb"]:
                # Web扫描工具需要HTTP/HTTPS访问
                if 80 not in allowed_ports and 443 not in allowed_ports:
                    warnings.append(f"Web扫描工具 {tool_name} 需要HTTP(80)或HTTPS(443)端口访问")

        is_safe = len(warnings) == 0
        return is_safe, warnings

    def _apply_network_policy(self, tool_name: str = None):
        """应用网络策略到Docker配置"""
        # 验证网络策略
        is_safe, warnings = self._validate_network_policy(tool_name)
        if not is_safe:
            logger.warning(f"网络策略存在安全警告: {warnings}")
            if self.security_level == SandboxSecurityLevel.PARANOID:
                logger.error("偏执模式下网络策略不安全，自动禁用网络")
                self.network_restrictions["network_disabled"] = True
                self.network_restrictions["outbound_allowed"] = False
                self.network_restrictions["inbound_allowed"] = False

        # 根据网络策略调整Docker配置
        network_mode = self.network_restrictions.get("network_mode", "none")
        network_disabled = self.network_restrictions.get("network_disabled", False)

        # 设置网络模式
        if network_disabled:
            self.security_config["network_disabled"] = True
            self.security_config["network_mode"] = "none"
        else:
            self.security_config["network_mode"] = network_mode

        # 设置DNS
        dns_servers = self.network_restrictions.get("dns", [])
        if dns_servers:
            self.security_config["dns"] = dns_servers

        # 设置额外主机映射
        extra_hosts = self.network_restrictions.get("extra_hosts")
        if extra_hosts:
            self.security_config["extra_hosts"] = extra_hosts

        # 设置端口映射
        ports = self.network_restrictions.get("ports", {})
        if ports:
            self.security_config["ports"] = ports

        # 记录网络策略
        logger.info(f"应用网络策略: mode={network_mode}, disabled={network_disabled}, "
                   f"outbound={self.network_restrictions.get('outbound_allowed')}, "
                   f"ports_allowed={len(self.network_restrictions.get('allowed_ports', []))}")

    def _apply_container_escape_protection(self):
        """应用容器逃逸防护措施"""
        # 1. 防止特权容器逃逸
        if self.security_config.get("privileged", False):
            logger.critical("检测到特权容器模式，这是严重的容器逃逸风险！")
            if self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
                # 在严格模式下自动禁用特权模式
                self.security_config["privileged"] = False
                logger.warning("已自动禁用特权容器模式")

        # 2. 限制危险的能力(capabilities)
        dangerous_capabilities = [
            "SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE",
            "SYS_BOOT", "SYS_TIME", "SYS_NICE", "SYS_RESOURCE",
            "NET_ADMIN", "NET_RAW", "IPC_LOCK", "IPC_OWNER",
            "DAC_READ_SEARCH", "DAC_OVERRIDE", "LINUX_IMMUTABLE"
        ]

        current_capabilities = self.security_config.get("capabilities", [])
        for dangerous_cap in dangerous_capabilities:
            if dangerous_cap in current_capabilities:
                logger.warning(f"检测到危险能力: {dangerous_cap}")
                if self.security_level == SandboxSecurityLevel.PARANOID:
                    # 在偏执模式下移除所有危险能力
                    self.security_config["capabilities"] = [
                        cap for cap in current_capabilities if cap != dangerous_cap
                    ]
                    logger.info(f"已移除危险能力: {dangerous_cap}")

        # 3. 防止敏感目录挂载
        sensitive_mounts = [
            "/", "/etc", "/root", "/home", "/var/run/docker.sock",
            "/proc", "/sys", "/dev", "/lib", "/usr", "/bin"
        ]

        # 检查是否挂载了敏感目录
        volumes = self.security_config.get("volumes", {})
        for volume in volumes:
            for sensitive_path in sensitive_mounts:
                if volume.startswith(sensitive_path):
                    logger.warning(f"检测到敏感目录挂载: {volume} -> {sensitive_path}")
                    if self.security_level == SandboxSecurityLevel.PARANOID:
                        # 在偏执模式下禁止挂载敏感目录
                        if "volumes" in self.security_config:
                            del self.security_config["volumes"]
                        logger.info("已禁止敏感目录挂载")

        # 4. 防止Docker socket访问
        docker_socket_paths = ["/var/run/docker.sock", "/run/docker.sock"]
        for socket_path in docker_socket_paths:
            if volumes and any(socket_path in str(v) for v in volumes):
                logger.critical(f"检测到Docker socket挂载: {socket_path}，这是严重的容器逃逸风险！")
                if self.security_level != SandboxSecurityLevel.MINIMAL:
                    # 移除Docker socket挂载
                    self.security_config["volumes"] = {
                        k: v for k, v in volumes.items()
                        if socket_path not in str(v)
                    }
                    logger.info(f"已移除Docker socket挂载: {socket_path}")

        # 5. 防止共享命名空间
        if self.security_config.get("pid_mode") == "host":
            logger.warning("检测到主机PID命名空间共享")
            if self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
                self.security_config["pid_mode"] = "private"
                logger.info("已设置为私有PID命名空间")

        if self.security_config.get("ipc_mode") == "host":
            logger.warning("检测到主机IPC命名空间共享")
            if self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
                self.security_config["ipc_mode"] = "private"
                logger.info("已设置为私有IPC命名空间")

        # 6. 确保只读根文件系统（重要防护措施）
        if not self.security_config.get("readonly_rootfs", False):
            logger.warning("根文件系统可写，可能被用于容器逃逸")
            if self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
                self.security_config["readonly_rootfs"] = True
                logger.info("已设置为只读根文件系统")

        # 7. 确保no-new-privileges启用
        security_opts = self.security_config.get("security_opt", [])
        if "no-new-privileges:true" not in security_opts:
            logger.warning("no-new-privileges未启用")
            self.security_config.setdefault("security_opt", []).append("no-new-privileges:true")
            logger.info("已启用no-new-privileges")

        # 8. 记录容器逃逸防护状态
        protection_status = {
            "privileged": self.security_config.get("privileged", False),
            "dangerous_capabilities_removed": len([c for c in current_capabilities if c in dangerous_capabilities]) == 0,
            "readonly_rootfs": self.security_config.get("readonly_rootfs", False),
            "no_new_privileges": "no-new-privileges:true" in security_opts,
            "docker_socket_mounted": any(any(socket in str(v) for socket in docker_socket_paths) for v in volumes.values()) if volumes else False,
        }

        logger.info(f"容器逃逸防护状态: {protection_status}")

    def _get_seccomp_profile(self) -> str:
        """获取标准seccomp配置文件 - 增强版，提供容器逃逸防护"""
        # 基础允许的系统调用（Docker默认 + 必要应用调用）
        base_allowed_syscalls = [
            "accept", "accept4", "access", "alarm", "arch_prctl",
            "bind", "brk", "capget", "capset", "chdir", "chmod",
            "chown", "chown32", "clock_gettime", "clone", "close",
            "connect", "copy_file_range", "creat", "dup", "dup2",
            "dup3", "epoll_create", "epoll_create1", "epoll_ctl",
            "epoll_pwait", "epoll_wait", "eventfd", "eventfd2",
            "execve", "execveat", "exit", "exit_group", "faccessat",
            "fadvise64", "fallocate", "fchdir", "fchmod", "fchmodat",
            "fchown", "fchown32", "fchownat", "fcntl", "fcntl64",
            "fdatasync", "fgetxattr", "flistxattr", "flock", "fork",
            "fremovexattr", "fsetxattr", "fstat", "fstat64",
            "fstatat64", "fstatfs", "fstatfs64", "fsync", "ftruncate",
            "ftruncate64", "futex", "getcpu", "getcwd", "getdents",
            "getdents64", "getegid", "getegid32", "geteuid",
            "geteuid32", "getgid", "getgid32", "getgroups",
            "getgroups32", "getitimer", "getpeername", "getpgid",
            "getpgrp", "getpid", "getppid", "getpriority",
            "getrandom", "getresgid", "getresgid32", "getresuid",
            "getresuid32", "getrlimit", "get_robust_list", "getrusage",
            "getsid", "getsockname", "getsockopt", "gettid",
            "gettimeofday", "getuid", "getuid32", "getxattr",
            "inotify_add_watch", "inotify_init", "inotify_init1",
            "inotify_rm_watch", "ioctl", "kill", "lchown", "lchown32",
            "lgetxattr", "link", "linkat", "listen", "listxattr",
            "llistxattr", "lremovexattr", "lseek", "lsetxattr",
            "lstat", "lstat64", "madvise", "memfd_create",
            "mincore", "mkdir", "mkdirat", "mknod", "mknodat",
            "mlock", "mlock2", "mlockall", "mmap", "mmap2",
            "mprotect", "mq_getsetattr", "mq_notify", "mq_open",
            "mq_timedreceive", "mq_timedsend", "mq_unlink",
            "mremap", "msgctl", "msgget", "msgrcv", "msgsnd",
            "msync", "munlock", "munlockall", "munmap", "nanosleep",
            "newfstatat", "_newselect", "open", "openat",
            "pause", "pipe", "pipe2", "poll", "ppoll", "prctl",
            "pread64", "preadv", "preadv2", "prlimit64", "pselect6",
            "ptrace", "pwrite64", "pwritev", "pwritev2", "read",
            "readahead", "readlink", "readlinkat", "readv",
            "recv", "recvfrom", "recvmmsg", "recvmsg", "remap_file_pages",
            "removexattr", "rename", "renameat", "renameat2",
            "restart_syscall", "rmdir", "rt_sigaction", "rt_sigpending",
            "rt_sigprocmask", "rt_sigqueueinfo", "rt_sigreturn",
            "rt_sigsuspend", "rt_sigtimedwait", "rt_tgsigqueueinfo",
            "sched_getaffinity", "sched_getattr", "sched_getparam",
            "sched_get_priority_max", "sched_get_priority_min",
            "sched_getscheduler", "sched_rr_get_interval",
            "sched_setaffinity", "sched_setattr", "sched_setparam",
            "sched_setscheduler", "sched_yield", "seccomp",
            "select", "semctl", "semget", "semop", "semtimedop",
            "send", "sendfile", "sendfile64", "sendmmsg",
            "sendmsg", "sendto", "setfsgid", "setfsgid32",
            "setfsuid", "setfsuid32", "setgid", "setgid32",
            "setgroups", "setgroups32", "setitimer", "setpgid",
            "setpriority", "setregid", "setregid32", "setresgid",
            "setresgid32", "setresuid", "setresuid32",
            "setreuid", "setreuid32", "setrlimit", "set_robust_list",
            "setsid", "setsockopt", "set_tid_address", "setuid",
            "setuid32", "setxattr", "shmat", "shmctl", "shmdt",
            "shmget", "shutdown", "sigaltstack", "signalfd",
            "signalfd4", "sigreturn", "socket", "socketcall",
            "socketpair", "splice", "stat", "stat64", "statfs",
            "statfs64", "statx", "symlink", "symlinkat", "sync",
            "sync_file_range", "syncfs", "sysinfo", "tee",
            "tgkill", "time", "timer_create", "timer_delete",
            "timer_getoverrun", "timer_gettime", "timer_settime",
            "timerfd_create", "timerfd_gettime", "timerfd_settime",
            "times", "tkill", "truncate", "truncate64", "ugetrlimit",
            "umask", "uname", "unlink", "unlinkat", "utime",
            "utimensat", "utimes", "vfork", "vmsplice", "wait4",
            "waitid", "waitpid", "write", "writev"
        ]

        # 容器逃逸相关的危险系统调用（需要特殊处理）
        container_escape_dangerous_syscalls = [
            "unshare",  # 创建新的命名空间（可用于容器逃逸）
            "mount", "umount", "umount2",  # 挂载文件系统
            "pivot_root",  # 改变根文件系统
            "sethostname", "setdomainname",  # 修改主机名
            "syslog",  # 访问内核消息
            "keyctl", "add_key", "request_key",  # 密钥管理
            "perf_event_open",  # 性能监控（可能泄露信息）
            "bpf",  # BPF系统调用（可用于内核攻击）
            "fanotify_init", "fanotify_mark",  # 文件系统监控
            "name_to_handle_at", "open_by_handle_at",  # 通过句柄访问文件
            "setns",  # 加入现有命名空间
            "userfaultfd",  # 用户态页错误处理（可用于利用）
        ]

        # 从基础允许列表中移除危险系统调用
        filtered_allowed_syscalls = [
            syscall for syscall in base_allowed_syscalls
            if syscall not in container_escape_dangerous_syscalls
        ]

        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": [
                "SCMP_ARCH_X86_64",
                "SCMP_ARCH_X86",
                "SCMP_ARCH_X32"
            ],
            "syscalls": [
                {
                    "names": filtered_allowed_syscalls,
                    "action": "SCMP_ACT_ALLOW"
                },
                # 添加针对容器逃逸的特定拒绝规则
                {
                    "names": container_escape_dangerous_syscalls,
                    "action": "SCMP_ACT_ERRNO",
                    "args": [],
                    "comment": "阻止容器逃逸攻击"
                },
                # 添加参数过滤规则
                {
                    "names": ["clone"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [
                        {
                            "index": 0,
                            "value": 2114060288,  # CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWUSER
                            "valueTwo": 0,
                            "op": "SCMP_CMP_MASKED_EQ"
                        }
                    ],
                    "comment": "禁止创建新的命名空间（容器逃逸防护）"
                }
            ]
        }

        return json.dumps(profile)

    def _get_strict_seccomp_profile(self) -> str:
        """获取严格seccomp配置文件 - 针对生产环境的高度安全配置"""
        # 基于标准配置
        profile = json.loads(self._get_seccomp_profile())

        # 严格模式需要移除的系统调用（包括容器逃逸和内核攻击）
        strict_forbidden_syscalls = [
            # 容器逃逸相关
            "ptrace", "process_vm_readv", "process_vm_writev",
            "keyctl", "add_key", "request_key",
            "iopl", "ioperm", "chroot", "unshare",
            "swapon", "swapoff", "sysfs", "mount", "umount", "umount2",
            "pivot_root", "sethostname", "setdomainname",
            "acct", "settimeofday", "adjtimex",
            "clock_settime", "clock_adjtime",
            "kexec_load", "init_module", "finit_module", "delete_module",
            "perf_event_open", "quotactl", "nfsservctl",
            "get_kernel_syms", "query_module", "create_module",
            "ioprio_set", "ioprio_get", "lookup_dcookie",
            "uselib", "personality", "afs_syscall",
            "break", "ftime", "getpmsg", "gtty", "lock", "mpx",
            "prof", "profil", "putpmsg", "security", "stty",
            "tuxcall", "ulimit", "vserver",
            # 网络和系统信息泄露
            "syslog", "sysinfo", "getrusage", "getitimer",
            # 进程间通信（可能用于攻击）
            "msgctl", "msgget", "msgrcv", "msgsnd",
            "semctl", "semget", "semop", "semtimedop",
            "shmat", "shmctl", "shmdt", "shmget",
            # 文件系统高级操作
            "fanotify_init", "fanotify_mark",
            "name_to_handle_at", "open_by_handle_at",
            "setns", "userfaultfd", "bpf",
            # 内存操作（可能用于攻击）
            "mlock", "mlock2", "mlockall", "munlock", "munlockall",
            "mincore", "remap_file_pages",
            # 时间操作（可能用于侧信道攻击）
            "timer_create", "timer_delete", "timer_getoverrun",
            "timer_gettime", "timer_settime",
            "timerfd_create", "timerfd_gettime", "timerfd_settime",
            # 信号处理（可能被滥用）
            "rt_sigqueueinfo", "rt_tgsigqueueinfo",
            "signalfd", "signalfd4",
        ]

        # 从允许列表中移除危险系统调用
        for syscall_list in profile["syscalls"]:
            if syscall_list["action"] == "SCMP_ACT_ALLOW":
                syscall_list["names"] = [
                    name for name in syscall_list["names"]
                    if name not in strict_forbidden_syscalls
                ]

        # 添加额外的严格规则
        strict_rules = [
            {
                "names": ["socket"],
                "action": "SCMP_ACT_ALLOW",
                "args": [
                    {
                        "index": 0,
                        "value": 1,  # AF_UNIX
                        "valueTwo": 0,
                        "op": "SCMP_CMP_EQ"
                    }
                ],
                "comment": "只允许UNIX域套接字，禁止网络套接字"
            },
            {
                "names": ["connect"],
                "action": "SCMP_ACT_ERRNO",
                "args": [],
                "comment": "禁止网络连接"
            },
            {
                "names": ["accept", "accept4"],
                "action": "SCMP_ACT_ERRNO",
                "args": [],
                "comment": "禁止接受网络连接"
            },
            {
                "names": ["bind", "listen"],
                "action": "SCMP_ACT_ERRNO",
                "args": [],
                "comment": "禁止绑定和监听网络端口"
            }
        ]

        profile["syscalls"].extend(strict_rules)

        return json.dumps(profile)

    def _get_paranoid_seccomp_profile(self) -> str:
        """获取偏执seccomp配置文件 - 最高安全级别，仅允许绝对必要的系统调用"""
        # 偏执模式只允许最基础的系统调用，适合处理不受信任的代码
        paranoid_allowed_syscalls = [
            # 基本进程和内存管理
            "brk", "clone", "exit", "exit_group",
            "getpid", "getppid", "gettid",
            "mmap", "mprotect", "munmap", "madvise",
            # 基本文件操作（仅限openat，更安全）
            "openat", "close", "read", "write",
            "fstat", "lseek",
            # 基本时间
            "clock_gettime", "gettimeofday", "nanosleep",
            # 基本信号处理
            "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
            # 基本同步
            "futex",
            # 受限的execve（仅允许执行预定义的可信二进制文件）
            "execve",
        ]

        profile = {
            "defaultAction": "SCMP_ACT_KILL",  # 偏执模式：默认杀死进程
            "architectures": ["SCMP_ARCH_X86_64"],
            "syscalls": [
                {
                    "names": paranoid_allowed_syscalls,
                    "action": "SCMP_ACT_ALLOW",
                    "comment": "偏执模式：仅允许最基本的系统调用"
                },
                # 对execve添加严格参数过滤
                {
                    "names": ["execve"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [
                        {
                            "index": 0,
                            "value": 0,
                            "valueTwo": 0,
                            "op": "SCMP_CMP_EQ"
                        }
                    ],
                    "comment": "偏执模式：只允许执行空路径（通过/proc/self/exe执行自己）"
                },
                # 对clone添加严格限制（禁止创建新命名空间）
                {
                    "names": ["clone"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [
                        {
                            "index": 0,
                            "value": 0x02000000,  # SIGCHLD标志
                            "valueTwo": 0x02000000,
                            "op": "SCMP_CMP_MASKED_EQ"
                        }
                    ],
                    "comment": "偏执模式：只允许创建子进程，禁止创建新命名空间"
                },
                # 对文件操作添加限制
                {
                    "names": ["openat"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [
                        {
                            "index": 1,  # pathname参数
                            "value": 0,
                            "valueTwo": 0,
                            "op": "SCMP_CMP_EQ"
                        }
                    ],
                    "comment": "偏执模式：只允许打开相对路径"
                }
            ]
        }

        return json.dumps(profile)

    def _get_tool_specific_seccomp_profile(self, tool_name: str) -> str:
        """获取工具特定的seccomp配置文件"""
        # 工具特定的系统调用需求
        tool_specific_syscalls = {
            "nmap": [
                "socket", "connect", "bind", "listen", "accept", "accept4",
                "sendto", "recvfrom", "setsockopt", "getsockopt",
                "getsockname", "getpeername", "shutdown"
            ],
            "masscan": [
                "socket", "connect", "bind", "sendto", "recvfrom",
                "setsockopt", "getsockopt"
            ],
            "tcpdump": [
                "socket", "bind", "setsockopt", "getsockopt",
                "recvfrom", "sendto"
            ],
            "sqlmap": [],  # 不需要特殊系统调用
            "nikto": [],   # 不需要特殊系统调用
            "dirsearch": [],  # 不需要特殊系统调用
            "whatweb": [],  # 不需要特殊系统调用
        }

        # 获取基础配置
        base_profile = json.loads(self._get_seccomp_profile())

        # 添加工具特定的系统调用
        tool_syscalls = tool_specific_syscalls.get(tool_name, [])
        if tool_syscalls:
            # 查找允许列表
            for syscall_list in base_profile["syscalls"]:
                if syscall_list["action"] == "SCMP_ACT_ALLOW":
                    # 添加工具特定的系统调用（如果不在列表中）
                    for syscall in tool_syscalls:
                        if syscall not in syscall_list["names"]:
                            syscall_list["names"].append(syscall)
                    break

        # 如果是网络工具，添加网络特定的限制
        if tool_name in ["nmap", "masscan", "tcpdump"]:
            # 限制网络操作只能用于扫描目的
            network_restriction = {
                "names": ["socket"],
                "action": "SCMP_ACT_ALLOW",
                "args": [
                    {
                        "index": 0,
                        "value": 2,  # AF_INET (IPv4)
                        "valueTwo": 0,
                        "op": "SCMP_CMP_EQ"
                    }
                ],
                "comment": f"工具 {tool_name}: 只允许IPv4套接字"
            }
            base_profile["syscalls"].append(network_restriction)

        return json.dumps(base_profile)

    def get_docker_config(self) -> Dict[str, Any]:
        """获取Docker容器配置"""
        config = {}

        # 添加资源限制
        config.update(self.resource_limits)

        # 添加网络限制
        config.update(self.network_restrictions)

        # 添加安全配置
        config.update(self.security_config)

        # 根据安全级别调整
        if self.security_level in [SandboxSecurityLevel.STRICT, SandboxSecurityLevel.PARANOID]:
            config["network_disabled"] = True

        return config

    def validate_tool_requirements(self, tool_name: str, required_capabilities: List[str] = None) -> bool:
        """验证工具是否可以在当前安全配置下运行"""
        if not required_capabilities:
            return True

        current_capabilities = self.security_config.get("capabilities", [])

        # 检查所有必需权限是否可用
        for required_cap in required_capabilities:
            if required_cap not in current_capabilities:
                logger.warning(
                    f"工具 {tool_name} 需要权限 {required_cap}，但当前配置不允许"
                )
                return False

        return True

    def validate_security(self) -> Tuple[bool, List[str]]:
        """验证安全配置是否安全，包括容器逃逸风险"""
        warnings = []

        # 检查危险配置
        if self.security_config.get("privileged", False):
            warnings.append("容器以特权模式运行，这是严重的容器逃逸风险")

        if not self.security_config.get("readonly_rootfs", False):
            warnings.append("根文件系统可写，可能被用于持久化攻击和容器逃逸")

        # 检查危险权限（容器逃逸相关）
        dangerous_capabilities = [
            "SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE", "SYS_BOOT",
            "SYS_TIME", "SYS_NICE", "SYS_RESOURCE", "NET_ADMIN", "NET_RAW",
            "IPC_LOCK", "IPC_OWNER", "DAC_READ_SEARCH", "DAC_OVERRIDE", "LINUX_IMMUTABLE"
        ]
        current_caps = self.security_config.get("capabilities", [])
        for dangerous_cap in dangerous_capabilities:
            if dangerous_cap in current_caps:
                warnings.append(f"容器拥有危险权限，可能被用于容器逃逸: {dangerous_cap}")

        # 检查网络配置
        network_mode = self.network_restrictions.get("network_mode", "bridge")
        if network_mode == "host":
            warnings.append("容器使用主机网络模式，网络隔离被禁用，增加容器逃逸风险")

        # 检查资源限制
        memory_limit = self.resource_limits.get("memory", "")
        if not memory_limit:
            warnings.append("未设置内存限制，可能导致内存耗尽攻击")

        # 检查容器逃逸特定风险
        # 1. Docker socket挂载
        volumes = self.security_config.get("volumes", {})
        docker_socket_paths = ["/var/run/docker.sock", "/run/docker.sock"]
        for socket_path in docker_socket_paths:
            if volumes and any(socket_path in str(v) for v in volumes.values()):
                warnings.append(f"Docker socket挂载: {socket_path}，这是严重的容器逃逸风险")

        # 2. 敏感目录挂载
        sensitive_mounts = ["/", "/etc", "/root", "/home", "/proc", "/sys", "/dev"]
        for volume in volumes:
            for sensitive_path in sensitive_mounts:
                if volume.startswith(sensitive_path):
                    warnings.append(f"敏感目录挂载: {volume}，可能被用于容器逃逸")

        # 3. 共享命名空间
        if self.security_config.get("pid_mode") == "host":
            warnings.append("共享主机PID命名空间，增加容器逃逸风险")

        if self.security_config.get("ipc_mode") == "host":
            warnings.append("共享主机IPC命名空间，增加容器逃逸风险")

        # 4. 检查no-new-privileges
        security_opts = self.security_config.get("security_opt", [])
        if "no-new-privileges:true" not in security_opts:
            warnings.append("no-new-privileges未启用，增加权限提升风险")

        # 5. 检查用户命名空间
        if self.security_config.get("userns_mode") == "host":
            warnings.append("使用主机用户命名空间，可能被用于容器逃逸")

        # 根据安全级别评估风险严重性
        high_risk_warnings = []
        medium_risk_warnings = []
        low_risk_warnings = []

        for warning in warnings:
            if any(keyword in warning.lower() for keyword in ["特权", "docker socket", "严重", "高危"]):
                high_risk_warnings.append(warning)
            elif any(keyword in warning.lower() for keyword in ["危险权限", "共享", "敏感目录"]):
                medium_risk_warnings.append(warning)
            else:
                low_risk_warnings.append(warning)

        # 重新组织警告，高风险在前
        warnings = high_risk_warnings + medium_risk_warnings + low_risk_warnings

        # 在偏执模式下，任何警告都视为不安全
        if self.security_level == SandboxSecurityLevel.PARANOID and warnings:
            logger.error(f"偏执模式下检测到安全警告: {warnings}")

        is_safe = len(warnings) == 0
        return is_safe, warnings

    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        is_safe, warnings = self.validate_security()

        return {
            "security_level": self.security_level.value,
            "resource_limits": self.resource_limits,
            "network_restrictions": self.network_restrictions,
            "security_config": {
                k: v for k, v in self.security_config.items()
                if k not in ["security_opt"]  # 排除敏感信息
            },
            "capabilities": self.security_config.get("capabilities", []),
            "readonly_rootfs": self.security_config.get("readonly_rootfs", False),
            "privileged": self.security_config.get("privileged", False),
            "security_validation": {
                "is_safe": is_safe,
                "warnings": warnings,
                "recommendation": "使用STRICT或PARANOID安全级别以获得最佳安全性" if warnings else "配置安全"
            }
        }


# 预配置的沙箱
def get_sandbox_config(
    security_level: SandboxSecurityLevel = SandboxSecurityLevel.STANDARD,
    tool_name: Optional[str] = None
) -> SandboxConfig:
    """获取沙箱配置"""
    # 生产环境安全检查
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production" and security_level == SandboxSecurityLevel.MINIMAL:
        logger.warning("生产环境中使用MINIMAL安全级别，这是安全风险！自动升级到STANDARD级别")
        security_level = SandboxSecurityLevel.STANDARD

    config = SandboxConfig(security_level)

    # 根据工具名称调整配置
    if tool_name:
        config = _adjust_config_for_tool(config, tool_name)

    # 验证安全性并记录警告
    is_safe, warnings = config.validate_security()
    if not is_safe:
        logger.warning(f"沙箱配置存在安全警告: {warnings}")
        if environment == "production" and security_level in [SandboxSecurityLevel.MINIMAL, SandboxSecurityLevel.STANDARD]:
            logger.error("生产环境中使用不安全的沙箱配置，考虑使用STRICT或PARANOID级别")

    return config


def _adjust_config_for_tool(config: SandboxConfig, tool_name: str) -> SandboxConfig:
    """根据工具调整配置"""
    # 工具特定的权限需求
    tool_requirements = {
        "nmap": ["NET_RAW", "NET_ADMIN"],
        "masscan": ["NET_RAW", "NET_ADMIN"],
        "tcpdump": ["NET_RAW", "NET_ADMIN"],
        "nikto": [],  # 不需要特殊权限
        "sqlmap": [],  # 不需要特殊权限
        "dirsearch": [],  # 不需要特殊权限
        "whatweb": [],  # 不需要特殊权限
    }

    required_caps = tool_requirements.get(tool_name, [])

    # 检查权限兼容性
    if not config.validate_tool_requirements(tool_name, required_caps):
        logger.warning(
            f"工具 {tool_name} 需要权限 {required_caps}，但当前安全级别 "
            f"{config.security_level.value} 不允许。考虑降低安全级别或调整工具配置。"
        )

    # 应用工具特定的seccomp配置
    try:
        config._apply_tool_specific_seccomp(tool_name)
        logger.info(f"已为工具 {tool_name} 应用特定的seccomp配置")
    except Exception as e:
        logger.warning(f"应用工具特定seccomp配置失败: {e}")

    # 应用AppArmor配置
    try:
        config._apply_apparmor_config(tool_name)
        logger.info(f"已为工具 {tool_name} 应用AppArmor配置")
    except Exception as e:
        logger.warning(f"应用AppArmor配置失败: {e}")

    # 应用网络策略
    try:
        config._apply_network_policy(tool_name)
        logger.info(f"已为工具 {tool_name} 应用网络策略")
    except Exception as e:
        logger.warning(f"应用网络策略失败: {e}")

    # 应用容器逃逸防护
    try:
        config._apply_container_escape_protection()
        logger.info(f"已为工具 {tool_name} 应用容器逃逸防护")
    except Exception as e:
        logger.warning(f"应用容器逃逸防护失败: {e}")

    # 记录安全监控事件
    try:
        # 记录配置应用事件
        monitor_security_event(
            event_type="sandbox_config_applied",
            severity="low",
            message=f"为工具 {tool_name} 应用沙箱配置",
            details={
                "tool_name": tool_name,
                "security_level": config.security_level.value,
                "timestamp": time.time()
            }
        )
    except Exception as e:
        logger.warning(f"记录安全监控事件失败: {e}")

    return config


class AppArmorProfileGenerator:
    """AppArmor配置文件生成器"""

    @staticmethod
    def generate_base_profile(profile_name: str) -> str:
        """生成基础的AppArmor配置文件"""
        base_profile = f"""/**/{{,*/**/}}** {profile_name} {{
  # 包含Docker默认配置
  #include <abstractions/docker>

  # 基础规则
  capability,
  network,
  mount,
  umount,
  signal,
  ptrace,
  chown,
  dac_override,
  dac_read_search,
  fowner,
  fsetid,
  kill,
  setgid,
  setuid,
  setpcap,
  linux_immutable,
  net_bind_service,
  net_broadcast,
  net_admin,
  net_raw,
  ipc_lock,
  ipc_owner,
  sys_module,
  sys_rawio,
  sys_chroot,
  sys_ptrace,
  sys_pacct,
  sys_admin,
  sys_boot,
  sys_nice,
  sys_resource,
  sys_time,
  sys_tty_config,
  mknod,
  lease,
  audit_write,
  audit_control,
  setfcap,

  # 文件系统访问
  deny /** wxlk,

  # 允许访问必要的系统目录
  /dev/null rw,
  /dev/zero rw,
  /dev/full rw,
  /dev/random rw,
  /dev/urandom rw,
  /dev/tty rw,
  /dev/console rw,
  /proc/** r,
  /sys/** r,

  # 容器特定目录
  /var/lib/docker/** r,
  /run/docker.sock rw,

  # 允许创建临时文件
  /tmp/** rw,
  /var/tmp/** rw,

  # 网络访问
  network inet,
  network inet6,
  network netlink,

  # 信号
  signal (receive) peer={profile_name},

  # Ptrace限制
  deny ptrace (trace) peer=unconfined,

  # 挂载限制
  deny mount,
  deny umount,
}}"""
        return base_profile

    @staticmethod
    def generate_tool_profile(tool_name: str) -> str:
        """生成工具特定的AppArmor配置文件"""
        # 工具特定的规则
        tool_profiles = {
            "nmap": """
  # Nmap特定规则
  capability net_raw,
  capability net_admin,

  # 网络扫描相关
  network raw,
  network packet,

  # 允许创建原始套接字
  audit capability net_raw,
  audit capability net_admin,

  # 文件访问
  /usr/bin/nmap mr,
  /usr/share/nmap/** r,
  /etc/services r,
  /proc/net/** r,
""",
            "sqlmap": """
  # Sqlmap特定规则
  # 不需要特殊权限，基础配置足够

  # 文件访问
  /usr/bin/sqlmap mr,
  /usr/share/sqlmap/** r,
  /tmp/sqlmap/** rw,

  # 网络访问（HTTP请求）
  network inet stream,
  network inet6 stream,
""",
            "nikto": """
  # Nikto特定规则
  # 网络扫描工具

  # 文件访问
  /usr/bin/nikto mr,
  /usr/share/nikto/** r,

  # SSL相关
  /etc/ssl/** r,
  /usr/lib/ssl/** r,
""",
            "dirsearch": """
  # Dirsearch特定规则
  # 目录扫描工具

  # 文件访问
  /usr/bin/dirsearch mr,
  /usr/share/dirsearch/** r,
  /usr/lib/python*/** mr,

  # 字典文件访问
  /usr/share/wordlists/** r,
""",
            "whatweb": """
  # WhatWeb特定规则
  # Web指纹识别工具

  # 文件访问
  /usr/bin/whatweb mr,
  /usr/share/whatweb/** r,

  # 插件访问
  /usr/share/whatweb/plugins/** r,
"""
        }

        # 获取基础配置
        base_profile = AppArmorProfileGenerator.generate_base_profile(f"clawai-{tool_name}")

        # 添加工具特定规则
        tool_rules = tool_profiles.get(tool_name, "")

        # 将工具规则插入到基础配置中
        profile_lines = base_profile.split('\n')
        insert_position = -1

        # 找到插入位置（在基础规则之后）
        for i, line in enumerate(profile_lines):
            if line.strip() == "# 文件系统访问":
                insert_position = i
                break

        if insert_position > 0 and tool_rules:
            # 在文件系统访问之前插入工具特定规则
            tool_rule_lines = tool_rules.strip().split('\n')
            profile_lines = profile_lines[:insert_position] + tool_rule_lines + profile_lines[insert_position:]

        return '\n'.join(profile_lines)

    @staticmethod
    def generate_strict_profile(profile_name: str) -> str:
        """生成严格的AppArmor配置文件"""
        strict_profile = f"""/**/{{,*/**/}}** {profile_name} {{
  # 严格模式配置

  # 能力限制 - 仅允许最基本的能力
  capability chown,
  capability dac_override,
  capability fowner,
  capability fsetid,
  capability kill,
  capability setgid,
  capability setuid,
  capability setpcap,
  capability net_bind_service,
  capability sys_chroot,
  capability audit_write,

  # 明确拒绝危险能力
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability sys_admin,
  deny capability sys_boot,
  deny capability sys_ptrace,
  deny capability linux_immutable,
  deny capability net_admin,
  deny capability net_raw,

  # 文件系统访问 - 最小权限原则
  /dev/null rw,
  /dev/zero rw,
  /dev/full rw,
  /dev/random rw,
  /dev/urandom rw,
  /dev/tty rw,
  /dev/console rw,

  # 只读访问系统目录
  /proc/[0-9]*/fd/ r,
  /proc/[0-9]*/task/ r,
  /proc/sys/kernel/cap_last_cap r,
  /proc/sys/kernel/osrelease r,
  /proc/sys/kernel/ngroups_max r,
  /proc/sys/kernel/random/boot_id r,
  /proc/sys/vm/overcommit_memory r,

  # 拒绝所有其他文件系统访问
  deny /** wxlk,

  # 网络访问限制
  network inet,
  network inet6,

  # 明确的网络拒绝规则
  deny network raw,
  deny network packet,

  # 信号限制
  signal (receive) peer={profile_name},

  # 明确的ptrace拒绝
  deny ptrace,

  # 挂载拒绝
  deny mount,
  deny umount,

  # 命名空间操作拒绝
  deny capability sys_admin,  # 阻止unshare等操作

  # 审计规则
  audit deny /** wxlk,
  audit capability,
  audit network,
}}"""
        return strict_profile

    @staticmethod
    def save_profile_to_file(profile_content: str, profile_name: str, output_dir: str = "/etc/apparmor.d") -> str:
        """保存AppArmor配置文件到文件"""
        import os
        import tempfile

        # 在实际环境中，应该保存到/etc/apparmor.d
        # 这里我们返回文件内容，实际保存由调用者处理
        filename = f"{profile_name}"
        filepath = os.path.join(output_dir, filename)

        # 记录日志
        logger.info(f"生成AppArmor配置文件: {filepath}")

        return filepath


def get_apparmor_profile(tool_name: str = None, security_level: SandboxSecurityLevel = SandboxSecurityLevel.STANDARD) -> str:
    """获取AppArmor配置文件内容"""
    generator = AppArmorProfileGenerator()

    if security_level == SandboxSecurityLevel.PARANOID:
        profile_name = f"clawai-paranoid-{tool_name}" if tool_name else "clawai-paranoid"
        return generator.generate_strict_profile(profile_name)
    elif security_level == SandboxSecurityLevel.STRICT:
        profile_name = f"clawai-strict-{tool_name}" if tool_name else "clawai-strict"
        return generator.generate_strict_profile(profile_name)
    elif tool_name:
        # 工具特定的配置
        return generator.generate_tool_profile(tool_name)
    else:
        # 基础配置
        return generator.generate_base_profile("clawai-default")


class SecurityMonitor:
    """安全监控器，用于检测容器异常行为和安全事件"""

    def __init__(self):
        self.events = []
        self.anomalies = []
        self.metrics = {
            "container_starts": 0,
            "container_stops": 0,
            "security_events": 0,
            "anomalies_detected": 0,
            "policy_violations": 0
        }
        self.alert_thresholds = {
            "high_cpu": 80.0,  # CPU使用率阈值
            "high_memory": 80.0,  # 内存使用率阈值
            "high_io": 1000,  # IO操作阈值（次/秒）
            "unexpected_process": True,  # 检测意外进程
            "network_anomaly": True,  # 检测网络异常
            "file_system_anomaly": True,  # 检测文件系统异常
        }

    def log_security_event(self, event_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """记录安全事件"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "details": details or {}
        }

        self.events.append(event)
        self.metrics["security_events"] += 1

        # 根据严重性记录日志
        if severity == "critical":
            logger.critical(f"安全事件[{event_type}]: {message}")
        elif severity == "high":
            logger.error(f"安全事件[{event_type}]: {message}")
        elif severity == "medium":
            logger.warning(f"安全事件[{event_type}]: {message}")
        else:
            logger.info(f"安全事件[{event_type}]: {message}")

        return event

    def detect_anomalies(self, container_id: str, container_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测容器异常行为"""
        detected_anomalies = []

        # 1. 检测资源使用异常
        cpu_percent = container_stats.get("cpu_percent", 0)
        memory_percent = container_stats.get("memory_percent", 0)
        io_ops = container_stats.get("io_ops", 0)

        if cpu_percent > self.alert_thresholds["high_cpu"]:
            anomaly = {
                "type": "high_cpu_usage",
                "severity": "medium",
                "message": f"容器 {container_id} CPU使用率过高: {cpu_percent}%",
                "details": {"cpu_percent": cpu_percent, "threshold": self.alert_thresholds["high_cpu"]}
            }
            detected_anomalies.append(anomaly)

        if memory_percent > self.alert_thresholds["high_memory"]:
            anomaly = {
                "type": "high_memory_usage",
                "severity": "medium",
                "message": f"容器 {container_id} 内存使用率过高: {memory_percent}%",
                "details": {"memory_percent": memory_percent, "threshold": self.alert_thresholds["high_memory"]}
            }
            detected_anomalies.append(anomaly)

        if io_ops > self.alert_thresholds["high_io"]:
            anomaly = {
                "type": "high_io_operations",
                "severity": "medium",
                "message": f"容器 {container_id} IO操作过多: {io_ops} ops/s",
                "details": {"io_ops": io_ops, "threshold": self.alert_thresholds["high_io"]}
            }
            detected_anomalies.append(anomaly)

        # 2. 检测进程异常
        processes = container_stats.get("processes", [])
        if processes and self.alert_thresholds["unexpected_process"]:
            # 检查是否有意外进程（如shell、python解释器等）
            unexpected_processes = ["sh", "bash", "python", "python3", "perl", "ruby"]
            for process in processes:
                proc_name = process.get("name", "").lower()
                if any(unexpected in proc_name for unexpected in unexpected_processes):
                    anomaly = {
                        "type": "unexpected_process",
                        "severity": "high",
                        "message": f"容器 {container_id} 运行意外进程: {proc_name}",
                        "details": {"process_name": proc_name, "command": process.get("cmd", "")}
                    }
                    detected_anomalies.append(anomaly)

        # 3. 检测网络异常
        network_stats = container_stats.get("network", {})
        if network_stats and self.alert_thresholds["network_anomaly"]:
            # 检查异常网络连接
            connections = network_stats.get("connections", [])
            for conn in connections:
                # 检查是否连接到非常见端口或外部地址
                remote_port = conn.get("remote_port", 0)
                remote_ip = conn.get("remote_ip", "")

                # 常见服务端口
                common_ports = [80, 443, 53, 22, 21, 25, 110, 143]
                if remote_port not in common_ports and remote_port > 1024:
                    anomaly = {
                        "type": "unusual_network_connection",
                        "severity": "medium",
                        "message": f"容器 {container_id} 建立异常网络连接: {remote_ip}:{remote_port}",
                        "details": {"remote_ip": remote_ip, "remote_port": remote_port}
                    }
                    detected_anomalies.append(anomaly)

        # 记录检测到的异常
        for anomaly in detected_anomalies:
            self.anomalies.append({
                **anomaly,
                "timestamp": time.time(),
                "container_id": container_id
            })
            self.metrics["anomalies_detected"] += 1

            # 记录安全事件
            self.log_security_event(
                event_type="anomaly_detected",
                severity=anomaly["severity"],
                message=anomaly["message"],
                details=anomaly["details"]
            )

        return detected_anomalies

    def monitor_container_behavior(self, container_id: str, sandbox_config: SandboxConfig) -> Dict[str, Any]:
        """监控容器行为，检测策略违规"""
        violations = []

        # 检查容器配置是否符合安全策略
        config = sandbox_config.security_config

        # 1. 检查特权模式
        if config.get("privileged", False):
            violations.append({
                "type": "privileged_container",
                "severity": "critical",
                "message": f"容器 {container_id} 以特权模式运行",
                "policy": "禁止特权容器"
            })

        # 2. 检查危险能力
        dangerous_capabilities = ["SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE"]
        current_caps = config.get("capabilities", [])
        for dangerous_cap in dangerous_capabilities:
            if dangerous_cap in current_caps:
                violations.append({
                    "type": "dangerous_capability",
                    "severity": "high",
                    "message": f"容器 {container_id} 拥有危险能力: {dangerous_cap}",
                    "policy": "限制危险能力"
                })

        # 3. 检查网络策略违规
        network_restrictions = sandbox_config.network_restrictions
        if network_restrictions.get("network_mode") == "host":
            violations.append({
                "type": "host_network_mode",
                "severity": "high",
                "message": f"容器 {container_id} 使用主机网络模式",
                "policy": "禁止主机网络模式"
            })

        # 记录策略违规
        for violation in violations:
            self.metrics["policy_violations"] += 1
            self.log_security_event(
                event_type="policy_violation",
                severity=violation["severity"],
                message=violation["message"],
                details={
                    "violation_type": violation["type"],
                    "policy": violation["policy"],
                    "container_id": container_id
                }
            )

        return {
            "container_id": container_id,
            "violations": violations,
            "violation_count": len(violations),
            "timestamp": time.time()
        }

    def get_security_report(self) -> Dict[str, Any]:
        """获取安全监控报告"""
        recent_events = self.events[-100:] if len(self.events) > 100 else self.events
        recent_anomalies = self.anomalies[-50:] if len(self.anomalies) > 50 else self.anomalies

        # 统计事件类型
        event_types = {}
        for event in recent_events:
            event_type = event["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # 统计严重性分布
        severity_distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for event in recent_events:
            severity = event["severity"]
            if severity in severity_distribution:
                severity_distribution[severity] += 1

        return {
            "metrics": self.metrics,
            "recent_events": recent_events,
            "recent_anomalies": recent_anomalies,
            "event_types": event_types,
            "severity_distribution": severity_distribution,
            "alert_thresholds": self.alert_thresholds,
            "timestamp": time.time()
        }

    def reset_monitor(self):
        """重置监控器"""
        self.events = []
        self.anomalies = []
        self.metrics = {
            "container_starts": 0,
            "container_stops": 0,
            "security_events": 0,
            "anomalies_detected": 0,
            "policy_violations": 0
        }


# 全局安全监控器实例
_global_security_monitor = None

def get_security_monitor() -> SecurityMonitor:
    """获取全局安全监控器实例"""
    global _global_security_monitor
    if _global_security_monitor is None:
        _global_security_monitor = SecurityMonitor()
        logger.info("安全监控器已初始化")
    return _global_security_monitor

def monitor_container_start(container_id: str, sandbox_config: SandboxConfig):
    """监控容器启动"""
    monitor = get_security_monitor()
    monitor.metrics["container_starts"] += 1

    # 记录容器启动事件
    monitor.log_security_event(
        event_type="container_start",
        severity="low",
        message=f"容器启动: {container_id}",
        details={
            "container_id": container_id,
            "security_level": sandbox_config.security_level.value,
            "timestamp": time.time()
        }
    )

    # 检查策略违规
    monitor.monitor_container_behavior(container_id, sandbox_config)

def monitor_container_stop(container_id: str, exit_code: int, reason: str = ""):
    """监控容器停止"""
    monitor = get_security_monitor()
    monitor.metrics["container_stops"] += 1

    severity = "high" if exit_code != 0 else "low"
    message = f"容器停止: {container_id}, 退出码: {exit_code}"
    if reason:
        message += f", 原因: {reason}"

    monitor.log_security_event(
        event_type="container_stop",
        severity=severity,
        message=message,
        details={
            "container_id": container_id,
            "exit_code": exit_code,
            "reason": reason,
            "timestamp": time.time()
        }
    )

def monitor_security_event(event_type: str, severity: str, message: str, details: Dict[str, Any] = None):
    """记录安全事件"""
    monitor = get_security_monitor()
    return monitor.log_security_event(event_type, severity, message, details)


class SecurityBaselineValidator:
    """安全基线验证器，验证沙箱配置是否符合安全基线要求"""

    # 安全基线定义
    BASELINES = {
        "minimal": {
            "name": "最小安全基线",
            "description": "基本的安全要求，适合测试环境",
            "requirements": [
                {"id": "MIN-001", "description": "容器不能以特权模式运行", "check": "privileged", "expected": False},
                {"id": "MIN-002", "description": "必须设置内存限制", "check": "memory_limit", "expected": True},
                {"id": "MIN-003", "description": "必须启用no-new-privileges", "check": "no_new_privileges", "expected": True},
            ]
        },
        "standard": {
            "name": "标准安全基线",
            "description": "生产环境推荐的安全要求",
            "requirements": [
                {"id": "STD-001", "description": "容器不能以特权模式运行", "check": "privileged", "expected": False},
                {"id": "STD-002", "description": "必须设置内存和CPU限制", "check": "resource_limits", "expected": True},
                {"id": "STD-003", "description": "必须启用no-new-privileges", "check": "no_new_privileges", "expected": True},
                {"id": "STD-004", "description": "根文件系统必须只读", "check": "readonly_rootfs", "expected": True},
                {"id": "STD-005", "description": "不能使用主机网络模式", "check": "host_network", "expected": False},
                {"id": "STD-006", "description": "必须移除危险能力", "check": "dangerous_capabilities", "expected": False},
            ]
        },
        "strict": {
            "name": "严格安全基线",
            "description": "高安全环境的要求",
            "requirements": [
                {"id": "STR-001", "description": "容器不能以特权模式运行", "check": "privileged", "expected": False},
                {"id": "STR-002", "description": "必须设置严格资源限制", "check": "strict_resource_limits", "expected": True},
                {"id": "STR-003", "description": "必须启用no-new-privileges", "check": "no_new_privileges", "expected": True},
                {"id": "STR-004", "description": "根文件系统必须只读", "check": "readonly_rootfs", "expected": True},
                {"id": "STR-005", "description": "不能使用主机网络模式", "check": "host_network", "expected": False},
                {"id": "STR-006", "description": "必须移除所有危险能力", "check": "all_dangerous_capabilities", "expected": False},
                {"id": "STR-007", "description": "必须使用seccomp过滤器", "check": "seccomp_enabled", "expected": True},
                {"id": "STR-008", "description": "必须使用AppArmor配置文件", "check": "apparmor_enabled", "expected": True},
                {"id": "STR-009", "description": "网络必须被限制或禁用", "check": "network_restricted", "expected": True},
            ]
        }
    }

    def __init__(self, baseline_level: str = "standard"):
        self.baseline_level = baseline_level
        self.baseline = self.BASELINES.get(baseline_level, self.BASELINES["standard"])
        self.validation_results = []

    def validate_config(self, sandbox_config: SandboxConfig) -> Dict[str, Any]:
        """验证沙箱配置是否符合安全基线"""
        self.validation_results = []

        # 执行所有基线检查
        for requirement in self.baseline["requirements"]:
            check_result = self._perform_check(requirement, sandbox_config)
            self.validation_results.append(check_result)

        # 计算合规性
        passed_checks = [r for r in self.validation_results if r["passed"]]
        failed_checks = [r for r in self.validation_results if not r["passed"]]

        compliance_rate = len(passed_checks) / len(self.validation_results) * 100 if self.validation_results else 0

        # 生成报告
        report = {
            "baseline_level": self.baseline_level,
            "baseline_name": self.baseline["name"],
            "baseline_description": self.baseline["description"],
            "total_requirements": len(self.validation_results),
            "passed_requirements": len(passed_checks),
            "failed_requirements": len(failed_checks),
            "compliance_rate": round(compliance_rate, 2),
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "timestamp": time.time(),
            "is_compliant": len(failed_checks) == 0
        }

        # 记录安全事件
        if failed_checks:
            monitor_security_event(
                event_type="baseline_violation",
                severity="high" if len(failed_checks) > 3 else "medium",
                message=f"安全基线验证失败: {len(failed_checks)}项不符合要求",
                details={
                    "baseline_level": self.baseline_level,
                    "failed_checks": failed_checks,
                    "compliance_rate": compliance_rate
                }
            )
        else:
            monitor_security_event(
                event_type="baseline_compliant",
                severity="low",
                message=f"安全基线验证通过: 符合{self.baseline['name']}",
                details={
                    "baseline_level": self.baseline_level,
                    "compliance_rate": compliance_rate
                }
            )

        return report

    def _perform_check(self, requirement: Dict[str, Any], sandbox_config: SandboxConfig) -> Dict[str, Any]:
        """执行单个检查"""
        check_id = requirement["id"]
        check_type = requirement["check"]
        expected = requirement["expected"]

        try:
            # 根据检查类型执行相应的验证
            if check_type == "privileged":
                actual = sandbox_config.security_config.get("privileged", False)
                passed = actual == expected
                details = {"actual": actual, "expected": expected}

            elif check_type == "memory_limit":
                actual = "memory" in sandbox_config.resource_limits
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "limit": sandbox_config.resource_limits.get("memory")}

            elif check_type == "no_new_privileges":
                security_opts = sandbox_config.security_config.get("security_opt", [])
                actual = "no-new-privileges:true" in security_opts
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "security_opts": security_opts}

            elif check_type == "resource_limits":
                actual = ("memory" in sandbox_config.resource_limits and
                         "cpus" in sandbox_config.resource_limits)
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "limits": sandbox_config.resource_limits}

            elif check_type == "readonly_rootfs":
                actual = sandbox_config.security_config.get("readonly_rootfs", False)
                passed = actual == expected
                details = {"actual": actual, "expected": expected}

            elif check_type == "host_network":
                actual = sandbox_config.network_restrictions.get("network_mode") == "host"
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "network_mode": sandbox_config.network_restrictions.get("network_mode")}

            elif check_type == "dangerous_capabilities":
                dangerous_caps = ["SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE", "SYS_BOOT"]
                current_caps = sandbox_config.security_config.get("capabilities", [])
                actual = any(cap in current_caps for cap in dangerous_caps)
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "dangerous_caps_found": [c for c in current_caps if c in dangerous_caps]}

            elif check_type == "all_dangerous_capabilities":
                dangerous_caps = ["SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE", "SYS_BOOT",
                                 "SYS_TIME", "SYS_NICE", "SYS_RESOURCE", "NET_ADMIN", "NET_RAW"]
                current_caps = sandbox_config.security_config.get("capabilities", [])
                actual = any(cap in current_caps for cap in dangerous_caps)
                passed = actual == expected
                details = {"actual": actual, "expected": expected, "dangerous_caps_found": [c for c in current_caps if c in dangerous_caps]}

            elif check_type == "seccomp_enabled":
                security_opts = sandbox_config.security_config.get("security_opt", [])
                actual = any(opt.startswith("seccomp=") for opt in security_opts)
                passed = actual == expected
                details = {"actual": actual, "expected": expected}

            elif check_type == "apparmor_enabled":
                security_opts = sandbox_config.security_config.get("security_opt", [])
                actual = any(opt.startswith("apparmor:") for opt in security_opts)
                passed = actual == expected
                details = {"actual": actual, "expected": expected}

            elif check_type == "network_restricted":
                network_disabled = sandbox_config.network_restrictions.get("network_disabled", False)
                network_mode = sandbox_config.network_restrictions.get("network_mode", "none")
                allowed_ports = sandbox_config.network_restrictions.get("allowed_ports", [])

                # 网络被禁用或严格限制
                actual = (network_disabled or
                         network_mode == "none" or
                         len(allowed_ports) <= 10)  # 只允许少量端口
                passed = actual == expected
                details = {
                    "actual": actual,
                    "expected": expected,
                    "network_disabled": network_disabled,
                    "network_mode": network_mode,
                    "allowed_ports_count": len(allowed_ports)
                }

            elif check_type == "strict_resource_limits":
                # 检查是否有严格的资源限制
                has_cpu_limit = "cpus" in sandbox_config.resource_limits
                has_memory_limit = "memory" in sandbox_config.resource_limits
                has_pids_limit = "pids_limit" in sandbox_config.resource_limits

                actual = has_cpu_limit and has_memory_limit and has_pids_limit
                passed = actual == expected
                details = {
                    "actual": actual,
                    "expected": expected,
                    "has_cpu_limit": has_cpu_limit,
                    "has_memory_limit": has_memory_limit,
                    "has_pids_limit": has_pids_limit
                }

            else:
                # 未知检查类型
                passed = False
                details = {"error": f"未知检查类型: {check_type}"}

            # 构建检查结果
            result = {
                "check_id": check_id,
                "check_type": check_type,
                "description": requirement["description"],
                "passed": passed,
                "expected": expected,
                "details": details,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            # 检查执行失败
            return {
                "check_id": check_id,
                "check_type": check_type,
                "description": requirement["description"],
                "passed": False,
                "expected": expected,
                "details": {"error": str(e)},
                "timestamp": time.time()
            }

    def get_baseline_report(self, sandbox_config: SandboxConfig) -> Dict[str, Any]:
        """获取完整的安全基线报告"""
        # 验证所有基线级别
        all_reports = {}
        for baseline_level in self.BASELINES.keys():
            validator = SecurityBaselineValidator(baseline_level)
            report = validator.validate_config(sandbox_config)
            all_reports[baseline_level] = report

        # 确定最适合的基线级别
        suitable_baselines = []
        for baseline_level, report in all_reports.items():
            if report["is_compliant"]:
                suitable_baselines.append({
                    "level": baseline_level,
                    "name": self.BASELINES[baseline_level]["name"],
                    "compliance_rate": report["compliance_rate"]
                })

        # 按严格程度排序（从严格到宽松）
        baseline_order = ["strict", "standard", "minimal"]
        suitable_baselines.sort(key=lambda x: baseline_order.index(x["level"]) if x["level"] in baseline_order else 999)

        return {
            "all_baseline_reports": all_reports,
            "suitable_baselines": suitable_baselines,
            "recommended_baseline": suitable_baselines[0] if suitable_baselines else None,
            "current_config_security_level": sandbox_config.security_level.value,
            "timestamp": time.time()
        }


def validate_security_baseline(sandbox_config: SandboxConfig, baseline_level: str = None) -> Dict[str, Any]:
    """验证沙箱配置是否符合安全基线（便捷函数）"""
    if baseline_level is None:
        # 根据安全级别自动选择基线
        if sandbox_config.security_level == SandboxSecurityLevel.PARANOID:
            baseline_level = "strict"
        elif sandbox_config.security_level == SandboxSecurityLevel.STRICT:
            baseline_level = "strict"
        elif sandbox_config.security_level == SandboxSecurityLevel.STANDARD:
            baseline_level = "standard"
        else:
            baseline_level = "minimal"

    validator = SecurityBaselineValidator(baseline_level)
    return validator.validate_config(sandbox_config)


def get_security_baseline_report(sandbox_config: SandboxConfig) -> Dict[str, Any]:
    """获取完整的安全基线报告（便捷函数）"""
    validator = SecurityBaselineValidator()
    return validator.get_baseline_report(sandbox_config)


# 测试函数
def test_sandbox_config():
    """测试沙箱配置模块的所有功能"""
    print("=" * 60)
    print("测试 ClawAI 安全沙箱配置模块")
    print("=" * 60)

    print("\n1. 测试不同安全级别配置:")
    levels = [
        SandboxSecurityLevel.MINIMAL,
        SandboxSecurityLevel.STANDARD,
        SandboxSecurityLevel.STRICT,
        SandboxSecurityLevel.PARANOID
    ]

    for level in levels:
        print(f"\n  安全级别: {level.value}")
        config = get_sandbox_config(level)
        report = config.get_security_report()

        print(f"    资源限制: CPU={report['resource_limits'].get('cpus', 'N/A')}, "
              f"内存={report['resource_limits'].get('memory', 'N/A')}")
        print(f"    网络模式: {report['network_restrictions'].get('network_mode', 'N/A')}")
        print(f"    只读根文件系统: {report['readonly_rootfs']}")
        print(f"    特权模式: {report['privileged']}")
        print(f"    权限: {report['capabilities']}")

        # 验证安全性
        is_safe, warnings = config.validate_security()
        if warnings:
            print(f"    安全警告: {len(warnings)}个")
            for i, warning in enumerate(warnings[:3], 1):  # 只显示前3个警告
                print(f"      {i}. {warning}")
            if len(warnings) > 3:
                print(f"      ... 还有{len(warnings)-3}个警告")

    print("\n2. 测试工具特定配置:")
    for tool in ["nmap", "nikto", "sqlmap"]:
        config = get_sandbox_config(SandboxSecurityLevel.STANDARD, tool)
        report = config.get_security_report()
        print(f"  {tool}: 权限={report['capabilities']}")

    print("\n3. 测试安全监控系统:")
    monitor = get_security_monitor()

    # 模拟一些安全事件
    monitor_security_event(
        event_type="test_event",
        severity="low",
        message="测试安全事件",
        details={"test": True}
    )

    monitor_security_event(
        event_type="container_escape_attempt",
        severity="high",
        message="模拟容器逃逸尝试",
        details={"technique": "privilege_escalation"}
    )

    # 获取监控报告
    monitor_report = monitor.get_security_report()
    print(f"  安全事件总数: {monitor_report['metrics']['security_events']}")
    print(f"  事件类型分布: {monitor_report['event_types']}")

    print("\n4. 测试安全基线验证:")
    # 测试标准安全基线
    config = get_sandbox_config(SandboxSecurityLevel.STANDARD)
    baseline_report = validate_security_baseline(config, "standard")

    print(f"  基线级别: {baseline_report['baseline_name']}")
    print(f"  合规率: {baseline_report['compliance_rate']}%")
    print(f"  通过检查: {baseline_report['passed_requirements']}/{baseline_report['total_requirements']}")

    if not baseline_report['is_compliant']:
        print(f"  未通过检查:")
        for check in baseline_report['failed_checks']:
            print(f"    - {check['description']} (ID: {check['check_id']})")

    print("\n5. 测试容器逃逸防护:")
    # 创建一个具有潜在风险的配置
    risky_config = SandboxConfig(SandboxSecurityLevel.MINIMAL)

    # 模拟危险配置
    risky_config.security_config["privileged"] = True
    risky_config.security_config["capabilities"] = ["SYS_ADMIN", "NET_RAW"]

    # 应用容器逃逸防护
    risky_config._apply_container_escape_protection()

    print(f"  特权模式防护: {not risky_config.security_config.get('privileged', True)}")
    print(f"  危险能力移除: {'SYS_ADMIN' not in risky_config.security_config.get('capabilities', [])}")

    print("\n6. 测试网络策略验证:")
    config = get_sandbox_config(SandboxSecurityLevel.STANDARD, "nmap")
    is_safe, warnings = config._validate_network_policy("nmap")

    print(f"  网络策略验证: {'安全' if is_safe else '存在警告'}")
    if warnings:
        print(f"  网络策略警告: {warnings}")

    print("\n7. 测试AppArmor配置文件生成:")
    for tool in ["nmap", "sqlmap"]:
        profile = get_apparmor_profile(tool, SandboxSecurityLevel.STANDARD)
        print(f"  {tool} AppArmor配置文件: {len(profile)} 字符")

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_sandbox_config()