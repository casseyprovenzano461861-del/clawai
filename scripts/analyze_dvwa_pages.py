#!/usr/bin/env python3
"""
分析DVWA页面结构，为优化漏洞检测提供数据
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def login_dvwa():
    """登录DVWA靶场"""
    dvwa_url = "http://127.0.0.1/dvwa"
    login_url = f"{dvwa_url}/login.php"

    session = requests.Session()

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

        return session
    else:
        print("❌ DVWA登录失败")
        return None

def analyze_sqli_page(session):
    """分析SQL注入页面"""
    dvwa_url = "http://127.0.0.1/dvwa"
    sqli_url = f"{dvwa_url}/vulnerabilities/sqli/"

    print(f"\n🔍 分析SQL注入页面: {sqli_url}")

    response = session.get(sqli_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找表单
        forms = soup.find_all('form')
        print(f"   找到 {len(forms)} 个表单")

        for i, form in enumerate(forms):
            print(f"\n   表单 #{i+1}:")
            print(f"      Action: {form.get('action', 'N/A')}")
            print(f"      Method: {form.get('method', 'GET').upper()}")

            # 查找输入字段
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name', '')
                type_ = inp.get('type', 'text')
                value = inp.get('value', '')
                print(f"      输入: name='{name}', type='{type_}', value='{value}'")

            # 查找按钮
            buttons = form.find_all('button')
            for btn in buttons:
                print(f"      按钮: {btn.text.strip()}")

        # 检查页面内容中的线索
        page_text = response.text.lower()

        vulnerabilities = []

        if 'sql' in page_text and 'injection' in page_text:
            vulnerabilities.append('SQL Injection')
            print("   页面包含SQL注入相关文本")

        if 'user id' in page_text:
            print("   页面包含'User ID'字段")

        if 'submit' in page_text:
            print("   页面包含'Submit'按钮")

        # 测试GET请求
        test_url = f"{sqli_url}?id=1&Submit=Submit"
        test_response = session.get(test_url)

        if test_response.status_code == 200:
            print("   GET请求测试成功")

            # 检查响应中是否包含数据库信息
            if 'first name' in test_response.text.lower() or 'surname' in test_response.text.lower():
                print("   ✅ 页面返回用户数据（可能存在SQL注入）")
                return {
                    'url': sqli_url,
                    'method': 'GET',
                    'parameters': ['id', 'Submit'],
                    'vulnerable_indicator': True,
                    'test_url': test_url
                }
            else:
                print("   ⚠️  页面未返回明显用户数据")
        else:
            print(f"   ❌ GET请求失败: {test_response.status_code}")

    return {
        'url': sqli_url,
        'method': 'GET',
        'parameters': ['id'],
        'vulnerable_indicator': False
    }

def analyze_xss_page(session):
    """分析XSS页面"""
    dvwa_url = "http://127.0.0.1/dvwa"

    # 反射型XSS
    xss_r_url = f"{dvwa_url}/vulnerabilities/xss_r/"
    # 存储型XSS
    xss_s_url = f"{dvwa_url}/vulnerabilities/xss_s/"

    print(f"\n🔍 分析XSS页面:")
    print(f"   反射型XSS: {xss_r_url}")
    print(f"   存储型XSS: {xss_s_url}")

    results = {}

    # 分析反射型XSS
    response = session.get(xss_r_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')

        print(f"   反射型XSS页面找到 {len(forms)} 个表单")

        for form in forms:
            inputs = form.find_all('input')
            for inp in inputs:
                if inp.get('name') == 'name':
                    results['xss_reflected'] = {
                        'url': xss_r_url,
                        'method': form.get('method', 'GET').upper(),
                        'parameter': 'name',
                        'test_value': '<script>alert(1)</script>'
                    }
                    print(f"   找到反射型XSS参数: name")

    # 分析存储型XSS
    response = session.get(xss_s_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')

        print(f"   存储型XSS页面找到 {len(forms)} 个表单")

        for form in forms:
            # 查找name和message字段
            inputs = form.find_all('input')
            textareas = form.find_all('textarea')

            params = []
            for inp in inputs:
                if inp.get('name') and inp.get('type') in ['text', 'textarea']:
                    params.append(inp.get('name'))

            for ta in textareas:
                if ta.get('name'):
                    params.append(ta.get('name'))

            if params:
                results['xss_stored'] = {
                    'url': xss_s_url,
                    'method': form.get('method', 'POST').upper(),
                    'parameters': params,
                    'test_value': '<script>alert("XSS")</script>'
                }
                print(f"   找到存储型XSS参数: {params}")

    return results

def analyze_command_injection_page(session):
    """分析命令注入页面"""
    dvwa_url = "http://127.0.0.1/dvwa"
    exec_url = f"{dvwa_url}/vulnerabilities/exec/"

    print(f"\n🔍 分析命令注入页面: {exec_url}")

    response = session.get(exec_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')

        print(f"   找到 {len(forms)} 个表单")

        for form in forms:
            inputs = form.find_all('input')

            for inp in inputs:
                if inp.get('name') == 'ip':
                    return {
                        'url': exec_url,
                        'method': form.get('method', 'POST').upper(),
                        'parameter': 'ip',
                        'test_values': [
                            '127.0.0.1 && ls',
                            '127.0.0.1 | dir',
                            '127.0.0.1; whoami'
                        ]
                    }

    return None

def analyze_csrf_page(session):
    """分析CSRF页面"""
    dvwa_url = "http://127.0.0.1/dvwa"
    csrf_url = f"{dvwa_url}/vulnerabilities/csrf/"

    print(f"\n🔍 分析CSRF页面: {csrf_url}")

    response = session.get(csrf_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找密码修改表单
        forms = soup.find_all('form')

        for form in forms:
            inputs = form.find_all('input')

            password_fields = []
            for inp in inputs:
                if 'password' in inp.get('name', '').lower():
                    password_fields.append(inp.get('name'))

            if password_fields:
                return {
                    'url': csrf_url,
                    'method': form.get('method', 'GET').upper(),
                    'parameters': password_fields,
                    'csrf_test': '需要验证token机制'
                }

    return None

def main():
    """主函数"""
    print("=" * 60)
    print("DVWA页面结构分析")
    print("=" * 60)

    # 登录DVWA
    session = login_dvwa()

    if not session:
        print("❌ 无法继续分析，请确保DVWA靶场运行")
        return

    analysis_results = {}

    # 分析各漏洞页面
    print("\n" + "="*60)
    print("开始分析漏洞页面")
    print("="*60)

    # 1. SQL注入
    analysis_results['sqli'] = analyze_sqli_page(session)

    # 2. XSS
    xss_results = analyze_xss_page(session)
    analysis_results.update(xss_results)

    # 3. 命令注入
    analysis_results['command_injection'] = analyze_command_injection_page(session)

    # 4. CSRF
    analysis_results['csrf'] = analyze_csrf_page(session)

    # 生成分析报告
    print("\n" + "="*60)
    print("分析报告")
    print("="*60)

    # 统计
    total_pages = len(analysis_results)
    pages_with_forms = sum(1 for page in analysis_results.values() if page)

    print(f"📊 分析统计:")
    print(f"   总页面数: {total_pages}")
    print(f"   包含表单页面: {pages_with_forms}")

    # 详细结果
    print(f"\n📋 详细分析结果:")

    for page_name, page_data in analysis_results.items():
        if page_data:
            print(f"\n   {page_name.upper()}:")
            print(f"     URL: {page_data.get('url', 'N/A')}")
            print(f"     方法: {page_data.get('method', 'N/A')}")

            params = page_data.get('parameters', [])
            if isinstance(params, list):
                print(f"     参数: {', '.join(params)}")
            elif params:
                print(f"     参数: {params}")

            if 'test_value' in page_data:
                print(f"     测试值: {page_data['test_value'][:50]}...")
            elif 'test_values' in page_data:
                print(f"     测试值示例: {page_data['test_values'][0]}")

    # 保存分析结果
    report_file = f"reports/dvwa_page_analysis_{time.strftime('%Y%m%d_%H%M%S')}.json"

    import os
    os.makedirs("reports", exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 分析完成！报告已保存至: {report_file}")

    # 生成优化建议
    print("\n" + "="*60)
    print("优化建议")
    print("="*60)

    suggestions = []

    if analysis_results.get('sqli'):
        suggestions.append("✅ SQL注入: 使用SQLMap测试GET参数'id'，技术包括UNION、Boolean-based blind")

    if analysis_results.get('xss_reflected'):
        suggestions.append("✅ 反射型XSS: 使用XSStrike测试参数'name'，payload: <script>alert(1)</script>")

    if analysis_results.get('command_injection'):
        suggestions.append("✅ 命令注入: 使用Commix测试参数'ip'，payload: 127.0.0.1 && ls")

    if suggestions:
        print("基于分析结果，建议进行以下测试:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("⚠️  未找到明确的漏洞测试目标，请检查DVWA配置")

    print("\n🎯 下一步:")
    print("  1. 基于分析结果创建针对性测试脚本")
    print("  2. 调整工具参数以提高检测率")
    print("  3. 运行全面测试收集量化数据")

if __name__ == "__main__":
    import time
    main()