# XHS Loop Engineer

> 小红书内容自动化工作流 — Loop Engineering 实战项目

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Loop-Engineering-orange.svg" alt="Loop Engineering">
  <img src="https://img.shields.io/badge/uv-包管理器-purple.svg" alt="uv">
</p>

---

## 🎯 一句话

用 Loop Engineering 的方式，把「选题 → 写稿 → 验证 → 归档 → 通知」的小红书内容生产流程自动化。

## 🧠 什么是 Loop Engineering？

> **不要做那个手动提示 Agent 的人。去设计一个自动调度 Agent 的系统。**

Loop Engineering 比提示词工程高一个层级。你不再是每篇文章都跟 AI 聊天，而是设计一个系统：

1. 定时唤醒
2. 发现热点选题
3. 按你的风格生成内容
4. 按你的标准验证质量
5. 自动保存到 Obsidian
6. 发送桌面通知

你只需要审核 + 发布。剩下的 Loop 帮你搞定。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│                  外层 Loop                       │
│                                                  │
│  触发（每天早 8 点 / 手动触发）                    │
│         ↓                                        │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 1: 选题发现                         │    │
│  │ 读取 Obsidian 选题库 + 数据看板            │    │
│  │ 输出：3 个候选选题                         │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│          ⚡ 人工确认（你选一个）                    │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 2: 内容生成                         │    │
│  │ 风格指南驱动的内容生成                     │    │
│  │ 输出：正文 + 标题 + 标签                    │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 3: 质量验证                         │    │
│  │ 敏感词 / 结构 / 标签 / 互动引导检查        │    │
│  │ 输出：通过 / 需修改                        │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 4: 归档 + 通知                      │    │
│  │ 保存到 Obsidian → 桌面通知                 │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  verifyCompletion: 确认发布？                     │
│    否 → 注入反馈 → Agent 2 重写                  │
│    是 → 归档 + 结束本轮                           │
└─────────────────────────────────────────────────┘
```

## 📁 项目结构

```
xhs-loop-engineer/
├── loop.py                    # Loop 主循环
├── agents/
│   ├── topic_finder.py        # Agent 1: 选题发现
│   ├── content_writer.py      # Agent 2: 内容生成
│   ├── quality_checker.py     # Agent 3: 质量验证
│   └── archiver.py            # Agent 4: 归档通知
├── config/
│   ├── style.yaml             # 风格指南（人设/禁忌词/结构规范）
│   └── schedule.yaml          # 发布计划（频率/Obsidian路径）
├── prompts/
│   ├── topic_finder.md        # 选题发现 prompt 模板
│   ├── content_writer.md      # 内容生成 prompt 模板
│   └── quality_checker.md     # 质量验证 prompt 模板
├── state/
│   └── loop_state.json        # Loop 状态持久化
├── output/                    # 生成内容输出
├── pyproject.toml             # 项目元数据 + 依赖（uv）
├── requirements.txt           # pip 兼容备用
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)（推荐包管理器）
- [Obsidian](https://obsidian.md/) vault 位于 `~/Documents/Obsidian Vault`
- macOS（桌面通知）或 Linux

### 安装

```bash
git clone git@github.com:mg1094/xhs-loop-engineer.git
cd xhs-loop-engineer

# 使用 uv 安装依赖
uv sync
source .venv/bin/activate
```

### 配置

编辑 `config/style.yaml`，设置你的人设和内容规则。

编辑 `config/schedule.yaml`，设置你的 Obsidian vault 路径和发布计划。

### 运行

```bash
python loop.py
```

## 📋 你的日常工作流

```
早 8 点 → 运行 python loop.py
        → Agent 1 展示 3 个候选选题
        → 你选一个
        → Agent 2 生成内容
        → Agent 3 验证质量
        → Agent 4 保存到 Obsidian + 桌面通知
        → 你打开 Obsidian，审核，复制到小红书
        → 发布
        → 搞定
```

## 🔧 配置说明

### style.yaml

定义内容风格：

- `forbidden_words` — 绝对不能出现的词
- `preferred_words` — 推荐用词和语气
- `structure` — 文章结构模板
- `article_types` — 小白文和技术深度稿的分别规则

### schedule.yaml

定义工作流：

- `frequency` — 发布频率
- `obsidian.vault_path` — Obsidian vault 路径
- `notification` — 桌面通知设置

## 🛠️ 技术栈

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) — 极速 Python 包管理器
- [Obsidian](https://obsidian.md/) — 本地 Markdown 知识库

## 🌐 语言

[English](README.md)

## 📄 许可证

MIT © [mg1094](https://github.com/mg1094)
