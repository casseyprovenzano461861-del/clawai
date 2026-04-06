#!/usr/bin/env python3
"""
精确DVWA SQL注入测试
模拟真实用户交互，优化检测参数
"""

import os
import sys
import subprocess
import json
import time
import re
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_dvwa_session():
    """获取DVWA登录后的session"""
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

            return session
        else:
            print("❌ DVWA登录失败")
            return None

    except Exception as e:
        print(f"❌ 连接DVWA失败: {e}")
        return None

def analyze_sqli_page_interaction(session):
    """分析SQL注入页面的实际交互"""
    dvwa_url = "http://127.0.0.1/dvwa"
    sqli_url = f"{dvwa_url}/vulnerabilities/sqli/"

    print(f"\n🔍 分析SQL注入页面交互: {sqli_url}")

    # 访问SQL注入页面
    response = session.get(sqli_url)

    if response.status_code != 200:
        print(f"❌ 访问SQL注入页面失败: {response.status_code}")
        return None

    # 检查页面内容
    page_content = response.text

    # 查找表单和参数
    import re

    # 查找可能的用户选择表单
    select_pattern = r'<select[^>]*name="([^"]+)"[^>]*>'
    select_match = re.search(select_pattern, page_content, re.IGNORECASE)

    # 查找提交按钮
    submit_pattern = r'<input[^>]*type="submit"[^>]*name="([^"]+)"[^>]*>'
    submit_match = re.search(submit_pattern, page_content, re.IGNORECASE)

    # 查找所有输入字段
    input_pattern = r'<input[^>]*name="([^"]+)"[^>]*>'
    input_matches = re.findall(input_pattern, page_content, re.IGNORECASE)

    print(f"   页面分析结果:")
    if select_match:
        print(f"     选择框参数: {select_match.group(1)}")
    if submit_match:
        print(f"     提交按钮: {submit_match.group(1)}")
    if input_matches:
        print(f"     输入字段: {', '.join(input_matches)}")

    # 测试不同参数组合
    test_cases = []

    # 测试1: 使用id参数（标准GET）
    test_url1 = f"{sqli_url}?id=1&Submit=Submit"
    test_cases.append({
        'url': test_url1,
        'method': 'GET',
        'params': {'id': '1', 'Submit': 'Submit'},
        'description': '标准GET请求，id=1'
    })

    # 测试2: 使用User ID参数（如果有）
    if select_match:
        param_name = select_match.group(1)
        test_url2 = f"{sqli_url}?{param_name}=1&Submit=Submit"
        test_cases.append({
            'url': test_url2,
            'method': 'GET',
            'params': {param_name: '1', 'Submit': 'Submit'},
            'description': f'使用选择框参数: {param_name}=1'
        })

    # 测试3: 尝试POST请求（如果有表单）
    if 'form' in page_content.lower():
        # 查找表单action
        form_action_pattern = r'<form[^>]*action="([^"]*)"[^>]*>'
        form_action_match = re.search(form_action_pattern, page_content, re.IGNORECASE)

        action = form_action_match.group(1) if form_action_match else sqli_url
        if not action.startswith('http'):
            action = f"{dvwa_url}/{action.lstrip('/')}"

        test_cases.append({
            'url': action,
            'method': 'POST',
            'params': {'id': '1', 'Submit': 'Submit'},
            'description': 'POST请求，id=1'
        })

    return test_cases

