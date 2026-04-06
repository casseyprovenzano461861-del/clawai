#!/usr/bin/env python3
"""
测试 SQLMap 对 DVWA 靶场的 SQL 注入检测能力
用于验证 ClawAI 的真实工具执行效果
"""

import os
import sys
import subprocess
import json
import time
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def login_dvwa():
    """登录DVWA靶场并获取session cookie"""
    import requests
    from requests.exceptions import RequestException

    dvwa_url = "http://127.0.0.1/dvwa"
    login_url = f"{dvwa_url}/login.php"

    # DVWA默认凭证
    login_data = {
        'username': 'admin',
        'password': 'password',
        'Login': 'Login'
    }

    try:
        # 创建session
        session = requests.Session()

        # 获取登录页面token
        response = session.get(login_url)

        # 查找token (DVWA使用user_token)
        token_match = re.search(r'name="user_token" value="([^"]+)"', response.text)
        if token_match:
            login_data['user_token'] = token_match.group(1)

        # 提交登录
        response = session.post(login_url, data=login_data)

        if response.status_code == 200 and 'Login failed' not in response.text:
            print("✅ DVWA登录成功")

            # 获取session cookie
            cookies = session.cookies.get_dict()
            # DVWA使用PHPSESSID
            phpsessid = cookies.get('PHPSESSID')

            if phpsessid:
                # 设置安全级别为low（方便测试）
                security_url = f"{dvwa_url}/security.php"
                security_data = {
                    'security': 'low',
                    'seclev_submit': 'Submit'
                }
                # 添加token
                token_match = re.search(r'name="user_token" value="([^"]+)"', response.text)
                if token_match:
                    security_data['user_token'] = token_match.group(1)

                session.post(security_url, data=security_data)
                print("✅ 设置安全级别为low")

            return phpsessid
        else:
            print("❌ DVWA登录失败")
            return None

    except RequestException as e:
        print(f"❌ 连接DVWA失败: {e}")
        return None

def run_sqlmap(target_url, cookie):
    """运行SQLMap检测SQL注入漏洞"""

    # SQLMap路径
    sqlmap_path = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Scripts\sqlmap.exe"

    if not os.path.exists(sqlmap_path):
        print(f"❌ SQLMap未找到: {sqlmap_path}")
        return None

    # 构建命令
    cmd = [
        sqlmap_path,
        "-u", target_url,
        "--cookie", f"PHPSESSID={cookie}; security=low",
        "--batch",  # 非交互模式
        "--level", "3",
        "--risk", "2",
        "--dbs",  # 枚举数据库
        "--flush-session",  # 清除之前的session
        "--output-dir", "reports/sqlmap_output"
    ]

    print(f"🚀 运行SQLMap命令: {' '.join(cmd[:6])}...")

    # 创建输出目录
    os.makedirs("reports/sqlmap_output", exist_ok=True)

    try:
        # 执行命令
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        # 读取输出（可以实时显示，但这里简单等待完成）
        stdout, stderr = process.communicate(timeout=300)  # 5分钟超时

        elapsed_time = time.time() - start_time

        # 检查结果
        if process.returncode == 0:
            print(f"✅ SQLMap执行成功，耗时: {elapsed_time:.1f}秒")

            # 分析输出
            vulnerable = "is vulnerable" in stdout
            db_type = None
            dbs = []

            # 提取数据库类型
            db_match = re.search(r"back-end DBMS: (.+)", stdout)
            if db_match:
                db_type = db_match.group(1)

            # 提取数据库列表
            db_matches = re.findall(r"\[\*\] (.+)", stdout)
            for db in db_matches:
                if "database" in db.lower() and "current" not in db.lower():
                    dbs.append(db.strip())

            result = {
                "vulnerable": vulnerable,
                "db_type": db_type,
                "databases": dbs,
                "raw_output": stdout[:5000],  # 截取部分
                "execution_time": elapsed_time,
                "success": True
            }

            if vulnerable:
                print(f"✅ 发现SQL注入漏洞！数据库类型: {db_type}")
                if dbs:
                    print(f"✅ 可访问的数据库: {', '.join(dbs)}")
            else:
                print("❌ 未发现SQL注入漏洞")

            return result

        else:
            print(f"❌ SQLMap执行失败，返回码: {process.returncode}")
            print(f"错误输出: {stderr[:500]}")
            return {
                "vulnerable": False,
                "error": stderr[:500],
                "success": False
            }

    except subprocess.TimeoutExpired:
        print("❌ SQLMap执行超时（5分钟）")
        return {
            "vulnerable": False,
            "error": "Timeout",
            "success": False
        }
    except Exception as e:
        print(f"❌ 执行SQLMap时出错: {e}")
        return {
            "vulnerable": False,
            "error": str(e),
            "success": False
        }

def main():
    """主函数"""
    print("=" * 60)
    print("SQLMap DVWA SQL注入检测测试")
    print("=" * 60)

    # 1. 登录DVWA
    print("\n1. 登录DVWA靶场...")
    cookie = login_dvwa()

    if not cookie:
        print("❌ 无法继续测试，请确保DVWA靶场运行在 http://127.0.0.1/dvwa")
        return

    # 2. 测试SQL注入页面
    print("\n2. 测试SQL注入页面...")

    # DVWA SQL注入页面 (GET型)
    sqli_url_get = "http://127.0.0.1/dvwa/vulnerabilities/sqli/?id=1"

    # DVWA SQL注入页面 (POST型 - Blind)
    sqli_url_post = "http://127.0.0.1/dvwa/vulnerabilities/sqli_blind/"

    # 测试GET型SQL注入
    print(f"\n🔍 测试GET型SQL注入: {sqli_url_get}")
    result_get = run_sqlmap(sqli_url_get, cookie)

    # 测试POST型SQL注入（如果需要）
    # print(f"\n🔍 测试POST型SQL注入: {sqli_url_post}")
    # result_post = run_sqlmap(sqli_url_post, cookie)

    # 3. 生成报告
    print("\n3. 生成测试报告...")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target": "DVWA SQL Injection",
        "login_success": cookie is not None,
        "tests": {
            "sqli_get": result_get,
            # "sqli_post": result_post
        },
        "summary": {
            "vulnerabilities_found": 0,
            "total_tests": 1,
            "success_rate": 0
        }
    }

    # 计算统计
    if result_get and result_get.get("success"):
        if result_get.get("vulnerable"):
            report["summary"]["vulnerabilities_found"] += 1

    report["summary"]["success_rate"] = (
        report["summary"]["vulnerabilities_found"] / report["summary"]["total_tests"] * 100
    )

    # 保存报告
    report_file = f"reports/sqlmap_dvwa_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("reports", exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ 测试完成！报告已保存至: {report_file}")
    print(f"📊 检测结果: {report['summary']['vulnerabilities_found']}/{report['summary']['total_tests']} 个漏洞")
    print(f"📈 检测率: {report['summary']['success_rate']:.1f}%")

    # 4. 竞赛指标评估
    print("\n4. 竞赛指标评估:")
    print(f"   - 漏洞检测率: {report['summary']['success_rate']:.1f}% {'✅' if report['summary']['success_rate'] >= 90 else '❌'} (要求 ≥90%)")
    print(f"   - 工具执行成功率: {'✅' if result_get and result_get.get('success') else '❌'} (要求 100%)")

    if report['summary']['success_rate'] >= 90:
        print("\n🎉 恭喜！SQL注入检测率满足竞赛要求！")
    else:
        print("\n⚠️  需要进一步优化检测能力")

if __name__ == "__main__":
    main()