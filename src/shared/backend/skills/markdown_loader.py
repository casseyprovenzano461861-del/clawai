# -*- coding: utf-8 -*-
"""
Markdown Skill 加载器

支持从 .md 文件（YAML frontmatter + Python 代码体）加载自定义技能。

文件格式示例：
    ---
    name: my_scan
    description: 自定义扫描
    category: recon
    type: scanner
    severity: medium
    target_type: url
    parameters:
      - name: target
        type: string
        required: true
        description: 目标URL
    tags:
      - custom
    author: user
    ---

    import urllib.request
    target = "{{target}}"
    # ... Python 代码
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 延迟导入，避免循环依赖
_Skill = None
_SkillType = None
_SkillCategory = None
_SkillParameter = None


def _get_skill_classes():
    global _Skill, _SkillType, _SkillCategory, _SkillParameter
    if _Skill is None:
        from .core import Skill, SkillType, SkillCategory, SkillParameter
        _Skill = Skill
        _SkillType = SkillType
        _SkillCategory = SkillCategory
        _SkillParameter = SkillParameter
    return _Skill, _SkillType, _SkillCategory, _SkillParameter


# ──────────────────────────────────────────────
# 简易 YAML 解析（仅支持 Skill frontmatter 需要的子集）
# 不引入第三方依赖，优先用标准库 yaml，否则 fallback
# ──────────────────────────────────────────────

def _parse_yaml_subset(text: str) -> dict:
    """解析简单 YAML（支持字符串、整数、布尔值、字符串列表、对象列表）"""
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    # Fallback：手写简易解析器
    result = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # 跳过空行和注释
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue

        # 顶层键值对：key: value
        m = re.match(r'^(\w+)\s*:\s*(.*)', line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value_str = m.group(2).strip()

        if value_str == '' or value_str is None:
            # 可能是列表或对象块
            items = []
            i += 1
            while i < len(lines):
                item_line = lines[i]
                if not item_line.strip():
                    i += 1
                    continue
                # 子项以 "  -" 开头
                if re.match(r'^\s+-', item_line):
                    # 判断是简单字符串列表还是对象列表
                    inner = item_line.strip().lstrip('- ').strip()
                    if ':' in inner:
                        # 对象列表：收集到该对象的所有属性
                        obj = {}
                        prop_m = re.match(r'^(\w+)\s*:\s*(.*)', inner)
                        if prop_m:
                            obj[prop_m.group(1)] = _parse_scalar(prop_m.group(2).strip())
                        i += 1
                        while i < len(lines):
                            sub = lines[i]
                            if not sub.strip():
                                break
                            if re.match(r'^\s+-', sub):
                                break
                            if not re.match(r'^\s', sub):
                                break
                            prop_m2 = re.match(r'\s+(\w+)\s*:\s*(.*)', sub)
                            if prop_m2:
                                obj[prop_m2.group(1)] = _parse_scalar(prop_m2.group(2).strip())
                            i += 1
                        items.append(obj)
                    else:
                        items.append(_parse_scalar(inner))
                        i += 1
                else:
                    break
            result[key] = items
        else:
            result[key] = _parse_scalar(value_str)
            i += 1

    return result


def _parse_scalar(s: str):
    """将字符串解析为 Python 标量"""
    if s in ('true', 'True', 'yes'):
        return True
    if s in ('false', 'False', 'no'):
        return False
    if s in ('null', 'None', '~', ''):
        return None
    # 去除引号
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # 整数
    try:
        return int(s)
    except ValueError:
        pass
    # 浮点
    try:
        return float(s)
    except ValueError:
        pass
    return s


# ──────────────────────────────────────────────
# 映射 frontmatter 字段 → 枚举值
# ──────────────────────────────────────────────

_TYPE_MAP = {
    'poc': 'POC',
    'exploit': 'EXPLOIT',
    'scanner': 'SCANNER',
    'bruteforce': 'BRUTEFORCE',
    'recon': 'RECON',
    'post': 'POST',
}

_CATEGORY_MAP = {
    'sql_injection': 'SQL_INJECTION',
    'sqli': 'SQL_INJECTION',
    'xss': 'XSS',
    'rce': 'RCE',
    'lfi': 'LFI',
    'auth_bypass': 'AUTH_BYPASS',
    'info_disclosure': 'INFO_DISCLOSURE',
    'file_upload': 'FILE_UPLOAD',
    'ssrf': 'SSRF',
    'xxe': 'XXE',
    'csrf': 'CSRF',
    'recon': 'GENERAL',
    'general': 'GENERAL',
}


def _resolve_type(Cls, value: str, default_name: str):
    """按名称获取枚举成员，不存在则返回默认值"""
    norm = _TYPE_MAP.get(value.lower(), value.upper()) if value else default_name
    try:
        return Cls[norm]
    except KeyError:
        return Cls[default_name]


def _resolve_category(Cls, value: str):
    norm = _CATEGORY_MAP.get(value.lower(), value.upper()) if value else 'GENERAL'
    try:
        return Cls[norm]
    except KeyError:
        return Cls['GENERAL']


# ──────────────────────────────────────────────
# 主解析函数
# ──────────────────────────────────────────────

def parse_skill_markdown(file_path: str) -> Optional[object]:
    """
    解析单个 Markdown Skill 文件，返回 Skill 对象。
    解析失败返回 None（不抛出异常）。
    """
    Skill, SkillType, SkillCategory, SkillParameter = _get_skill_classes()
    path = Path(file_path)

    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"[MarkdownLoader] 无法读取文件 {file_path}: {e}")
        return None

    # 拆分 frontmatter 和代码体
    # 格式：--- \n <yaml> \n --- \n <code>
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        logger.warning(f"[MarkdownLoader] {path.name}: 缺少 YAML frontmatter（需要 --- 分隔符）")
        return None

    _, yaml_text, code_body = parts[0], parts[1], parts[2]
    code = code_body.strip()

    # 解析 frontmatter
    try:
        meta = _parse_yaml_subset(yaml_text)
    except Exception as e:
        logger.warning(f"[MarkdownLoader] {path.name}: frontmatter 解析失败: {e}")
        return None

    # 必填字段
    skill_id = meta.get('name') or path.stem
    if not skill_id:
        logger.warning(f"[MarkdownLoader] {path.name}: 缺少 name 字段")
        return None

    # 将文件名中的空格/连字符替换为下划线，确保 ID 合法
    skill_id = re.sub(r'[\s\-]+', '_', skill_id).lower()

    description = meta.get('description', f"用户自定义技能: {skill_id}")

    # 解析枚举
    skill_type = _resolve_type(SkillType, str(meta.get('type', 'scanner')), 'SCANNER')
    skill_category = _resolve_category(SkillCategory, str(meta.get('category', 'general')))

    # 解析参数列表
    parameters = []
    for p in meta.get('parameters', []):
        if not isinstance(p, dict):
            continue
        param_name = p.get('name')
        if not param_name:
            continue
        parameters.append(SkillParameter(
            name=str(param_name),
            type=str(p.get('type', 'string')),
            required=bool(p.get('required', True)),
            default=p.get('default'),
            description=str(p.get('description', '')),
        ))

    # 如果没有定义参数但代码中有 {{target}}，自动添加 target 参数
    if not parameters and '{{target}}' in code:
        parameters.append(SkillParameter(
            name='target',
            type='string',
            required=True,
            description='目标 URL 或 IP',
        ))

    # 构建 Skill 对象
    skill = Skill(
        id=skill_id,
        name=meta.get('display_name') or meta.get('name') or skill_id,
        type=skill_type,
        category=skill_category,
        description=description,
        parameters=parameters,
        target_type=str(meta.get('target_type', 'url')),
        severity=str(meta.get('severity', 'medium')),
        cve_id=meta.get('cve_id') or None,
        references=list(meta.get('references', [])),
        tags=list(meta.get('tags', ['custom'])),
        author=str(meta.get('author', 'user')),
        enabled=bool(meta.get('enabled', True)),
        executor='python',
        code=code,
    )

    logger.debug(f"[MarkdownLoader] 解析成功: {skill_id} ({path.name})")
    return skill


def load_skills_from_dir(dir_path: str) -> List[object]:
    """
    扫描目录中所有 *.md 文件，返回成功解析的 Skill 列表。
    目录不存在时静默返回空列表。
    """
    path = Path(dir_path)
    if not path.exists() or not path.is_dir():
        return []

    skills = []
    for md_file in sorted(path.glob('*.md')):
        skill = parse_skill_markdown(str(md_file))
        if skill is not None:
            skills.append(skill)

    if skills:
        logger.info(f"[MarkdownLoader] 从 {dir_path} 加载了 {len(skills)} 个自定义技能")

    return skills
