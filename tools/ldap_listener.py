#!/usr/bin/env python3
"""
最简 LDAP 监听器 - 用于验证 FastJSON JNDI 回调
当 FastJSON 漏洞触发时，目标服务器会发起 LDAP 连接到此服务器
我们只需确认连接到达，即可验证漏洞存在

使用: python ldap_listener.py [port=1389] [timeout=15]
"""
import socket
import sys
import time
import threading

port = int(sys.argv[1]) if len(sys.argv) > 1 else 1389
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 15

received = []

def handle_client(conn, addr):
    """处理 LDAP 连接，返回最简错误响应让服务器知道我们在这里"""
    received.append(addr)
    try:
        data = conn.recv(1024)
        print(f"[LDAP_CALLBACK] 收到连接来自 {addr[0]}:{addr[1]}", flush=True)
        print(f"[LDAP_CALLBACK] 数据(hex): {data[:64].hex()}", flush=True)
        # 发送 LDAP BindResponse (成功) 最简响应
        # 0x30=SEQUENCE, len, messageID=1, BindResponse=0x61, resultCode=0(success)
        bind_resp = bytes([0x30, 0x0c, 0x02, 0x01, 0x01, 0x61, 0x07,
                           0x0a, 0x01, 0x00, 0x04, 0x00, 0x04, 0x00])
        conn.send(bind_resp)
    except Exception as e:
        print(f"[LDAP_CALLBACK] 处理错误: {e}", flush=True)
    finally:
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', port))
server.listen(5)
server.settimeout(timeout)

print(f"[LDAP_LISTENER] 监听端口 {port}，等待 {timeout} 秒...", flush=True)

deadline = time.time() + timeout
while time.time() < deadline:
    try:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
        t.join(3)
    except socket.timeout:
        break
    except Exception as e:
        print(f"[LDAP_LISTENER] 接受连接错误: {e}", flush=True)
        break

server.close()

if received:
    print(f"[LDAP_RESULT] JNDI_CALLBACK_RECEIVED from {[f'{a[0]}:{a[1]}' for a in received]}", flush=True)
    sys.exit(0)
else:
    print("[LDAP_RESULT] NO_CALLBACK_RECEIVED", flush=True)
    sys.exit(1)
