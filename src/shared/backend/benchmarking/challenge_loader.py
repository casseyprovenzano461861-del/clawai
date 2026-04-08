# -*- coding: utf-8 -*-
"""
挑战加载器模块
用于加载和管理测试挑战
"""

import os
import yaml
import json
from typing import List, Dict, Any


class ChallengeLoader:
    """挑战加载器类"""
    
    def __init__(self, challenges_dir="challenges"):
        self.challenges_dir = challenges_dir
        self.challenges = {}
        self._load_challenges()
    
    def _load_challenges(self):
        """加载挑战"""
        if not os.path.exists(self.challenges_dir):
            os.makedirs(self.challenges_dir)
            # 创建默认挑战
            self._create_default_challenges()
        
        # 加载挑战
        for filename in os.listdir(self.challenges_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                challenge_path = os.path.join(self.challenges_dir, filename)
                try:
                    with open(challenge_path, 'r', encoding='utf-8') as f:
                        challenge = yaml.safe_load(f)
                        challenge_name = challenge.get("name", os.path.splitext(filename)[0])
                        self.challenges[challenge_name] = challenge
                except Exception as e:
                    print(f"加载挑战 {filename} 失败: {e}")
    
    def _create_default_challenges(self):
        """创建默认挑战"""
        default_challenges = [
            {
                "name": "dvwa_basic",
                "description": "DVWA基础测试",
                "target": "http://localhost:8080/dvwa",
                "expected_flags": [
                    "flag{dvwa_basic_authentication_bypass}",
                    "flag{dvwa_basic_sql_injection}",
                    "flag{dvwa_basic_xss}"
                ],
                "difficulty": "easy",
                "categories": ["web", "dvwa"],
                "timeout": 3600
            },
            {
                "name": "metasploitable2",
                "description": "Metasploitable2测试",
                "target": "192.168.1.100",
                "expected_flags": [
                    "flag{metasploitable2_ssh_access}",
                    "flag{metasploitable2_web_vulnerability}",
                    "flag{metasploitable2_local_privilege_escalation}"
                ],
                "difficulty": "medium",
                "categories": ["network", "metasploitable"],
                "timeout": 7200
            },
            {
                "name": "owasp_top10",
                "description": "OWASP Top 10测试",
                "target": "http://localhost:8080/owasp",
                "expected_flags": [
                    "flag{owasp_injection}",
                    "flag{owasp_broken_auth}",
                    "flag{owasp_sensitive_data_exposure}",
                    "flag{owasp_xxe}",
                    "flag{owasp_broken_access_control}"
                ],
                "difficulty": "hard",
                "categories": ["web", "owasp"],
                "timeout": 10800
            }
        ]
        
        for challenge in default_challenges:
            filename = f"{challenge['name']}.yaml"
            challenge_path = os.path.join(self.challenges_dir, filename)
            with open(challenge_path, 'w', encoding='utf-8') as f:
                yaml.dump(challenge, f, default_flow_style=False, allow_unicode=True)
    
    def get_challenge(self, name):
        """获取挑战"""
        return self.challenges.get(name)
    
    def list_challenges(self):
        """列出所有挑战"""
        return list(self.challenges.keys())
    
    def list_challenges_by_category(self, category):
        """按类别列出挑战"""
        return [name for name, challenge in self.challenges.items() 
                if category in challenge.get("categories", [])]
    
    def add_challenge(self, challenge):
        """添加挑战"""
        name = challenge.get("name")
        if name:
            filename = f"{name}.yaml"
            challenge_path = os.path.join(self.challenges_dir, filename)
            with open(challenge_path, 'w', encoding='utf-8') as f:
                yaml.dump(challenge, f, default_flow_style=False, allow_unicode=True)
            self.challenges[name] = challenge
            return True
        return False
    
    def remove_challenge(self, name):
        """移除挑战"""
        if name in self.challenges:
            filename = f"{name}.yaml"
            challenge_path = os.path.join(self.challenges_dir, filename)
            if os.path.exists(challenge_path):
                os.remove(challenge_path)
            del self.challenges[name]
            return True
        return False
