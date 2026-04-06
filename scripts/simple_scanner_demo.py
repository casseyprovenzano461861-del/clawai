#!/usr/bin/env python3
"""
简单扫描器演示
展示ClawAI的实际扫描能力
"""

import socket
import requests
import time

class SimpleScanner:
    def __init__(self, target):
        self.target = target
    
    def port_scan(self, ports=[80, 443, 22, 21]):
        """简单的端口扫描"""
        print(f"扫描 {self.target} 的端口...")
        results = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target, port))
                
                if result == 0:
                    print(f"  [开放] 端口 {port}")
                    results.append(port)
                sock.close()
                
            except Exception as e:
                print(f"  端口 {port} 扫描错误: {e}")
        
        return results
    
    def web_scan(self):
        """简单的Web扫描"""
        print(f"扫描 {self.target} 的Web服务...")
        
        urls = [
            f"http://{self.target}/",
            f"https://{self.target}/",
            f"http://{self.target}/robots.txt",
            f"http://{self.target}/admin/"
        ]
        
        results = []
        for url in urls:
            try:
                response = requests.get(url, timeout=5, allow_redirects=True)
                print(f"  {url}: 状态码 {response.status_code}")
                results.append({
                    'url': url,
                    'status': response.status_code,
                    'length': len(response.text)
                })
            except Exception as e:
                print(f"  {url}: 错误 - {e}")
        
        return results

if __name__ == "__main__":
    print("ClawAI 简单扫描器演示")
    print("=" * 50)
    
    # 使用本地回环地址测试
    scanner = SimpleScanner("127.0.0.1")
    
    # 端口扫描
    open_ports = scanner.port_scan()
    print(f"\n发现 {len(open_ports)} 个开放端口: {open_ports}")
    
    # Web扫描
    web_results = scanner.web_scan()
    print(f"\n完成 {len(web_results)} 个Web扫描")
    
    print("\n扫描完成!")
