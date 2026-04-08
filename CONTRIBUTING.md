# ClawAI 贡献指南

## 欢迎加入 ClawAI 社区

我们非常欢迎并感谢所有对 ClawAI 项目的贡献！无论是代码提交、问题报告、文档改进还是功能建议，都是对项目的宝贵贡献。

## 贡献方式

### 1. 报告问题

如果您发现了 bug 或有功能建议，请在 [GitHub Issues](https://github.com/ClawAI/ClawAI/issues) 中提交。

**提交问题时，请包含以下信息**：
- 问题的详细描述
- 复现步骤
- 预期行为和实际行为
- 环境信息（操作系统、Python 版本等）
- 相关的错误信息或日志
- 可能的解决方案（如果您有）

### 2. 代码贡献

#### 开发环境设置

1. **克隆仓库**
   ```bash
   git clone https://github.com/ClawAI/ClawAI.git
   cd ClawAI
   ```

2. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **运行测试**
   ```bash
   pytest
   ```

#### 代码风格

- 遵循 PEP 8 编码规范
- 使用 4 个空格进行缩进
- 保持代码简洁明了
- 添加适当的注释
- 为新功能添加测试

#### 提交代码

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **提交更改**
   ```bash
   git add .
   git commit -m "描述您的更改"
   ```

3. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **创建 Pull Request**
   - 在 GitHub 上创建一个新的 Pull Request
   - 描述您的更改和解决的问题
   - 确保所有测试都通过

### 3. 文档贡献

文档改进是非常重要的贡献形式，包括：
- 更新 README.md
- 完善用户手册
- 改进 API 文档
- 添加使用示例
- 翻译文档

### 4. 案例分享

如果您使用 ClawAI 解决了实际问题，欢迎分享您的案例：
- 详细的使用场景
- 解决的问题
- 使用的工具和技术
- 取得的成果

请将案例提交到 [GitHub Discussions](https://github.com/ClawAI/ClawAI/discussions) 或发送邮件至 contact@clawai.com。

## 行为准则

我们希望 ClawAI 社区是一个友好、包容的环境。请遵循以下行为准则：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

## 贡献者表彰

所有贡献者都会在项目的贡献者列表中得到表彰。我们会定期更新贡献者名单，并在发布说明中感谢重要贡献。

## 联系方式

- **GitHub Issues**：https://github.com/ClawAI/ClawAI/issues
- **GitHub Discussions**：https://github.com/ClawAI/ClawAI/discussions
- **邮件**：contact@clawai.com
- **社区论坛**：https://forum.clawai.com

## 许可证

By contributing to ClawAI, you agree that your contributions will be licensed under the MIT License.

---

**感谢您的贡献！** 🎉