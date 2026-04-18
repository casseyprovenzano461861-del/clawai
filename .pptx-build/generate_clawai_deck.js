const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const outputPath = path.resolve("E:/ClawAI/比赛材料/ClawAI_项目介绍_初稿.pptx");

const C = {
  navy: "0F172A",
  darkCard: "111827",
  text: "0F172A",
  slate: "64748B",
  line: "DCE4EE",
  bg: "F7F9FC",
  card: "FFFFFF",
  teal: "14B8A6",
  cyan: "0EA5E9",
  green: "22C55E",
  amber: "F59E0B",
  red: "EF4444",
  softBlue: "DBEAFE",
  softTeal: "CCFBF1",
  softGreen: "DCFCE7",
  softAmber: "FEF3C7",
  softRed: "FEE2E2",
  softSlate: "E2E8F0",
  white: "FFFFFF",
};

const FONT = "Microsoft YaHei";
const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_16x9";
pptx.author = "CodeBuddy";
pptx.company = "ClawAI";
pptx.subject = "ClawAI 项目介绍";
pptx.title = "ClawAI — 基于大模型的自动化渗透测试系统";
pptx.lang = "zh-CN";

const line = (color = C.line, width = 1) => ({ color, width });

function footer(slide, text = "ClawAI · Project Deck", dark = false) {
  const color = dark ? "94A3B8" : "94A3B8";
  slide.addText(text, {
    x: 0.55, y: 5.23, w: 5.2, h: 0.18,
    fontFace: FONT, fontSize: 8, color, margin: 0,
  });
  slide.addText("仅限授权测试环境", {
    x: 7.75, y: 5.23, w: 1.7, h: 0.18,
    fontFace: FONT, fontSize: 8, color, align: "right", margin: 0,
  });
}

function header(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.55, y: 0.34, w: 6.8, h: 0.36,
    fontFace: FONT, fontSize: 24, bold: true, color: C.text, margin: 0,
  });
  slide.addText(subtitle, {
    x: 0.55, y: 0.76, w: 8.4, h: 0.2,
    fontFace: FONT, fontSize: 10, color: C.slate, margin: 0,
  });
  slide.addShape(pptx.shapes.LINE, {
    x: 0.55, y: 1.05, w: 8.9, h: 0,
    line: line(C.line, 1),
  });
}

function pill(slide, text, x, y, w, fill = C.softBlue, color = C.cyan) {
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h: 0.28,
    fill: { color: fill },
    line: { color: fill },
  });
  slide.addText(text, {
    x: x + 0.08, y: y + 0.055, w: w - 0.16, h: 0.15,
    fontFace: FONT, fontSize: 9, bold: true, color, align: "center", margin: 0,
  });
}

function addBullets(slide, items, x, y, w, h, options = {}) {
  const fontSize = options.fontSize || 9.5;
  const color = options.color || C.slate;
  const runs = [];
  items.forEach((item, idx) => {
    runs.push({
      text: item,
      options: {
        bullet: true,
        breakLine: idx < items.length - 1,
        fontFace: FONT,
        fontSize,
        color,
      },
    });
  });
  slide.addText(runs, {
    x, y, w, h,
    margin: 0.02,
    paraSpaceAfterPt: 6,
    breakLine: false,
  });
}

function rectCard(slide, { x, y, w, h, title, body, accent = C.teal, fill = C.card, titleColor = C.text, bodyColor = C.slate, dark = false }) {
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: dark ? fill : C.line, width: 1 },
  });
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w: 0.08, h,
    fill: { color: accent },
    line: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.18, y: y + 0.16, w: w - 0.28, h: 0.24,
    fontFace: FONT, fontSize: 13.5, bold: true, color: titleColor, margin: 0,
  });
  if (Array.isArray(body)) {
    addBullets(slide, body, x + 0.18, y + 0.48, w - 0.28, h - 0.58, { fontSize: 9.2, color: bodyColor });
  } else {
    slide.addText(body, {
      x: x + 0.18, y: y + 0.46, w: w - 0.28, h: h - 0.56,
      fontFace: FONT, fontSize: 9.5, color: bodyColor, margin: 0,
      valign: "top",
    });
  }
}

