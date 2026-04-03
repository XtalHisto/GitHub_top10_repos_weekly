# GitHub Weekly Star Tracker

> A lightweight intelligence pipeline for discovering fast-growing GitHub repos, tracking weekly momentum, and delivering polished HTML reports.

## Overview

`GitHub Weekly Star Tracker` 是一个面向技术趋势观察的自动化工具链，核心目标是：

- 用候选集策略捕捉近期有热度的开源项目
- 用快照差分识别 Star 增长趋势
- 用 LLM 生成可读摘要并邮件分发

---

## Feature Matrix

| 模块 | 能力 | 状态 |
|---|---|---|
| 数据抓取 | 双查询策略（稳定项目 + 新兴项目） | ✅ |
| 数据清洗 | 按 `repo_id` 去重合并候选仓库 | ✅ |
| 快照存储 | SQLite 按日期存储仓库 Star 快照 | ✅ |
| 同日更新 | 同一天重复抓取时，使用新快照覆盖旧快照 | ✅ |
| 趋势计算 | 基于相邻快照计算 Star 增长 Top N | ✅ |
| 质量保护 | 快照重叠率/共同仓库数安全校验 | ✅ |
| 内容生成 | 基于 LLM 生成中文项目摘要 | ✅ |
| 报告输出 | 生成 HTML 报告（统计周期 + 项目卡片） | ✅ |
| 通知分发 | 按收件人批量发送邮件 | ✅ |
| 参数化配置 | 统一通过 `config.yaml` 管理运行参数 | ✅ |

---

## Pipeline

1. 调用 GitHub Search API 拉取候选仓库（多查询策略）
2. 合并并去重仓库结果，生成当日快照
3. 写入 SQLite（同日快照先删后插，确保数据新鲜）
4. 选取“最新快照 vs 上一快照”做增长差分
5. 调用 LLM 生成项目摘要
6. 渲染 HTML 报告并邮件发送

---

## Project Structure

```text
.
├─ main.py                  # 主流程编排（抓取 -> 快照 -> 分析 -> 报告 -> 发送）
├─ config.yaml              # 运行配置（API、查询参数、邮件、数据库等）
├─ utils/
│  ├─ fetcher.py            # GitHub 数据抓取与候选集合并
│  ├─ snapshot.py           # 快照存储、快照比较、增长计算
│  ├─ summarizer.py         # LLM 摘要生成
│  ├─ html_maker.py         # HTML 报告构建
│  └─ emailer.py            # 邮件发送
└─ output/                  # 本地导出的报告文件
```

---

## Roadmap (TODO)

### P0 - 运行可靠性

- [ ] 增加 CLI 参数：`--dry-run`、`--top-n`、`--date`
- [ ] GitHub API 增强重试/退避机制（429 / 5xx）
- [ ] 增加结构化日志（运行耗时、错误分级、关键指标）
- [ ] 增加基础测试：快照覆盖、增长计算、HTML 渲染

### P1 - 自动化与可运营

- [ ] 提供定时任务方案（Windows Task Scheduler / cron）
- [ ] 报告结果同时导出 JSON/CSV，便于二次分析
- [ ] 报告模板分级（简版 / 详细版）

### P2 - 分析深度

- [ ] 引入多周期趋势视图（连续多周，不止两期对比）
- [ ] 支持多语言报告（中文 / 英文）
- [ ] 增加主题维度标签（AI、Infra、Data、Agent 等）

---

## Notes

- 当前方案是“候选集驱动”的趋势追踪，不是全量 GitHub 精确排名。
- 优点是速度快、成本低、可持续运行，适合做周报级技术雷达。

