# 工作区总索引

> 记录本项目中所有开发者与 AI Agent 的工作记录。

---

## 概览

本目录用于追踪所有开发者在本项目中的 AI 协作记录。

### 目录结构

```text
workspace/
|-- index.md              # 当前文件，总索引
+-- {developer}/          # 每位开发者的独立目录
    |-- index.md          # 个人索引与会话历史
    |-- tasks/            # 任务文件
    |   |-- *.json        # 活跃任务
    |   +-- archive/      # 按月份归档的历史任务
    +-- journal-N.md      # 会话日志文件（顺序编号：1, 2, 3...）
```

---

## 当前开发者

| 开发者 | 最后活跃时间 | 会话数 | 当前文件 |
|--------|--------------|--------|----------|
| (none yet) | - | - | - |

---

## 使用说明

### 新开发者

运行初始化脚本：

```bash
python3 ./.trellis/scripts/init_developer.py <your-name>
```

执行后会：
1. 创建开发者身份文件（gitignore）
2. 创建个人进度目录
3. 创建个人索引
4. 创建初始日志文件

### 已初始化开发者

1. 获取当前开发者名称：
   ```bash
   python3 ./.trellis/scripts/get_developer.py
   ```

2. 阅读个人索引：
   ```bash
   cat .trellis/workspace/$(python3 ./.trellis/scripts/get_developer.py)/index.md
   ```

---

## 记录规范

### 日志文件规则

- 每个 journal 文件最多 `2000` 行
- 达到上限后新建 `journal-{N+1}.md`
- 创建新文件时同步更新个人 `index.md`

### 会话记录格式

每次会话至少应包含：

- 摘要：一句话说明本次工作
- 主要变更：本次修改了什么
- Git 提交：提交哈希与对应说明
- 后续：下一步要做什么

---

## 会话模板

记录会话时使用以下模板：

```markdown
## Session {N}: {标题}

**Date**: YYYY-MM-DD
**Task**: {task-name}

### 摘要

{一句话摘要}

### 主要变更

- {变更 1}
- {变更 2}

### Git 提交

| 哈希 | 说明 |
|------|------|
| `abc1234` | {commit message} |

### 验证

- [OK] {验证结果}

### 状态

[OK] **已完成** / # **进行中** / [P] **阻塞**

### 后续

- {后续 1}
- {后续 2}
```

---

**语言要求**：所有描述性文档统一使用中文。
