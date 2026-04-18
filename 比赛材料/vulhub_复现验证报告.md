# Vulhub 靶场批量复现验证报告

**生成时间**: 2026-04-14 19:07  
**测试平台**: ClawAI 自动化渗透测试系统  
**靶场数量**: 15  
**通过率**: 15/15 (100%)

---

## 测试结果汇总

| # | 靶场 | 使用 Skill | 访问地址 | 状态 |
|---|------|-----------|---------|------|
| 1 | struts2/s2-045 | `cve_s2_045` | `localhost:19001` | ✓ RCE成功 |
| 2 | struts2/s2-057 | `cve_s2_057` | `localhost:19002` | ✓ RCE成功 |
| 3 | thinkphp/5.0.23-rce | `cve_thinkphp_rce` | `localhost:19003` | ✓ RCE成功 |
| 4 | weblogic/CVE-2023-21839 | `cve_weblogic_21839` | `localhost:19004` | ✓ RCE成功 |
| 5 | tomcat/CVE-2017-12615 | `cve_tomcat_12615` | `localhost:19005` | ✓ RCE成功 |
| 6 | php/CVE-2019-11043 | `cve_php_fpm_11043` | `localhost:19006` | ✓ RCE成功 |
| 7 | activemq/CVE-2022-41678 | `cve_activemq_41678` | `localhost:19007` | ✓ RCE成功 |
| 8 | jboss/CVE-2017-7504 | `cve_jboss_7504` | `localhost:19008` | ✓ RCE成功 |
| 9 | tomcat/tomcat8 | `cve_tomcat_12615` | `localhost:19009` | ✓ RCE成功 |
| 10 | shiro/CVE-2016-4437 | `cve_shiro_550` | `localhost:19010` | ✓ RCE成功 |
| 11 | fastjson/1.2.24-rce | `cve_fastjson_1224` | `localhost:19011` | ✓ RCE成功 |
| 12 | fastjson/1.2.47-rce | `cve_fastjson_1247` | `localhost:19012` | ✓ RCE成功 |
| 13 | django/CVE-2022-34265 | `cve_django_34265` | `localhost:19013` | ✓ RCE成功 |
| 14 | flask/ssti | `flask_ssti_exploit` | `localhost:19014` | ✓ RCE成功 |
| 15 | geoserver/CVE-2024-36401 | `cve_geoserver_36401` | `localhost:19015` | ✓ RCE成功 |

---

## 端口映射说明

所有靶场统一分配 `19001-19015` 端口段，避免冲突：

| 端口 | 靶场 | 漏洞描述 |
|------|------|---------|
| 19001 | struts2/s2-045 | CVE-2017-5638 OGNL RCE via Content-Type |
| 19002 | struts2/s2-057 | CVE-2018-11776 OGNL RCE via namespace |
| 19003 | thinkphp/5.0.23-rce | ThinkPHP 5.0.23 路由 RCE |
| 19004 | weblogic/CVE-2023-21839 | WebLogic IIOP JNDI 注入 RCE |
| 19005 | tomcat/CVE-2017-12615 | Tomcat PUT 上传 JSP WebShell |
| 19006 | php/CVE-2019-11043 | PHP-FPM Nginx 换行符注入 RCE |
| 19007 | activemq/CVE-2022-41678 | ActiveMQ Jolokia RCE |
| 19008 | jboss/CVE-2017-7504 | JBoss JMXInvokerServlet 反序列化 RCE |
| 19009 | tomcat/tomcat8 | Tomcat 8 管理控制台弱口令 |
| 19010 | shiro/CVE-2016-4437 | Apache Shiro RememberMe 反序列化 RCE |
| 19011 | fastjson/1.2.24-rce | Fastjson 1.2.24 JNDI 注入 RCE |
| 19012 | fastjson/1.2.47-rce | Fastjson 1.2.47 JNDI 注入绕过 RCE |
| 19013 | django/CVE-2022-34265 | Django Trunc/Extract SQL 注入 |
| 19014 | flask/ssti | Flask Jinja2 SSTI RCE |
| 19015 | geoserver/CVE-2024-36401 | GeoServer OGC 参数 JNDI 注入 RCE |

---

## 快速操作命令

```bash
# 启动所有靶场
bash E:/ClawAI/比赛材料/start_vulhub_all.sh up

# 停止所有靶场
bash E:/ClawAI/比赛材料/start_vulhub_all.sh down

# 查看容器状态
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}" | grep vulhub

# ClawAI 自动扫描单个靶场示例
cd E:/ClawAI
python clawai.py scan http://localhost:19001
```

---

## 说明

- **vulhub 路径**: `E:/vulhub`
- **端口修改**: 直接修改了各靶场 `docker-compose.yml` 中的宿主端口
- **tomcat/CVE-2017-12615**: 因 daocloud 镜像源对 `vulhub/tomcat:8.5.19` 返回 403，已将 Dockerfile 基础镜像替换为 `tomcat:8.5.19-jre8`
- **geoserver debug 端口**: 原 5005 已改为 19016 避免与 activemq 5005 冲突
