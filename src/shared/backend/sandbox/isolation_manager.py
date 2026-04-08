# -*- coding: utf-8 -*-
"""
隔离管理器模块
用于管理沙箱的生命周期和安全隔离
"""

import threading
import time
from typing import Dict, Any, Optional
from .kali_sandbox import KaliSandbox


class IsolationManager:
    """隔离管理器类"""
    
    def __init__(self):
        self.sandboxes = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 3600  # 清理间隔（秒）
        self.max_idle_time = 7200  # 最大空闲时间（秒）
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_idle_sandboxes)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
    
    def create_sandbox(self, name: str = None) -> Optional[str]:
        """创建沙箱"""
        with self.lock:
            if not name:
                name = f"clawai-sandbox-{int(time.time())}"
            
            if name in self.sandboxes:
                print(f"沙箱 {name} 已存在")
                return name
            
            print(f"创建沙箱: {name}")
            sandbox = KaliSandbox(container_name=name)
            if sandbox.start():
                self.sandboxes[name] = {
                    "sandbox": sandbox,
                    "created_at": time.time(),
                    "last_used": time.time(),
                    "status": "running"
                }
                print(f"沙箱 {name} 创建成功")
                return name
            else:
                print(f"沙箱 {name} 创建失败")
                return None
    
    def get_sandbox(self, name: str) -> Optional[KaliSandbox]:
        """获取沙箱"""
        with self.lock:
            sandbox_info = self.sandboxes.get(name)
            if sandbox_info:
                # 更新最后使用时间
                sandbox_info["last_used"] = time.time()
                return sandbox_info["sandbox"]
            return None
    
    def list_sandboxes(self) -> Dict[str, Dict[str, Any]]:
        """列出所有沙箱"""
        with self.lock:
            result = {}
            for name, info in self.sandboxes.items():
                result[name] = {
                    "status": info["status"],
                    "created_at": info["created_at"],
                    "last_used": info["last_used"],
                    "ip": info["sandbox"].get_ip()
                }
            return result
    
    def stop_sandbox(self, name: str) -> bool:
        """停止沙箱"""
        with self.lock:
            sandbox_info = self.sandboxes.get(name)
            if sandbox_info:
                print(f"停止沙箱: {name}")
                if sandbox_info["sandbox"].stop():
                    sandbox_info["status"] = "stopped"
                    print(f"沙箱 {name} 已停止")
                    return True
                else:
                    print(f"沙箱 {name} 停止失败")
                    return False
            else:
                print(f"沙箱 {name} 不存在")
                return False
    
    def start_sandbox(self, name: str) -> bool:
        """启动沙箱"""
        with self.lock:
            sandbox_info = self.sandboxes.get(name)
            if sandbox_info:
                print(f"启动沙箱: {name}")
                if sandbox_info["sandbox"].start():
                    sandbox_info["status"] = "running"
                    sandbox_info["last_used"] = time.time()
                    print(f"沙箱 {name} 已启动")
                    return True
                else:
                    print(f"沙箱 {name} 启动失败")
                    return False
            else:
                print(f"沙箱 {name} 不存在")
                return False
    
    def destroy_sandbox(self, name: str) -> bool:
        """销毁沙箱"""
        with self.lock:
            sandbox_info = self.sandboxes.get(name)
            if sandbox_info:
                print(f"销毁沙箱: {name}")
                if sandbox_info["sandbox"].destroy():
                    del self.sandboxes[name]
                    print(f"沙箱 {name} 已销毁")
                    return True
                else:
                    print(f"沙箱 {name} 销毁失败")
                    return False
            else:
                print(f"沙箱 {name} 不存在")
                return False
    
    def execute_in_sandbox(self, name: str, tool: str, args: str) -> Dict[str, Any]:
        """在沙箱中执行命令"""
        sandbox = self.get_sandbox(name)
        if not sandbox:
            return {"success": False, "output": "沙箱不存在或未启动"}
        
        result = sandbox.execute_tool(tool, args)
        return result
    
    def _cleanup_idle_sandboxes(self):
        """清理空闲沙箱"""
        while True:
            time.sleep(self.cleanup_interval)
            with self.lock:
                current_time = time.time()
                idle_sandboxes = []
                
                for name, info in self.sandboxes.items():
                    idle_time = current_time - info["last_used"]
                    if idle_time > self.max_idle_time:
                        idle_sandboxes.append(name)
                
                for name in idle_sandboxes:
                    print(f"清理空闲沙箱: {name}")
                    self.destroy_sandbox(name)
    
    def set_cleanup_interval(self, interval: int):
        """设置清理间隔"""
        self.cleanup_interval = interval
    
    def set_max_idle_time(self, idle_time: int):
        """设置最大空闲时间"""
        self.max_idle_time = idle_time
