#!/usr/bin/env python3
"""
ClawAI CVE Skills 完整回归测试
用法: python tools/regression_test.py [skill_id ...]
不带参数 = 运行全部 14 个
"""
import sys
import os
import time
import subprocess
import threading
import socket
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.shared.backend.skills.cve_exploit_skills import get_cve_exploit_skills
from src.shared.backend.skills.core import SkillExecutor

# ======================================================
# 靶场端口配置 (宿主机侧)
# ======================================================
TARGETS = {
    "cve_s2_045":         {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_s2_057":         {"url": "http://127.0.0.1:8080/struts2-showcase/", "extra": {}},
    "cve_thinkphp_rce":   {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_shiro_550":      {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_fastjson_1224":  {"url": "http://127.0.0.1:8090/",              "extra": {"ldap_server": "127.0.0.1:1389"}},
    "cve_fastjson_1247":  {"url": "http://127.0.0.1:8090/",              "extra": {"ldap_server": "127.0.0.1:1389"}},
    "cve_weblogic_21839": {"url": "127.0.0.1:7001",                      "extra": {"ldap_server": "127.0.0.1:1389"}},
    "cve_tomcat_12615":   {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_php_fpm_11043":  {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_activemq_41678": {"url": "http://127.0.0.1:8161/",              "extra": {}},
    "cve_jboss_7504":     {"url": "http://127.0.0.1:8080/",              "extra": {}},
    "cve_django_34265":   {"url": "http://127.0.0.1:8000/",              "extra": {}},
    "flask_ssti_exploit": {"url": "http://127.0.0.1:8000/",              "extra": {}},
    "cve_geoserver_36401":{"url": "http://127.0.0.1:8080/",              "extra": {}},
}

# 预期成功关键词
SUCCESS_KEYWORDS = {
    "cve_s2_045":         ["RCE_SUCCESS"],
    "cve_s2_057":         ["RCE_SUCCESS"],
    "cve_thinkphp_rce":   ["RCE_SUCCESS"],
    "cve_shiro_550":      ["SHIRO_DETECTED"],
    "cve_fastjson_1224":  ["JNDI_TRIGGERED", "REQUEST_SENT"],
    "cve_fastjson_1247":  ["JNDI_TRIGGERED", "REQUEST_SENT"],
    "cve_weblogic_21839": ["JNDI_TRIGGERED", "WEBLOGIC_DETECTED"],
    "cve_tomcat_12615":   ["RCE_SUCCESS", "WEBSHELL_UPLOADED"],
    "cve_php_fpm_11043":  ["PHP_FPM_DETECTED", "FPM_VULN"],
    "cve_activemq_41678": ["ACTIVEMQ_DETECTED", "JOLOKIA_RESPONSE"],
    "cve_jboss_7504":     ["JBOSS_DETECTED"],
    "cve_django_34265":   ["SQLI_POSSIBLE"],
    "flask_ssti_exploit": ["SSTI_DETECTED", "RCE_SUCCESS"],
    "cve_geoserver_36401":["RCE_SUCCESS", "GEOSERVER_DETECTED"],
}

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def run_skill(skill_id, target_url, extra_params, timeout=30):
    """执行单个 Skill，捕获 stdout，返回 (output, elapsed)"""
    registry = {s.id: s for s in get_cve_exploit_skills()}
    skill = registry.get(skill_id)
    if not skill:
        return f"SKILL_NOT_FOUND: {skill_id}", 0

    # 先用 SkillParameter 默认值填充
    params = {}
    for p in skill.parameters:
        if p.default is not None:
            params[p.name] = p.default
    params["target"] = target_url
    params.update(extra_params)

    # 模板替换（直接执行 code 字符串）
    code = skill.code
    for k, v in params.items():
        code = code.replace("{{" + k + "}}", str(v))

    # 在子进程中执行，捕获输出
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {timeout}s"
    except Exception as e:
        output = f"EXEC_ERROR: {e}"
    elapsed = time.time() - start
    return output.strip(), elapsed


def check_success(skill_id, output):
    keywords = SUCCESS_KEYWORDS.get(skill_id, [])
    return any(kw in output for kw in keywords)


def print_result(skill_id, output, elapsed, passed):
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{status}] {skill_id:35} ({elapsed:.1f}s)")
    # 打印前几行输出
    lines = [l for l in output.split('\n') if l.strip()][:4]
    for l in lines:
        color = GREEN if any(kw in l for kw in SUCCESS_KEYWORDS.get(skill_id, [])) else ""
        print(f"         {color}{l}{RESET}")
    if not passed:
        print(f"         {YELLOW}期望关键词: {SUCCESS_KEYWORDS.get(skill_id)}{RESET}")


def main():
    filter_ids = sys.argv[1:] if len(sys.argv) > 1 else None
    skills = get_cve_exploit_skills()
    skill_ids = [s.id for s in skills]
    if filter_ids:
        skill_ids = [sid for sid in skill_ids if sid in filter_ids]

    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  ClawAI CVE Skills 回归测试  ({len(skill_ids)} Skills)")
    print(f"{'='*60}{RESET}\n")

    results = []
    passed_count = 0

    for skill_id in skill_ids:
        cfg = TARGETS.get(skill_id)
        if not cfg:
            print(f"  {YELLOW}SKIP{RESET}  {skill_id} (无靶场配置)")
            results.append((skill_id, "SKIP", 0, False))
            continue

        print(f"  {CYAN}RUN{RESET}   {skill_id}")
        output, elapsed = run_skill(skill_id, cfg["url"], cfg.get("extra", {}))
        passed = check_success(skill_id, output)
        print_result(skill_id, output, elapsed, passed)
        if passed:
            passed_count += 1
        results.append((skill_id, output, elapsed, passed))
        print()

    # 汇总
    total = len([r for r in results if r[1] != "SKIP"])
    skipped = len([r for r in results if r[1] == "SKIP"])
    print(f"\n{BOLD}{'='*60}")
    print(f"  结果: {GREEN}{passed_count}{RESET}/{total} 通过  ({skipped} 跳过)")
    print(f"{'='*60}{RESET}")

    failed = [r[0] for r in results if r[1] != "SKIP" and not r[3]]
    if failed:
        print(f"\n{RED}失败项:{RESET}")
        for sid in failed:
            print(f"  - {sid}")
    else:
        print(f"\n{GREEN}{BOLD}全部通过！{RESET}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
