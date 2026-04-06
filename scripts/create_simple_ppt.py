# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建简化的ClawAI演示PPT（Markdown格式）
由于python-pptx可能存在安装问题，创建Markdown格式的PPT内容
"""

import os
from datetime import datetime

def create_ppt_markdown():
    """创建Markdown格式的PPT内容"""
    
    ppt_content = """# ClawAI Demo Presentation

## Slide 1: Title Slide
- **ClawAI**: AI-Powered Penetration Testing System
- **Team**: [Your Team Name]
- **Competition**: [Competition Name]
- **Tagline**: "From Manual to AI-Driven Security"

---

## Slide 2: Problem & Solution
### The Problem
- Manual penetration testing is slow (days/weeks)
- Expensive (security experts cost $100-300/hour)
- Inconsistent results (depends on individual skill)

### Our Solution
- AI automates the entire process
- 90% faster than manual testing
- Consistent, repeatable results
- 24/7 availability

---

## Slide 3: Architecture Overview
```
┌─────────────────────────────────────────┐
│ AI Core Layer                           │
│ • LLM Orchestrator (DeepSeek/OpenAI)    │
│ • Multi-Model Decision System           │
│ • Prompt Engineering                    │
│ • Explanation Engine                    │
├─────────────────────────────────────────┤
│ Workflow Engine                         │
│ • 6-Stage Penetration Testing           │
│ • AI-Guided Execution                   │
│ • Real-Time Monitoring                  │
├─────────────────────────────────────────┤
│ Tools Integration                       │
│ • 37 Security Tools (nmap, nuclei, etc) │
│ • Unified Execution Interface           │
│ • Result Aggregation                    │
└─────────────────────────────────────────┘
```

---

## Slide 4: AI Innovation Points
### 1. Multi-Model Decision Making
- 4 AI models (DeepSeek, OpenAI, Claude, Local)
- Collaborative voting system
- Confidence scoring for each decision

### 2. Smart Fallback System
- Primary: AI decision
- Fallback 1: Unified generator
- Fallback 2: Rule engine
- Ensures 100% availability

### 3. AI Explanation Engine
- Explains why AI made each decision
- Shows confidence levels
- Provides alternative options

### 4. Learning Capability
- Learns from successful attacks
- Improves over time
- Adapts to new targets

---

## Slide 5: Demo Screenshots
### Screenshot 1: AI Decision Panel
- Shows target analysis
- Displays vulnerability findings
- Presents recommended attack path

### Screenshot 2: Multi-Model Comparison
- Shows 4 AI models voting
- Displays confidence scores
- Highlights final decision

### Screenshot 3: Workflow Execution
- Shows 6-stage progress
- Real-time execution status
- Final results summary

---

## Slide 6: 3 Demo Scenarios (5 Minutes)
### Scene 1: AI Decision Making (90 seconds)
- Target: demo-target.com
- AI analyzes and recommends attack
- Score: 8.5/10, Confidence: 92%

### Scene 2: Multi-Model Comparison (90 seconds)
- 4 AI models vote independently
- 3/4 support rce_attack
- Final decision: rce_attack

### Scene 3: Complete Workflow (90 seconds)
- 6-stage penetration testing
- Total time: 24.4 seconds
- Success: All stages completed

---

## Slide 7: Technical Advantages
### ✅ Real AI, Not Rule Engine
- True machine learning decisions
- Not just if-then rules

### ✅ 37 Tools Integrated
- Far exceeds competition requirements
- Covers all penetration testing needs

### ✅ Production Ready
- Docker containerization
- One-command deployment
- Scalable architecture

### ✅ Enterprise Features
- Role-based access control
- Audit logging
- Report generation
- API integration

---

## Slide 8: Thank You & Q&A
### Contact Information
- GitHub: [Your GitHub URL]
- Email: [Your Email]
- Website: [Your Website]

### Next Steps
- Open source community edition
- Enterprise version development
- Partner integrations

### Q&A
**Questions?**
"""

    return ppt_content

def create_slide_deck():
    """创建幻灯片文件"""
    
    print("创建ClawAI演示幻灯片...")
    
    # 创建Markdown格式的PPT
    markdown_content = create_ppt_markdown()
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file = f"ClawAI_Demo_Presentation_{timestamp}.md"
    
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Markdown幻灯片已创建: {markdown_file}")
    
    # 创建文本格式的PPT（兼容性更好）
    text_file = f"ClawAI_Demo_Presentation_{timestamp}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("ClawAI Demo Presentation\n")
        f.write("=" * 50 + "\n\n")
        
        # 转换为文本格式
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                f.write("\n" + line[2:] + "\n" + "=" * len(line[2:]) + "\n\n")
            elif line.startswith('## '):
                f.write("\n" + line[3:] + "\n" + "-" * len(line[3:]) + "\n\n")
            elif line.startswith('### '):
                f.write(line[4:] + "\n")
            elif line.strip() == '---':
                f.write("\n" + "-" * 50 + "\n\n")
            elif line.strip():
                f.write("  " + line + "\n")
            else:
                f.write("\n")
    
    print(f"文本格式幻灯片已创建: {text_file}")
    
    # 创建PPT使用说明
    readme_content = f"""# ClawAI 演示幻灯片使用说明

## 文件说明
1. `{markdown_file}` - Markdown格式的幻灯片，支持GitHub预览
2. `{text_file}` - 纯文本格式的幻灯片，兼容所有编辑器

## 如何使用
### 选项1: 使用现有PPT工具
1. 将Markdown文件导入到PPT工具中
2. 使用分隔符"---"作为幻灯片分隔
3. 标题使用"# Slide X: Title"格式

### 选项2: 直接使用文本文件
1. 使用任何文本编辑器打开
2. 按照分隔符进行演示
3. 每页幻灯片之间有清晰的分隔

### 选项3: 转换为PPTX格式
如果需要PowerPoint格式，请：
1. 安装python-pptx: `pip install python-pptx`
2. 运行: `python utils/create_ppt.py`

## 幻灯片内容
共有8张幻灯片:
1. 标题页
2. 问题与解决方案
3. 架构概述
4. AI创新点
5. 演示截图
6. 3个演示场景
7. 技术优势
8. 感谢与Q&A

## 演示建议
1. 每张幻灯片演示时间: 30-60秒
2. 总演示时间: 5-8分钟
3. 重点展示: AI创新点、演示场景、技术优势

创建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    readme_file = "PPT_README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"使用说明已创建: {readme_file}")
    
    return {
        "markdown_file": markdown_file,
        "text_file": text_file,
        "readme_file": readme_file
    }

def main():
    """主函数"""
    print("=" * 60)
    print("ClawAI 演示幻灯片生成工具")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        files = create_slide_deck()
        
        print("\n" + "=" * 60)
        print("生成完成！")
        print("=" * 60)
        
        print("\n已创建的文件:")
        for key, filename in files.items():
            print(f"  - {key}: {filename}")
        
        print("\n使用建议:")
        print("  1. 使用Markdown文件进行预览和编辑")
        print("  2. 使用文本文件进行简单演示")
        print("  3. 参考README文件了解详细信息")
        
        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"创建幻灯片时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)