def test_sqlmap_with_case(test_case, cookie):
    """使用特定测试用例运行SQLMap"""
    sqlmap_path = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Scripts\sqlmap.exe"

    if not os.path.exists(sqlmap_path):
        print(f"❌ SQLMap未找到: {sqlmap_path}")
        return None

    print(f"\n🧪 测试用例: {test_case['description']}")
    print(f"   URL: {test_case['url']}")
    print(f"   方法: {test_case['method']}")

    # 构建SQLMap命令
    cmd = [
        sqlmap_path,
        "-u", test_case['url'],
        "--cookie", f"PHPSESSID={cookie}; security=low",
        "--batch",
        "--level", "5",
        "--risk", "3",
        "--technique", "BEUSTQ",  # 所有技术
        "--dbms", "mysql",  # DVWA使用MySQL
        "--dbs",  # 枚举数据库
        "--flush-session",
        "--output-dir", f"reports/sqlmap_case_{int(time.time())}",
        "--threads", "3"
    ]

    # 如果是POST请求，添加数据
    if test_case['method'] == 'POST' and test_case.get('params'):
        # 将参数字典转换为字符串
        data_str = '&'.join([f"{k}={v}" for k, v in test_case['params'].items()])
        cmd.extend(["--data", data_str])

    # 限制输出，只显示关键信息
    cmd.extend(["--answers", "follow=Y"])

    try:
        # 创建输出目录
        os.makedirs("reports", exist_ok=True)

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

        # 设置超时（3分钟）
        stdout, stderr = process.communicate(timeout=180)
        elapsed_time = time.time() - start_time

        # 分析结果
        result = {
            'test_case': test_case['description'],
            'url': test_case['url'],
            'method': test_case['method'],
            'execution_time': elapsed_time,
            'success': process.returncode == 0,
            'vulnerable': False,
            'details': {}
        }

        # 检查是否发现漏洞
        if 'is vulnerable' in stdout:
            result['vulnerable'] = True
            result['details']['vulnerability'] = 'SQL Injection found'

            # 提取数据库信息
            db_match = re.search(r"back-end DBMS: (.+)", stdout)
            if db_match:
                result['details']['dbms'] = db_match.group(1)

            # 提取数据库列表
            db_matches = re.findall(r"\[\*\] (.+)", stdout)
            databases = []
            for db in db_matches:
                if db and 'available databases' not in db and len(db) > 2:
                    databases.append(db.strip())

            if databases:
                result['details']['databases'] = databases

        elif 'heuristic test' in stdout:
            result['details']['note'] = 'Heuristic test performed, manual confirmation needed'
        elif 'all tested parameters appear to be not injectable' in stdout:
            result['details']['note'] = 'No injection points found'

        # 记录关键输出片段
        output_lines = stdout.split('\n')
        key_lines = []
        for line in output_lines:
            if any(keyword in line.lower() for keyword in ['vulnerable', 'injection', 'database', 'error', 'warning']):
                key_lines.append(line.strip())

        result['details']['key_output'] = key_lines[:10]  # 前10个关键行

        # 打印结果摘要
        if result['vulnerable']:
            print(f"   ✅ 发现SQL注入漏洞！耗时: {elapsed_time:.1f}秒")
            if 'dbms' in result['details']:
                print(f"   📊 数据库类型: {result['details']['dbms']}")
        else:
            print(f"   ❌ 未发现漏洞，耗时: {elapsed_time:.1f}秒")
            if result['details'].get('note'):
                print(f"   ℹ️  {result['details']['note']}")

        return result

    except subprocess.TimeoutExpired:
        print(f"   ⏰ 测试超时（3分钟）")
        return {
            'test_case': test_case['description'],
            'url': test_case['url'],
            'timeout': True,
            'success': False,
            'vulnerable': False,
            'details': {'error': 'Timeout after 180 seconds'}
        }
    except Exception as e:
        print(f"   ❌ 执行出错: {e}")
        return {
            'test_case': test_case['description'],
            'url': test_case['url'],
            'success': False,
            'vulnerable': False,
            'details': {'error': str(e)}
        }

