# -*- coding: utf-8 -*-
"""
提示管理器模块
用于加载和管理提示模板
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from .prompt_templates import PromptTemplates


class PromptManager:
    """提示管理器类"""
    
    def __init__(self, prompts_dir="prompts"):
        self.prompts_dir = prompts_dir
        self.templates = PromptTemplates()
        self.custom_prompts = {}
        self._load_custom_prompts()
    
    def _load_custom_prompts(self):
        """加载自定义提示"""
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir)
            # 创建默认提示配置
            self._create_default_prompts()
        
        # 加载自定义提示
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                prompt_path = os.path.join(self.prompts_dir, filename)
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompt = yaml.safe_load(f)
                        prompt_name = prompt.get("name", os.path.splitext(filename)[0])
                        self.custom_prompts[prompt_name] = prompt
                except Exception as e:
                    print(f"加载提示 {filename} 失败: {e}")
    
    def _create_default_prompts(self):
        """创建默认提示"""
        default_prompts = [
            {
                "name": "default_reconnaissance",
                "description": "默认侦察提示",
                "template": self.templates.get_template("reconnaissance"),
                "category": "reconnaissance",
                "version": "1.0.0"
            },
            {
                "name": "default_scanning",
                "description": "默认扫描提示",
                "template": self.templates.get_template("scanning"),
                "category": "scanning",
                "version": "1.0.0"
            },
            {
                "name": "default_exploitation",
                "description": "默认利用提示",
                "template": self.templates.get_template("exploitation"),
                "category": "exploitation",
                "version": "1.0.0"
            }
        ]
        
        for prompt in default_prompts:
            filename = f"{prompt['name']}.yaml"
            prompt_path = os.path.join(self.prompts_dir, filename)
            with open(prompt_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompt, f, default_flow_style=False, allow_unicode=True)
    
    def get_prompt(self, name: str) -> Optional[Dict[str, Any]]:
        """获取提示"""
        # 先查找自定义提示
        if name in self.custom_prompts:
            return self.custom_prompts[name]
        # 再查找内置模板
        template = self.templates.get_template(name)
        if template:
            return {
                "name": name,
                "description": f"内置{name}模板",
                "template": template,
                "category": name,
                "version": "1.0.0"
            }
        return None
    
    def list_prompts(self) -> list:
        """列出所有提示"""
        prompts = []
        # 内置模板
        for template_name in self.templates.list_templates():
            prompts.append({
                "name": template_name,
                "type": "builtin",
                "description": f"内置{template_name}模板"
            })
        # 自定义提示
        for name, prompt in self.custom_prompts.items():
            prompts.append({
                "name": name,
                "type": "custom",
                "description": prompt.get("description", "")
            })
        return prompts
    
    def add_prompt(self, prompt: Dict[str, Any]) -> bool:
        """添加自定义提示"""
        name = prompt.get("name")
        if name:
            filename = f"{name}.yaml"
            prompt_path = os.path.join(self.prompts_dir, filename)
            with open(prompt_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompt, f, default_flow_style=False, allow_unicode=True)
            self.custom_prompts[name] = prompt
            return True
        return False
    
    def update_prompt(self, name: str, prompt: Dict[str, Any]) -> bool:
        """更新自定义提示"""
        if name in self.custom_prompts:
            filename = f"{name}.yaml"
            prompt_path = os.path.join(self.prompts_dir, filename)
            with open(prompt_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompt, f, default_flow_style=False, allow_unicode=True)
            self.custom_prompts[name] = prompt
            return True
        return False
    
    def delete_prompt(self, name: str) -> bool:
        """删除自定义提示"""
        if name in self.custom_prompts:
            filename = f"{name}.yaml"
            prompt_path = os.path.join(self.prompts_dir, filename)
            if os.path.exists(prompt_path):
                os.remove(prompt_path)
            del self.custom_prompts[name]
            return True
        return False
    
    def render_prompt(self, name: str, **kwargs) -> Optional[str]:
        """渲染提示"""
        prompt = self.get_prompt(name)
        if prompt:
            template = prompt.get("template")
            if template:
                try:
                    return template.format(**kwargs)
                except KeyError as e:
                    print(f"渲染提示失败: 缺少参数 {e}")
                    return None
        return None
    
    def get_prompts_by_category(self, category: str) -> list:
        """按类别获取提示"""
        prompts = []
        # 内置模板
        if category in self.templates.list_templates():
            prompts.append({
                "name": category,
                "type": "builtin",
                "description": f"内置{category}模板"
            })
        # 自定义提示
        for name, prompt in self.custom_prompts.items():
            if prompt.get("category") == category:
                prompts.append({
                    "name": name,
                    "type": "custom",
                    "description": prompt.get("description", "")
                })
        return prompts