function metricCard(slide, { x, y, w, h, value, label, note = "", accent = C.teal, fill = C.card, valueColor = C.text, labelColor = C.slate }) {
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: fill === C.darkCard ? fill : C.line, width: 1 },
  });
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h: 0.07,
    fill: { color: accent },
    line: { color: accent },
  });
  slide.addText(value, {
    x: x + 0.12, y: y + 0.16, w: w - 0.24, h: 0.36,
    fontFace: FONT, fontSize: 22, bold: true, color: valueColor, margin: 0,
    align: "center",
  });
  slide.addText(label, {
    x: x + 0.12, y: y + 0.56, w: w - 0.24, h: 0.18,
    fontFace: FONT, fontSize: 9.2, color: labelColor, margin: 0, align: "center",
  });
  if (note) {
    slide.addText(note, {
      x: x + 0.12, y: y + 0.78, w: w - 0.24, h: 0.16,
      fontFace: FONT, fontSize: 8, color: labelColor, margin: 0, align: "center",
    });
  }
}

function stepBox(slide, { x, y, w, h, index, title, detail, fill = C.card, accent = C.cyan }) {
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: C.line, width: 1 },
  });
  slide.addShape(pptx.shapes.OVAL, {
    x: x + 0.12, y: y + 0.12, w: 0.34, h: 0.34,
    fill: { color: accent },
    line: { color: accent },
  });
  slide.addText(String(index), {
    x: x + 0.12, y: y + 0.19, w: 0.34, h: 0.1,
    fontFace: FONT, fontSize: 10, bold: true, color: C.white, align: "center", margin: 0,
  });
  slide.addText(title, {
    x: x + 0.55, y: y + 0.12, w: w - 0.67, h: 0.18,
    fontFace: FONT, fontSize: 11, bold: true, color: C.text, margin: 0,
  });
  slide.addText(detail, {
    x: x + 0.55, y: y + 0.34, w: w - 0.67, h: h - 0.42,
    fontFace: FONT, fontSize: 8.6, color: C.slate, margin: 0,
  });
}

function addChartTitle(slide, title, x, y, w) {
  slide.addText(title, {
    x, y, w, h: 0.18,
    fontFace: FONT, fontSize: 10.5, bold: true, color: C.text, margin: 0,
  });
}