def main():
    """主函数"""
    print("=" * 60)
    print("精确DVWA SQL注入测试")
    print("=" * 60)

    # 1. 获取DVWA session
    print("\n1. 获取DVWA会话...")
    session = get_dvwa_session()

    if not session:
        print("❌ 无法继续测试")
        return

    # 获取cookie
    cookie = session.cookies.get('PHPSESSID')
    if not cookie:
        print("❌ 无法获取session cookie")
        return

    print(f"✅ 获取到PHPSESSID: {cookie[:10]}...")

    # 2. 分析页面交互
    print("\n2. 分析SQL注入页面交互...")
    test_cases = analyze_sqli_page_interaction(session)

    if not test_cases:
        print("❌ 无法分析页面交互")
        return

    print(f"✅ 生成 {len(test_cases)} 个测试用例")

    # 3. 运行测试用例
    print("\n3. 运行SQLMap测试用例...")
    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}/{len(test_cases)} ---")
        result = test_sqlmap_with_case(test_case, cookie)
        if result:
            results.append(result)

    # 4. 分析结果
    print("\n" + "="*60)
    print("4. 测试结果分析")
    print("="*60)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('success'))
    vulnerable_tests = sum(1 for r in results if r.get('vulnerable'))

    print(f"📊 总体统计:")
    print(f"   总测试用例: {total_tests}")
    print(f"   成功执行: {successful_tests}")
    print(f"   发现漏洞: {vulnerable_tests}")

    if successful_tests > 0:
        detection_rate = (vulnerable_tests / successful_tests) * 100
        print(f"   检测率: {detection_rate:.1f}%")
    else:
        detection_rate = 0
        print(f"   检测率: N/A (无成功测试)")

    # 详细结果
    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('vulnerable') else "❌"
        print(f"   {i}. {result['test_case']} - {status}")
        if result.get('timeout'):
            print(f"      ⏰ 超时")
        elif result.get('details', {}).get('note'):
            print(f"      ℹ️  {result['details']['note']}")

    # 5. 生成报告
    print("\n" + "="*60)
    print("5. 生成测试报告")
    print("="*60)

    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'target': 'DVWA SQL Injection (low security)',
        'cookie_obtained': cookie is not None,
        'test_cases_analyzed': len(test_cases),
        'results': results,
        'summary': {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'vulnerable_tests': vulnerable_tests,
            'detection_rate': detection_rate,
            'competition_requirement_met': detection_rate >= 90
        }
    }

    # 保存报告
    report_file = f"reports/precise_sqli_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("reports", exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ 报告已保存至: {report_file}")

    # 6. 竞赛评估
    print("\n" + "="*60)
    print("6. 竞赛指标评估")
    print("="*60)

    if detection_rate >= 90:
        print(f"🎉 恭喜！SQL注入检测率 {detection_rate:.1f}% 满足竞赛要求（≥90%）")
    else:
        print(f"⚠️  SQL注入检测率 {detection_rate:.1f}% 未达到竞赛要求（≥90%）")

        print(f"\n🔧 优化建议:")
        print(f"   1. 尝试其他SQL注入技术（时间盲注、报错注入等）")
        print(f"   2. 调整SQLMap的level和risk参数")
        print(f"   3. 测试DVWA的其他SQL注入页面（SQLi Blind）")
        print(f"   4. 验证DVWA数据库配置和连接")

    # 7. 生成演示数据
    print("\n" + "="*60)
    print("7. 生成竞赛演示数据")
    print("="*60)

    demo_stats = {
        'test_scenario': 'DVWA SQL Injection Detection',
        'test_date': report['timestamp'],
        'tools_used': ['SQLMap'],
        'parameters_tested': ['id', 'Submit'],
        'techniques_tested': ['Boolean-based blind', 'Error-based', 'UNION query', 'Stacked queries', 'Time-based blind'],
        'results_summary': {
            'best_case_detection': 'Vulnerable' if vulnerable_tests > 0 else 'Not Vulnerable',
            'execution_time_avg': sum(r.get('execution_time', 0) for r in results if r.get('execution_time')) / max(1, successful_tests),
            'tool_success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
        }
    }

    demo_file = f"reports/competition_sqli_demo_{time.strftime('%Y%m%d')}.json"
    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(demo_stats, f, indent=2, ensure_ascii=False)

    print(f"✅ 竞赛演示数据已保存至: {demo_file}")

    if vulnerable_tests > 0:
        print(f"\n🚀 下一步:")
        print(f"   1. 使用成功测试用例的参数进行完整渗透测试")
        print(f"   2. 测试DVWA其他漏洞类型（XSS、命令注入等）")
        print(f"   3. 准备PPT和演示视频素材")

if __name__ == "__main__":
    main()