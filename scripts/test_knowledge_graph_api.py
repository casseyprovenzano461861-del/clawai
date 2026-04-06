#!/usr/bin/env python3
"""
测试知识图谱API
"""
import sys
import os
import json
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.backend.graph.repository import KnowledgeGraphRepository
from src.shared.backend.graph.neo4j_client import Neo4jClient
from config.config import Config

def test_api_endpoints():
    """测试API端点"""
    base_url = "http://localhost:8000/api/v1/knowledge-graph"

    endpoints = [
        "/health",
        "/graph",
        "/nodes",
        "/edges",
        "/stats"
    ]

    print("测试知识图谱API端点...")

    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {endpoint}: 成功 (状态码: {response.status_code})")
                if data.get("success"):
                    print(f"  数据: {json.dumps(data.get('data', {}), indent=2, ensure_ascii=False)[:200]}...")
                else:
                    print(f"  错误: {data.get('detail', '未知错误')}")
            else:
                print(f"✗ {endpoint}: 失败 (状态码: {response.status_code})")
                print(f"  响应: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print(f"✗ {endpoint}: 无法连接到服务器，请确保后端服务正在运行")
            break
        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {str(e)}")

def test_mock_data_import():
    """测试模拟数据导入"""
    base_url = "http://localhost:8000/api/v1/knowledge-graph"

    print("\n测试模拟数据导入...")

    try:
        response = requests.post(base_url + "/import/mock", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                imported = data.get("data", {})
                print(f"✓ 模拟数据导入成功")
                print(f"  导入节点: {imported.get('imported_nodes', 0)}")
                print(f"  导入边: {imported.get('imported_edges', 0)}")
            else:
                print(f"✗ 模拟数据导入失败: {data.get('detail', '未知错误')}")
        else:
            print(f"✗ 模拟数据导入失败 (状态码: {response.status_code})")
            print(f"  响应: {response.text[:200]}")
    except Exception as e:
        print(f"✗ 模拟数据导入错误: {str(e)}")

def test_advanced_queries():
    """测试高级查询"""
    base_url = "http://localhost:8000/api/v1/knowledge-graph"

    print("\n测试高级查询...")

    queries = [
        "/attack-paths?start_type=host&end_type=asset",
        "/recommendations/vulnerability?limit=5"
    ]

    for query in queries:
        url = base_url + query
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {query}: 成功")
                if data.get("success"):
                    result = data.get("data", {})
                    if "paths" in result:
                        print(f"  找到 {len(result['paths'])} 条攻击路径")
                    elif "recommendations" in result:
                        print(f"  找到 {len(result['recommendations'])} 条推荐")
            else:
                print(f"✗ {query}: 失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"✗ {query}: 错误 - {str(e)}")

def test_neovis_integration():
    """测试Neo4j连接"""
    print("\n测试Neo4j连接...")

    try:
        from src.shared.backend.graph.neo4j_client import Neo4jClient
        from config.config import Config

        config = Config()
        client = Neo4jClient(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )

        # 测试连接
        with client.get_session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✓ Neo4j连接成功")

                # 检查数据库状态
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                for record in result:
                    print(f"  Neo4j版本: {record['name']} {record['versions'][0]} ({record['edition']})")

                # 检查图数据
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                record = result.single()
                print(f"  现有节点数: {record['node_count']}")

                result = session.run("MATCH ()-[r]->() RETURN count(r) as edge_count")
                record = result.single()
                print(f"  现有边数: {record['edge_count']}")
            else:
                print("✗ Neo4j连接测试失败")

    except Exception as e:
        print(f"✗ Neo4j连接错误: {str(e)}")
        print("  提示: 请确保Neo4j服务正在运行，并且配置正确")

def main():
    print("=" * 60)
    print("ClawAI 知识图谱集成测试")
    print("=" * 60)

    # 测试Neo4j连接
    test_neovis_integration()

    # 测试API端点
    test_api_endpoints()

    # 测试模拟数据导入
    test_mock_data_import()

    # 测试高级查询
    test_advanced_queries()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()