function buildSlides() {
  // 1. Cover
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.navy };
    slide.addShape(pptx.shapes.OVAL, { x: 7.2, y: 0.15, w: 2.2, h: 2.2, fill: { color: C.cyan, transparency: 86 }, line: { color: C.cyan, transparency: 100 } });
    slide.addShape(pptx.shapes.OVAL, { x: 8.05, y: 0.95, w: 1.35, h: 1.35, fill: { color: C.teal, transparency: 82 }, line: { color: C.teal, transparency: 100 } });
    slide.addShape(pptx.shapes.LINE, { x: 6.45, y: 1.18, w: 2.5, h: 0, line: { color: "1D4ED8", width: 1, transparency: 50 } });
    slide.addShape(pptx.shapes.LINE, { x: 6.45, y: 1.7, w: 2.5, h: 0, line: { color: "14B8A6", width: 1, transparency: 45 } });

    pill(slide, "赛题 A10 · 安恒信息命题", 0.7, 0.55, 1.8, "1E293B", C.white);
    slide.addText("ClawAI", {
      x: 0.7, y: 1.08, w: 4.8, h: 0.55,
      fontFace: FONT, fontSize: 30, bold: true, color: C.white, margin: 0,
    });
    slide.addText("基于大模型的自动化渗透测试系统", {
      x: 0.7, y: 1.7, w: 5.5, h: 0.35,
      fontFace: FONT, fontSize: 18, bold: true, color: "D6F4FF", margin: 0,
    });
    slide.addText("让 AI 参与目标分析、漏洞发现、利用验证与报告生成，形成可复用、可量化、可演示的安全测试闭环。", {
      x: 0.7, y: 2.2, w: 4.8, h: 0.55,
      fontFace: FONT, fontSize: 10.5, color: "CBD5E1", margin: 0,
    });

    const coverTags = [
      "P-E-R 智能体闭环",
      "30+ 安全工具能力",
      "27 类 Skills / 14+ CVE",
      "Web + CLI + API",
    ];
    coverTags.forEach((tag, idx) => {
      slide.addShape(pptx.shapes.RECTANGLE, {
        x: 6.5, y: 1.0 + idx * 0.52, w: 2.55, h: 0.36,
        fill: { color: C.darkCard }, line: { color: "1F2937", width: 1 },
      });
      slide.addText(tag, {
        x: 6.65, y: 1.11 + idx * 0.52, w: 2.2, h: 0.12,
        fontFace: FONT, fontSize: 9.5, bold: true, color: C.white, margin: 0,
      });
    });

    metricCard(slide, { x: 0.7, y: 4.12, w: 2.6, h: 0.95, value: "100%", label: "DVWA 检测率", note: "10 / 10 漏洞检出", accent: C.green, fill: C.darkCard, valueColor: C.white, labelColor: "CBD5E1" });
    metricCard(slide, { x: 3.45, y: 4.12, w: 2.6, h: 0.95, value: "100%", label: "Pikachu 检测率", note: "15 / 15 漏洞检出", accent: C.teal, fill: C.darkCard, valueColor: C.white, labelColor: "CBD5E1" });
    metricCard(slide, { x: 6.2, y: 4.12, w: 2.85, h: 0.95, value: "176", label: "自动化测试通过", note: "0 failed / 16 skipped", accent: C.cyan, fill: C.darkCard, valueColor: C.white, labelColor: "CBD5E1" });

    slide.addText("项目介绍初稿 · 基于仓库文档与量化测试材料自动整理", {
      x: 0.7, y: 5.18, w: 5.8, h: 0.18,
      fontFace: FONT, fontSize: 8.3, color: "94A3B8", margin: 0,
    });
    slide.addText("2026", {
      x: 8.7, y: 5.18, w: 0.35, h: 0.18,
      fontFace: FONT, fontSize: 8.3, color: "94A3B8", align: "right", margin: 0,
    });
  }

  // 2. Pain points
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "为什么需要 ClawAI", "把专家经验转化为可复用、可扩展、可量化的自动化流程");

    rectCard(slide, {
      x: 0.6, y: 1.35, w: 2.7, h: 3.2,
      title: "痛点一：强依赖专家",
      body: ["一次完整手工渗透通常需要 3–7 天", "高度依赖资深工程师经验与临场判断", "人员稀缺时难以形成稳定产能"],
      accent: C.red,
      fill: C.card,
    });
    slide.addText("3–7 天", { x: 1.0, y: 3.55, w: 1.9, h: 0.35, fontFace: FONT, fontSize: 22, bold: true, color: C.red, align: "center", margin: 0 });

    rectCard(slide, {
      x: 3.65, y: 1.35, w: 2.7, h: 3.2,
      title: "痛点二：效率与覆盖不足",
      body: ["流程割裂，资产发现、验证、报告往往分散进行", "测试人员精力有限，容易遗漏漏洞类型", "企业平均漏洞暴露窗口可达 197 天"],
      accent: C.amber,
      fill: C.card,
    });
    slide.addText("197 天", { x: 4.05, y: 3.55, w: 1.95, h: 0.35, fontFace: FONT, fontSize: 22, bold: true, color: C.amber, align: "center", margin: 0 });

    rectCard(slide, {
      x: 6.7, y: 1.35, w: 2.7, h: 3.2,
      title: "痛点三：结果不稳定",
      body: ["不同测试人员对同一目标的结果差异明显", "传统口径下误报率常见 15%–30%", "复盘与复现实验成本较高"],
      accent: C.cyan,
      fill: C.card,
    });
    slide.addText("15%–30%", { x: 7.03, y: 3.55, w: 2.05, h: 0.35, fontFace: FONT, fontSize: 22, bold: true, color: C.cyan, align: "center", margin: 0 });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.75, y: 4.82, w: 8.5, h: 0.36, fill: { color: "EAF2FF" }, line: { color: "EAF2FF" } });
    slide.addText("传统方式：慢 / 贵 / 依赖个人  →  ClawAI：自动化 / 标准化 / 可复现", {
      x: 0.95, y: 4.92, w: 8.1, h: 0.12, fontFace: FONT, fontSize: 10.2, bold: true, color: "1E3A8A", align: "center", margin: 0,
    });
    footer(slide);
  }

  // 3. Product positioning
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "产品定位：AI 驱动的全流程渗透测试系统", "从目标分析到报告生成，让任务闭环像“安全工程师团队”一样协同运行");

    const flowX = [0.65, 2.08, 3.51, 4.94, 6.37];
    const flowTitles = ["目标分析", "资产识别", "漏洞发现", "利用验证", "报告生成"];
    const flowDetails = ["理解目标与范围", "识别端口 / 服务 / 技术栈", "调用工具与 Skills 检测", "根据结果执行利用与复核", "沉淀 Findings 与修复建议"];
    flowX.forEach((x, idx) => {
      slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1.8, w: 1.15, h: 0.88, fill: { color: C.card }, line: { color: C.line, width: 1 } });
      slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1.8, w: 1.15, h: 0.08, fill: { color: idx % 2 === 0 ? C.teal : C.cyan }, line: { color: idx % 2 === 0 ? C.teal : C.cyan } });
      slide.addText(flowTitles[idx], { x: x + 0.08, y: 2.06, w: 0.99, h: 0.14, fontFace: FONT, fontSize: 10.4, bold: true, color: C.text, align: "center", margin: 0 });
      slide.addText(flowDetails[idx], { x: x + 0.08, y: 2.26, w: 0.99, h: 0.26, fontFace: FONT, fontSize: 8.1, color: C.slate, align: "center", margin: 0 });
      if (idx < flowX.length - 1) {
        slide.addShape(pptx.shapes.LINE, { x: x + 1.15, y: 2.24, w: 0.28, h: 0, line: { color: C.cyan, width: 2 } });
      }
    });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.72, y: 3.0, w: 6.95, h: 0.45, fill: { color: C.softTeal }, line: { color: C.softTeal } });
    slide.addText("失败或结果不充分时，由 Reflector 触发重规划，再次进入 Planner → Executor 循环", {
      x: 0.95, y: 3.13, w: 6.5, h: 0.12, fontFace: FONT, fontSize: 10.2, bold: true, color: "0F766E", align: "center", margin: 0,
    });

    rectCard(slide, { x: 7.95, y: 1.38, w: 1.35, h: 0.95, title: "统一入口", body: "Web / CLI / API", accent: C.cyan, fill: C.card });
    rectCard(slide, { x: 7.95, y: 2.43, w: 1.35, h: 0.95, title: "统一调度", body: "P-E-R 智能体协作", accent: C.teal, fill: C.card });
    rectCard(slide, { x: 7.95, y: 3.48, w: 1.35, h: 0.95, title: "统一产出", body: "Finding / 历史 / 报告", accent: C.green, fill: C.card });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.72, y: 4.55, w: 8.55, h: 0.45, fill: { color: "EAF2FF" }, line: { color: "EAF2FF" } });
    slide.addText("一句话概括：这不是“会聊天的工具集合”，而是“会规划、会调用、会复盘、会出报告”的自动化安全测试系统。", {
      x: 0.95, y: 4.68, w: 8.1, h: 0.13, fontFace: FONT, fontSize: 10.2, bold: true, color: "1E3A8A", align: "center", margin: 0,
    });
    footer(slide);
  }

  // 4. Architecture
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "核心架构：Planner · Executor · Reflector", "上层接收任务，中层做智能决策，下层编排工具与技能，形成可解释的闭环");

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.75, y: 1.34, w: 8.5, h: 0.5, fill: { color: C.card }, line: { color: C.line, width: 1 } });
    slide.addText("用户交互层", { x: 0.95, y: 1.51, w: 1.2, h: 0.12, fontFace: FONT, fontSize: 11, bold: true, color: C.text, margin: 0 });
    ["Web Dashboard", "CLI / TUI", "REST API"].forEach((item, idx) => {
      pill(slide, item, 2.55 + idx * 1.85, 1.45, 1.55, idx === 1 ? C.softTeal : C.softBlue, idx === 1 ? C.teal : C.cyan);
    });

    rectCard(slide, { x: 1.0, y: 2.18, w: 2.15, h: 1.75, title: "Planner", body: ["理解用户目标与范围", "分解为可执行子任务图", "选择阶段与优先级"], accent: C.cyan, fill: C.card });
    rectCard(slide, { x: 3.42, y: 2.18, w: 2.15, h: 1.75, title: "Executor", body: ["调用安全工具与 Skills", "支持真实 / 模拟 / 混合执行", "收集证据与运行状态"], accent: C.teal, fill: C.card });
    rectCard(slide, { x: 5.84, y: 2.18, w: 2.15, h: 1.75, title: "Reflector", body: ["评估结果质量与完整性", "判断是否需要重规划", "输出下一步建议"], accent: C.green, fill: C.card });

    slide.addShape(pptx.shapes.LINE, { x: 3.15, y: 3.02, w: 0.27, h: 0, line: { color: C.cyan, width: 2 } });
    slide.addShape(pptx.shapes.LINE, { x: 5.57, y: 3.02, w: 0.27, h: 0, line: { color: C.teal, width: 2 } });
    slide.addShape(pptx.shapes.LINE, { x: 5.84, y: 3.6, w: -4.84, h: 0, line: { color: C.green, width: 1.5, dashType: "dash" } });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.75, y: 4.2, w: 6.6, h: 0.65, fill: { color: C.card }, line: { color: C.line, width: 1 } });
    slide.addText("工具与能力层", { x: 0.95, y: 4.45, w: 1.2, h: 0.12, fontFace: FONT, fontSize: 11, bold: true, color: C.text, margin: 0 });
    ["信息收集", "端口扫描", "Web 漏扫", "漏洞利用", "后渗透", "报告生成"].forEach((item, idx) => {
      pill(slide, item, 2.1 + (idx % 3) * 1.45, 4.28 + (idx > 2 ? 0.2 : 0), 1.18, idx % 2 === 0 ? C.softTeal : C.softBlue, idx % 2 === 0 ? C.teal : C.cyan);
    });

    rectCard(slide, { x: 7.6, y: 4.2, w: 1.65, h: 0.65, title: "实时事件", body: "EventBus → WebSocket\n状态 / 工具 / Finding / Progress", accent: C.amber, fill: C.card });
    footer(slide);
  }

  // 5. Capability matrix
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "能力矩阵：不仅能测，还能“协同、解释、沉淀”", "核心能力来自智能体方法论、工具链整合、技能库封装与多入口交付");

    metricCard(slide, { x: 0.65, y: 1.25, w: 2.0, h: 0.85, value: "30+", label: "安全工具能力", accent: C.cyan });
    metricCard(slide, { x: 2.85, y: 1.25, w: 2.0, h: 0.85, value: "27", label: "类 Skills", accent: C.teal });
    metricCard(slide, { x: 5.05, y: 1.25, w: 2.0, h: 0.85, value: "14+", label: "CVE 利用模块", accent: C.green });
    metricCard(slide, { x: 7.25, y: 1.25, w: 2.0, h: 0.85, value: "5", label: "类 LLM 后端", accent: C.amber });

    const cards = [
      { x: 0.65, y: 2.35, title: "自主规划", body: ["目标拆解", "任务依赖图", "阶段优先级选择"], accent: C.cyan },
      { x: 3.35, y: 2.35, title: "工具编排", body: ["真实 / 模拟 / 混合执行", "超时与结果收集", "统一接口调用"], accent: C.teal },
      { x: 6.05, y: 2.35, title: "技能利用", body: ["Payload 构造与解析封装", "漏洞验证流程复用", "支持 Function Calling"], accent: C.green },
      { x: 0.65, y: 4.0, title: "模型路由", body: ["OpenAI / DeepSeek / Anthropic", "Ollama / Mock", "按复杂度与成本分层"], accent: C.amber },
      { x: 3.35, y: 4.0, title: "多入口交付", body: ["Web Dashboard", "CLI / TUI", "REST API / WebSocket"], accent: C.cyan },
      { x: 6.05, y: 4.0, title: "报告与治理", body: ["Finding / 历史 / 报告", "JWT + RBAC + Audit", "速率限制与输入验证"], accent: C.red },
    ];
    cards.forEach((c) => rectCard(slide, { x: c.x, y: c.y, w: 2.35, h: 1.35, title: c.title, body: c.body, accent: c.accent, fill: C.card }));
    footer(slide);
  }

  // 6. Tech stack
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "技术栈与交付形态", "Python 后端 + React 前端 + 事件驱动实时体验，形成完整的项目交付面");

    rectCard(slide, { x: 0.65, y: 1.28, w: 4.15, h: 1.0, title: "后端核心", body: ["Python 3.12 / FastAPI / SQLAlchemy / Pydantic", "Textual + Rich 构建 CLI / TUI", "P-E-R、LLM 路由、Skills、Tool Manager"], accent: C.cyan, fill: C.card });
    rectCard(slide, { x: 0.65, y: 2.48, w: 4.15, h: 1.0, title: "前端可视化", body: ["React 18 / Vite 5 / TailwindCSS 3", "Three.js 攻击链可视化", "vis-network 知识图谱 / 拓扑图"], accent: C.teal, fill: C.card });
    rectCard(slide, { x: 0.65, y: 3.68, w: 4.15, h: 1.0, title: "基础设施与运维", body: ["Docker / docker-compose", "Redis / Qdrant（可选增强）", "Prometheus + Grafana 监控"], accent: C.green, fill: C.card });

    rectCard(slide, { x: 5.15, y: 1.28, w: 1.9, h: 1.0, title: "Web", body: "Dashboard / 实时面板 / 历史视图", accent: C.cyan, fill: C.card });
    rectCard(slide, { x: 7.25, y: 1.28, w: 1.9, h: 1.0, title: "CLI", body: "chat / scan / tools / status", accent: C.teal, fill: C.card });
    rectCard(slide, { x: 5.15, y: 2.48, w: 1.9, h: 1.0, title: "API", body: "REST 接口 + WebSocket 事件", accent: C.green, fill: C.card });
    rectCard(slide, { x: 7.25, y: 2.48, w: 1.9, h: 1.0, title: "安全治理", body: "JWT / RBAC / Audit / Rate Limit", accent: C.amber, fill: C.card });
    rectCard(slide, { x: 5.15, y: 3.68, w: 4.0, h: 1.0, title: "交付结果", body: ["Finding 列表 / 漏洞明细", "渗透测试报告 / 历史记录", "支持展示、复盘与二次分析"], accent: C.red, fill: C.card });
    footer(slide);
  }

  // 7. Benchmarks
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "量化测试结果：真实靶场已形成可展示数据", "数据来自项目仓库中的 DVWA / Pikachu 在线量化测试报告与自动化测试统计");

    metricCard(slide, { x: 0.65, y: 1.28, w: 2.05, h: 0.95, value: "10 / 10", label: "DVWA 检出", note: "检测率 100%", accent: C.green });
    metricCard(slide, { x: 2.9, y: 1.28, w: 2.05, h: 0.95, value: "15 / 15", label: "Pikachu 检出", note: "检测率 100%", accent: C.teal });
    metricCard(slide, { x: 5.15, y: 1.28, w: 2.05, h: 0.95, value: "0%", label: "误报率", note: "两个靶场均为 0", accent: C.cyan });
    metricCard(slide, { x: 7.4, y: 1.28, w: 1.85, h: 0.95, value: "176", label: "自动化测试通过", note: "0 failed", accent: C.amber });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.65, y: 2.55, w: 4.1, h: 2.25, fill: { color: C.card }, line: { color: C.line, width: 1 } });
    slide.addShape(pptx.shapes.RECTANGLE, { x: 5.05, y: 2.55, w: 4.2, h: 2.25, fill: { color: C.card }, line: { color: C.line, width: 1 } });
    addChartTitle(slide, "检出漏洞数", 0.88, 2.72, 3.6);
    addChartTitle(slide, "靶场总耗时（秒）", 5.28, 2.72, 3.6);

    slide.addChart(pptx.charts.BAR, [{ name: "Vulns", labels: ["DVWA", "Pikachu"], values: [10, 15] }], {
      x: 0.88, y: 2.96, w: 3.62, h: 1.5,
      barDir: "col",
      showTitle: false,
      showLegend: false,
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelColor: C.text,
      chartColors: [C.teal, C.cyan],
      chartArea: { fill: { color: C.white } },
      catAxisLabelColor: C.slate,
      valAxisLabelColor: C.slate,
      valGridLine: { color: C.softSlate, size: 0.5 },
      catGridLine: { style: "none" },
      valAxisMinVal: 0,
      valAxisMaxVal: 16,
    });

    slide.addChart(pptx.charts.BAR, [{ name: "Seconds", labels: ["DVWA", "Pikachu"], values: [9.8, 2.4] }], {
      x: 5.28, y: 2.96, w: 3.62, h: 1.5,
      barDir: "col",
      showTitle: false,
      showLegend: false,
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelColor: C.text,
      chartColors: [C.amber, C.green],
      chartArea: { fill: { color: C.white } },
      catAxisLabelColor: C.slate,
      valAxisLabelColor: C.slate,
      valGridLine: { color: C.softSlate, size: 0.5 },
      catGridLine: { style: "none" },
      valAxisMinVal: 0,
      valAxisMaxVal: 12,
    });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.85, y: 4.94, w: 8.2, h: 0.22, fill: { color: "EAF2FF" }, line: { color: "EAF2FF" } });
    slide.addText("DVWA 覆盖 8 种 CWE，Pikachu 覆盖 13 种 CWE；单次完整测试时间均远低于 30 分钟要求。", {
      x: 1.02, y: 5.01, w: 7.86, h: 0.1, fontFace: FONT, fontSize: 8.8, color: "1E3A8A", align: "center", margin: 0,
    });
    footer(slide);
  }

  // 8. Workflow timeline
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "运行流程：P-E-R + Skills + 事件总线", "把侦察、检测、利用、复盘和报告串成一条可追踪、可回放的执行链路");

    const steps = [
      { title: "接收目标", detail: "用户在 Web / CLI / API 中输入目标与意图", accent: C.cyan },
      { title: "规划阶段", detail: "Planner 拆解任务，生成子任务与优先级", accent: C.teal },
      { title: "执行阶段", detail: "Executor 调用工具 / Skills / CVE 模块", accent: C.green },
      { title: "反思阶段", detail: "Reflector 评估证据，决定继续、重试或调整", accent: C.amber },
      { title: "结果沉淀", detail: "生成 Finding、历史记录和报告", accent: C.red },
    ];
    steps.forEach((item, idx) => {
      stepBox(slide, { x: 0.6 + idx * 1.82, y: 1.7, w: 1.55, h: 1.2, index: idx + 1, title: item.title, detail: item.detail, accent: item.accent });
      if (idx < steps.length - 1) {
        slide.addShape(pptx.shapes.LINE, { x: 2.15 + idx * 1.82, y: 2.3, w: 0.22, h: 0, line: { color: C.cyan, width: 2 } });
      }
    });

    rectCard(slide, {
      x: 0.75, y: 3.28, w: 5.65, h: 1.2,
      title: "执行模式",
      body: ["Real：直接调用宿主机工具，适合授权靶场与真实环境", "Simulated：返回模拟结果，适合教学、演示与离线调试", "Hybrid：优先真实执行，失败时自动回退到模拟结果"],
      accent: C.teal,
      fill: C.card,
    });

    rectCard(slide, {
      x: 6.65, y: 3.28, w: 2.6, h: 1.2,
      title: "实时事件流",
      body: ["STATE_CHANGED：状态切换", "TOOL：工具开始 / 完成 / 错误", "FINDING / PROGRESS：发现与进度"],
      accent: C.cyan,
      fill: C.card,
    });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.75, y: 4.72, w: 8.5, h: 0.26, fill: { color: C.softTeal }, line: { color: C.softTeal } });
    slide.addText("EventBus → WebSocket 让前端可以实时看到：当前阶段、工具时间线、发现项与进度百分比。", {
      x: 0.96, y: 4.8, w: 8.08, h: 0.1, fontFace: FONT, fontSize: 8.9, color: "0F766E", align: "center", margin: 0,
    });
    footer(slide);
  }

  // 9. Engineering maturity
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "工程成熟度：从功能实现走向可维护、可运维、可审计", "项目不仅有功能展示，还有较完整的测试、权限、审计与部署支撑");

    rectCard(slide, {
      x: 0.65, y: 1.32, w: 4.45, h: 3.35,
      title: "四个已完成阶段",
      body: "",
      accent: C.cyan,
      fill: C.card,
    });

    const phases = [
      { y: 1.82, color: C.softBlue, accent: C.cyan, title: "Phase 1 · 安全加固", detail: "输入校验、JWT、RBAC、审计" },
      { y: 2.42, color: C.softTeal, accent: C.teal, title: "Phase 2 · 工程基础设施", detail: "LLM 抽象、EventBus、会话路由" },
      { y: 3.02, color: C.softGreen, accent: C.green, title: "Phase 3 · 功能补全", detail: "CLI/TUI、27 类 Skills、P-E-R 闭环" },
      { y: 3.62, color: C.softAmber, accent: C.amber, title: "Phase 4 · 生产就绪", detail: "Docker、日志、限流、监控" },
    ];
    phases.forEach((p) => {
      slide.addShape(pptx.shapes.RECTANGLE, { x: 0.95, y: p.y, w: 3.85, h: 0.42, fill: { color: p.color }, line: { color: p.color } });
      slide.addShape(pptx.shapes.RECTANGLE, { x: 0.95, y: p.y, w: 0.08, h: 0.42, fill: { color: p.accent }, line: { color: p.accent } });
      slide.addText(p.title, { x: 1.12, y: p.y + 0.08, w: 1.9, h: 0.12, fontFace: FONT, fontSize: 10, bold: true, color: C.text, margin: 0 });
      slide.addText(p.detail, { x: 3.0, y: p.y + 0.08, w: 1.6, h: 0.12, fontFace: FONT, fontSize: 8.3, color: C.slate, align: "right", margin: 0 });
    });

    metricCard(slide, { x: 5.45, y: 1.32, w: 1.2, h: 0.95, value: "134", label: "单元测试", note: "passed", accent: C.cyan });
    metricCard(slide, { x: 6.82, y: 1.32, w: 1.2, h: 0.95, value: "28", label: "集成测试", note: "passed", accent: C.teal });
    metricCard(slide, { x: 8.19, y: 1.32, w: 1.06, h: 0.95, value: "0", label: "failed", note: "总计 176", accent: C.green });

    rectCard(slide, { x: 5.45, y: 2.55, w: 1.8, h: 0.95, title: "认证与权限", body: "JWT + RBAC\n默认 5 类角色", accent: C.cyan, fill: C.card });
    rectCard(slide, { x: 7.45, y: 2.55, w: 1.8, h: 0.95, title: "审计与日志", body: "敏感操作审计\n结构化日志", accent: C.teal, fill: C.card });
    rectCard(slide, { x: 5.45, y: 3.72, w: 1.8, h: 0.95, title: "输入防护", body: "SQLi / XSS / 路径遍历\n命令注入检测", accent: C.green, fill: C.card });
    rectCard(slide, { x: 7.45, y: 3.72, w: 1.8, h: 0.95, title: "部署运维", body: "Docker / 监控 / 健康检查\nAPI 文档 / Swagger", accent: C.amber, fill: C.card });
    footer(slide);
  }

  // 10. Risks and roadmap
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.bg };
    header(slide, "下一阶段：把 Demo 能力继续打磨成稳定平台", "这页既说明当前可信度边界，也给出下一步里程碑与建议外宣口径");

    rectCard(slide, {
      x: 0.65, y: 1.32, w: 4.15, h: 2.95,
      title: "当前仍需持续优化的点",
      body: ["对外数字口径需统一，避免工具数与测试口径混用", "真实工具执行依赖宿主机环境，复现稳定性受安装状态影响", "长链路任务下，Planner / Reflector 决策仍可继续优化", "端口与部署说明需收敛，降低演示与部署成本"],
      accent: C.red,
      fill: C.card,
    });

    rectCard(slide, {
      x: 5.1, y: 1.32, w: 4.15, h: 2.95,
      title: "近期里程碑建议",
      body: ["统一 PPT、文档与比赛材料的引用口径", "扩展更多授权靶场与基准数据集", "继续完善实时扫描与 WebSocket 体验", "补齐部署演示站点、视频素材与报告模板"],
      accent: C.teal,
      fill: C.card,
    });

    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.85, y: 4.54, w: 8.2, h: 0.42, fill: { color: "EAF2FF" }, line: { color: "EAF2FF" } });
    slide.addText("建议外宣口径：30+ 工具能力 · 27 类 Skills · 14+ CVE 模块 · 5 类 LLM 后端 · DVWA / Pikachu 检测率 100%", {
      x: 1.02, y: 4.68, w: 7.86, h: 0.12, fontFace: FONT, fontSize: 9.4, bold: true, color: "1E3A8A", align: "center", margin: 0,
    });
    footer(slide);
  }

  // 11. Closing
  {
    const slide = pptx.addSlide();
    slide.background = { color: C.navy };
    slide.addShape(pptx.shapes.OVAL, { x: 7.6, y: 0.4, w: 1.9, h: 1.9, fill: { color: C.teal, transparency: 84 }, line: { color: C.teal, transparency: 100 } });
    slide.addShape(pptx.shapes.OVAL, { x: 8.2, y: 1.1, w: 1.1, h: 1.1, fill: { color: C.cyan, transparency: 82 }, line: { color: C.cyan, transparency: 100 } });

    pill(slide, "总结", 0.7, 0.6, 0.9, "1E293B", C.white);
    slide.addText("ClawAI 让 AI 成为渗透测试的协同专家", {
      x: 0.7, y: 1.22, w: 6.6, h: 0.55,
      fontFace: FONT, fontSize: 26, bold: true, color: C.white, margin: 0,
    });
    slide.addText("它把目标理解、工具调用、漏洞验证、结果复盘与报告生成串成了一个可展示、可扩展、可复现的完整系统。", {
      x: 0.7, y: 1.98, w: 6.0, h: 0.42,
      fontFace: FONT, fontSize: 11.2, color: "CBD5E1", margin: 0,
    });

    const closeCards = [
      { value: "P-E-R", label: "智能体闭环", accent: C.cyan },
      { value: "30+", label: "工具能力", accent: C.teal },
      { value: "27", label: "类 Skills", accent: C.green },
      { value: "5", label: "类 LLM", accent: C.amber },
      { value: "100%", label: "核心靶场检测率", accent: C.red },
    ];
    closeCards.forEach((card, idx) => {
      metricCard(slide, {
        x: 0.72 + idx * 1.78, y: 3.55, w: 1.48, h: 1.02,
        value: card.value, label: card.label, accent: card.accent,
        fill: C.darkCard, valueColor: C.white, labelColor: "CBD5E1",
      });
    });

    slide.addText("本演示基于项目仓库文档、比赛材料与量化测试报告自动生成；使用场景应严格限定在授权测试环境。", {
      x: 0.7, y: 4.92, w: 8.35, h: 0.2,
      fontFace: FONT, fontSize: 8.6, color: "94A3B8", margin: 0,
    });
    footer(slide, "ClawAI · Closing", true);
  }
}

async function main() {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  buildSlides();
  await pptx.writeFile({ fileName: outputPath });
  console.log(`PPT generated: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
