# -*- coding: utf-8 -*-
"""
Kali Linux沙箱模块
用于在隔离环境中执行渗透测试工具
"""

import os
import time
from typing import Dict, Any, Optional
from .docker_manager import DockerManager


class KaliSandbox:
    """Kali Linux沙箱类"""
    
    def __init__(self, container_name: str = "clawai-kali-sandbox"):
        self.container_name = container_name
        self.docker_manager = DockerManager()
        self.container_id = None
    
    def start(self) -> bool:
        """启动沙箱"""
        if not self.docker_manager.is_available():
            print("Docker不可用，无法启动沙箱")
            return False
        
        # 检查容器是否已存在
        containers = self.docker_manager.list_containers(all=True)
        existing_container = None
        for container in containers:
            if container.name == self.container_name:
                existing_container = container
                break
        
        if existing_container:
            if existing_container.status == "running":
                print(f"沙箱容器 {self.container_name} 已经在运行")
                self.container_id = existing_container.id
                return True
            else:
                # 启动现有容器
                print(f"启动现有沙箱容器 {self.container_name}")
                if self.docker_manager.start_container(existing_container.id):
                    self.container_id = existing_container.id
                    return True
                else:
                    return False
        else:
            # 创建新容器
            print(f"创建新的Kali Linux沙箱容器")
            
            # 准备挂载卷
            volumes = {
                os.path.join(os.getcwd(), "tools"): {
                    "bind": "/tools",
                    "mode": "rw"
                },
                os.path.join(os.getcwd(), "results"): {
                    "bind": "/results",
                    "mode": "rw"
                }
            }
            
            # 环境变量
            environment = {
                "DEBIAN_FRONTEND": "noninteractive",
                "LANG": "en_US.UTF-8"
            }
            
            # 创建容器
            self.container_id = self.docker_manager.create_container(
                image_name="kalilinux/kali-rolling",
                container_name=self.container_name,
                volumes=volumes,
                environment=environment,
                network_mode="bridge",
                privileged=False
            )
            
            if self.container_id:
                # 启动容器
                if self.docker_manager.start_container(self.container_id):
                    # 等待容器就绪
                    if self.docker_manager.wait_for_container_ready(self.container_id):
                        # 安装必要的工具
                        self._install_tools()
                        return True
                    else:
                        print("容器启动超时")
                        self.docker_manager.remove_container(self.container_id)
                        self.container_id = None
                        return False
                else:
                    print("启动容器失败")
                    self.docker_manager.remove_container(self.container_id)
                    self.container_id = None
                    return False
            else:
                print("创建容器失败")
                return False
    
    def stop(self) -> bool:
        """停止沙箱"""
        if not self.container_id:
            return False
        
        print(f"停止沙箱容器 {self.container_name}")
        result = self.docker_manager.stop_container(self.container_id)
        if result:
            print(f"沙箱容器 {self.container_name} 已停止")
        return result
    
    def destroy(self) -> bool:
        """销毁沙箱"""
        if not self.container_id:
            return False
        
        print(f"销毁沙箱容器 {self.container_name}")
        result = self.docker_manager.remove_container(self.container_id)
        if result:
            print(f"沙箱容器 {self.container_name} 已销毁")
            self.container_id = None
        return result
    
    def execute_tool(self, tool_name: str, args: str) -> Dict[str, Any]:
        """在沙箱中执行工具"""
        if not self.container_id:
            return {"success": False, "output": "沙箱未启动"}
        
        # 构建命令
        command = f"{tool_name} {args}"
        print(f"在沙箱中执行: {command}")
        
        # 执行命令
        result = self.docker_manager.execute_command(self.container_id, command)
        return result
    
    def _install_tools(self):
        """安装必要的工具"""
        if not self.container_id:
            return
        
        print("在沙箱中安装必要的工具...")
        
        # 更新包管理器
        self.docker_manager.execute_command(self.container_id, "apt-get update -y")
        
        # 安装常用工具
        tools = [
            "nmap",
            "sqlmap",
            "nikto",
            "gobuster",
            "dirsearch",
            "subfinder",
            "amass",
            "hashcat",
            "john",
            "hydra",
            "metasploit-framework",
            "nuclei",
            "httpx",
            "wfuzz",
            "testssl.sh",
            "wafw00f",
            "arachni",
            "w3af"
        ]
        
        for tool in tools:
            print(f"安装工具: {tool}")
            self.docker_manager.execute_command(
                self.container_id, 
                f"apt-get install -y {tool}"
            )
        
        print("工具安装完成")
    
    def get_status(self) -> Optional[str]:
        """获取沙箱状态"""
        if not self.container_id:
            return "stopped"
        return self.docker_manager.get_container_status(self.container_id)
    
    def get_ip(self) -> Optional[str]:
        """获取沙箱IP地址"""
        if not self.container_id:
            return None
        return self.docker_manager.get_container_ip(self.container_id)
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到沙箱"""
        if not self.container_id:
            return False
        
        try:
            # 构建上传命令
            command = f"mkdir -p $(dirname {remote_path}) && cat > {remote_path} << 'EOF'\n$(cat {local_path})\nEOF"
            result = self.docker_manager.execute_command(self.container_id, command)
            return result.get("success", False)
        except Exception as e:
            print(f"上传文件失败: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从沙箱下载文件"""
        if not self.container_id:
            return False
        
        try:
            # 构建下载命令
            result = self.docker_manager.execute_command(self.container_id, f"cat {remote_path}")
            if result.get("success", False):
                # 确保本地目录存在
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                # 写入文件
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(result.get("output", ""))
                return True
            return False
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
