# -*- coding: utf-8 -*-
"""
Docker管理器模块
用于管理Docker容器的创建、运行和管理
"""

import docker
import time
import os
from typing import Dict, Any, Optional


class DockerManager:
    """Docker管理器类"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"无法连接到Docker: {e}")
            self.client = None
    
    def is_available(self):
        """检查Docker是否可用"""
        return self.client is not None
    
    def create_container(self, image_name: str, container_name: str, 
                        ports: Dict[str, int] = None, 
                        volumes: Dict[str, Dict[str, str]] = None, 
                        environment: Dict[str, str] = None, 
                        network_mode: str = "bridge",
                        privileged: bool = False) -> Optional[str]:
        """创建容器"""
        if not self.is_available():
            return None
        
        try:
            # 检查镜像是否存在
            try:
                self.client.images.get(image_name)
            except docker.errors.ImageNotFound:
                print(f"拉取镜像: {image_name}")
                self.client.images.pull(image_name)
            
            # 创建容器
            container = self.client.containers.create(
                image=image_name,
                name=container_name,
                ports=ports,
                volumes=volumes,
                environment=environment,
                network_mode=network_mode,
                privileged=privileged,
                tty=True,
                stdin_open=True
            )
            
            return container.id
            
        except Exception as e:
            print(f"创建容器失败: {e}")
            return None
    
    def start_container(self, container_id: str) -> bool:
        """启动容器"""
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return True
        except Exception as e:
            print(f"启动容器失败: {e}")
            return False
    
    def stop_container(self, container_id: str) -> bool:
        """停止容器"""
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            return True
        except Exception as e:
            print(f"停止容器失败: {e}")
            return False
    
    def remove_container(self, container_id: str, force: bool = True) -> bool:
        """移除容器"""
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            return True
        except Exception as e:
            print(f"移除容器失败: {e}")
            return False
    
    def execute_command(self, container_id: str, command: str) -> Dict[str, Any]:
        """在容器中执行命令"""
        if not self.is_available():
            return {"success": False, "output": "Docker不可用"}
        
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                stdin=False
            )
            
            return {
                "success": exec_result.exit_code == 0,
                "output": exec_result.output.decode('utf-8'),
                "exit_code": exec_result.exit_code
            }
            
        except Exception as e:
            print(f"执行命令失败: {e}")
            return {"success": False, "output": str(e)}
    
    def get_container_status(self, container_id: str) -> Optional[str]:
        """获取容器状态"""
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except Exception as e:
            print(f"获取容器状态失败: {e}")
            return None
    
    def list_containers(self, all: bool = False) -> list:
        """列出容器"""
        if not self.is_available():
            return []
        
        try:
            return self.client.containers.list(all=all)
        except Exception as e:
            print(f"列出容器失败: {e}")
            return []
    
    def get_container_ip(self, container_id: str) -> Optional[str]:
        """获取容器IP地址"""
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
            for network_name, network_info in networks.items():
                return network_info.get("IPAddress")
            return None
        except Exception as e:
            print(f"获取容器IP失败: {e}")
            return None
    
    def wait_for_container_ready(self, container_id: str, timeout: int = 60) -> bool:
        """等待容器就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_container_status(container_id)
            if status == "running":
                return True
            time.sleep(1)
        return False
