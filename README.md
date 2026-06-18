# XHS Loop Engineer

> 小红书内容自动化工作流 — Loop Engineering 实战项目

## 🎯 一句话

用 Loop Engineering 的方式，把「选题 → 写稿 → 验证 → 归档 → 通知」的小红书内容生产流程自动化。

## 🧠 核心理念

Loop Engineering：**不要做那个手动提示 Agent 的人。去设计一个自动调度 Agent 的系统。**

```
定时触发（每天早上 8 点）
    ↓
Agent 1: 选题发现 → 3 个候选选题
    ↓
⚡ 人工确认（选一个）
    ↓
Agent 2: 内容生成 → 正文 + 标题 + 标签
    ↓
Agent 3: 质量验证 → 敏感词 / 风格 / 字数
    ↓
Agent 4: 归档 + 通知 → Obsidian + 推送
    ↓
verifyCompletion: 你确认发布了吗？
    ↓ No → 收集反馈 → Agent 2 重写
    ↓ Yes → 归档 + 结束本轮
```

## 🏗️ 目录结构

```
xhs-loop-engineer/
├── loop.py                 # Loop 主循环
├── agents/
│   ├── topic_finder.py     # Agent 1: 选题发现
│   ├── content_writer.py   # Agent 2: 内容生成
│   ├── quality_checker.py  # Agent 3: 质量验证
│   └── archiver.py         # Agent 4: 归档通知
├── config/
│   ├── style.yaml          # 风格指南
│   └── schedule.yaml       # 发布计划
├── prompts/
│   ├── topic_finder.md     # 选题发现 prompt
│   ├── content_writer.md   # 内容生成 prompt
│   └── quality_checker.md  # 质量验证 prompt
├── state/
│   └── loop_state.json     # Loop 状态
├── output/                 # 生成内容输出
├── requirements.txt
└── README.md
```

## 🚀 快速开始

```bash
pip install -r requirements.txt
python loop.py
```

## 📋 你的工作流

```
早 8 点 → 收到通知「今天有 3 个选题，选一个？」
       → 你回复「选 2」
       → Agent 写稿 → 验证通过
       → 收到通知「稿子已写好，在 Obsidian」
       → 你打开看一眼，复制到小红书发布
       → 回复「已发」
       → Agent 归档 + 更新数据看板
```

## 📄 License

MIT
