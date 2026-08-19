# CodeVoyager 模块开发清单

> V1 核心目标：完成 **本地项目导入 → 项目分析 → 学习路线 → 源码学习 → AI 辅导 → 学习记录** 的完整闭环。

---

## Module 0：工程基础

### 主要工作

* 初始化 Git 仓库
* 建立项目目录结构
* Python 开发环境
* React + TypeScript 开发环境
* Electron 桌面端环境
* 环境变量管理
* 日志系统
* 基础异常处理
* `.gitignore`
* README
* 基础测试框架

### 项目结构

```text
CodeVoyager/
├── backend/
├── frontend/
├── agent/
├── tests/
├── docs/
└── scripts/
```

### 完成标准

能够启动桌面程序和 Python 服务，各模块具备继续开发的基础。

---

# Module 1：项目导入

## 功能

用户可以：

* 导入本地已有项目
* 查看已经导入的项目
* 删除项目

## 后端工作

* 获取仓库名称
* 获取本地路径
* Clone 失败处理
* 项目元数据保存

## 数据

保存：

```text
Project

    id
    name
    source_type
    local_path
```

---

# Module 2：项目文件扫描

## 功能

扫描整个项目，建立 CodeVoyager 自己的项目结构信息。

## 需要识别

* 文件
* 文件夹
* 文件类型
* 编程语言
* README
* 配置文件
* 依赖文件
* Dockerfile
* Compose 文件
* 测试目录
* 文档目录
* 源码目录

## 忽略

例如：

```text
.git
node_modules
.venv
__pycache__
dist
build
```

## 输出

生成：

```text
Project Tree
```

以及：

```text
项目文件数量
主要语言
目录结构
配置文件
依赖文件
```

---

# Module 3：代码静态分析

## 功能

进一步理解源码内部结构。

V1 优先支持 Python。

## 分析

* Class
* Function
* Method
* Import
* Module
* 继承关系
* 函数位置
* 类位置
* 函数参数
* Docstring

## 技术

V1：

```text
Python AST
```

后续：

```text
Tree-sitter
```

支持更多语言。

## 输出

例如：

```text
applications.py

FastAPI
├── __init__()
├── add_api_route()
├── get()
├── post()
└── include_router()
```

---

# Module 4：代码关系分析

## 功能

在 Module 3 基础上建立代码之间的关系。

## 分析

* 文件 → 文件
* Module → Module
* Class → Class
* Function → Function
* Import关系
* 调用关系
* 继承关系
* 引用关系

## 支持查询

例如：

```text
这个函数在哪里定义？

谁调用了这个函数？

这个类继承谁？

这个模块依赖什么？

这个文件被谁使用？
```

## 输出

形成基础：

```text
Code Graph
```

---

# Module 5：项目概要分析

## 功能

让 CodeVoyager 对整个项目建立宏观理解。

## 分析内容

* 项目用途
* 项目类型
* 技术栈
* 主要语言
* 依赖
* 核心模块
* 项目入口
* 配置系统
* 数据库
* API
* 测试方式
* 项目运行方式

## 输入来源

综合：

```text
README
+
目录结构
+
配置文件
+
依赖文件
+
代码静态分析
+
Git信息
```

## 输出

生成：

```text
Project Overview
```

作为后续 AI 学习路线的基础。

---

# Module 6：架构地图

## 功能

把项目结构转换成容易理解的视觉信息。

## 展示

### 项目目录图

```text
Project
├── API
├── Service
├── Database
└── Core
```

### 模块关系图

```text
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

### 代码关系

```text
Function A
 ↓
Function B
 ↓
Function C
```

## 用户可以

* 点击模块
* 查看对应文件
* 查看模块介绍
* 跳转源码
* 查看依赖关系

---

# Module 7：源码阅读器

## 功能

提供专门用于**学习源码**的阅读界面。

## 基础功能

* 文件树
* 打开源码
* 多文件切换
* 语法高亮
* 行号
* 搜索
* 跳转指定行
* 跳转函数
* 跳转类

## 技术

```text
Monaco Editor
```

## 布局

```text
项目目录 | 源码 | 学习 / AI 面板
```

## 与其他模块联动

可以从：

* 学习任务
* AI回答
* 架构图
* 搜索结果

直接跳到真实源码位置。

---

# Module 8：代码搜索

## 功能

提供项目级源码检索能力。

## Tools

```text
list_files

read_file

search_text

find_symbol

find_definition

find_references
```

## 用户可以搜索

```text
FastAPI

add_api_route

DATABASE_URL

@app.get
```

## Agent 也可以调用

例如：

```text
用户：
add_api_route 在哪里实现？

AI
 ↓
find_symbol
 ↓
获取真实代码
 ↓
回答
```

避免 AI 单纯依赖模型记忆回答源码问题。

---


# Module 9：Agent Core / Agent Runtime

## 目标

自己实现一个最小可用的 Coding Agent Runtime。

第一版不追求完整复刻 Codex / Claude Code，只学习并实现它们最核心的一小部分机制：

```text
用户目标
  ↓
LLM
  ↓
判断是否需要调用 Tool
  ↓
执行 Tool
  ↓
Tool Result 返回给 LLM
  ↓
继续判断
  ↓
最终回答
```

CodeVoyager 的 Agent 目标不是替用户把代码全部完成，而是：

```text
理解真实项目
↓
寻找与当前问题相关的信息
↓
调用工具读取真实源码
↓
结合用户当前学习任务
↓
给提示 / 解释 / 引导
↓
检查用户是否理解
```

## 第一版核心组件

```text
agent/
├── runtime.py
├── state.py
├── context.py
├── prompts.py
├── tool_registry.py
└── tools/
```

### runtime.py

Agent 主循环。

负责：

```text
接收用户消息
↓
构建上下文
↓
调用 LLM
↓
识别 Tool Call
↓
调用对应 Tool
↓
把 Tool Result 加回上下文
↓
再次调用 LLM
↓
直到得到最终回答
```

第一版必须设置最大循环次数，避免 Agent 无限调用工具。

---

### state.py

保存 Agent 当前运行状态。

第一版可以包含：

```text
current_project_id
current_chapter_id
current_task_id
conversation_messages
tool_call_count
```

状态只保存 Agent 当前需要的信息，不要一开始设计复杂状态机。

---

### context.py

负责构建送给 LLM 的上下文。

输入可以来自：

```text
当前用户问题
+
Project Overview
+
Project Tree
+
Code Structure
+
当前 Chapter
+
当前 Task
+
Tool Result
```

核心原则：

```text
不是把整个项目全部塞给 LLM
而是根据当前问题选择需要的信息
```

后续可以加入：

```text
Context Budget
Token Budget
上下文裁剪
相关文件选择
```

---

### prompts.py

保存 Agent 的系统提示词和教学策略。

例如：

```text
你是 CodeVoyager 的源码学习 Agent。

目标不是直接替用户完成所有代码，而是帮助用户理解真实项目。

回答源码问题时：
1. 优先基于真实项目数据。
2. 信息不足时调用 Tool。
3. 不要凭模型记忆猜测项目源码。
4. Guide 模式优先提示和引导。
5. Explain 模式可以直接解释。
6. Review 模式评价用户自己的理解。
```

---

### tool_registry.py

统一管理 Agent 可以调用的工具。

例如：

```text
Tool Registry

list_files
read_file
search_text
find_symbol
find_definition
find_references
get_project_structure
get_current_task
get_learning_progress
```

职责：

```text
工具注册
↓
向 LLM 描述工具
↓
接收 Tool Call
↓
找到真实 Python 函数
↓
执行
↓
返回 Tool Result
```

不要把每个 Tool 的执行逻辑全部写在 runtime.py。

---

### tools/

这里放 Agent 真正可以操作 CodeVoyager 的能力。

第一版优先复用已有代码搜索能力：

```text
tools/
├── files.py
├── search.py
├── symbols.py
└── learning.py
```

例如：

```text
files.py
- list_files()
- read_file()
- get_project_structure()

search.py
- search_text()

symbols.py
- find_symbol()
- find_definition()
- find_references()

learning.py
- get_current_task()
- get_learning_progress()
```

Tools 尽量调用 CodeVoyager 已有 Scanner、AST、Code Graph、Repository，而不是重复重新扫描项目。

---

## Agent Loop

第一版核心流程：

```text
用户：
ProjectRepository 是干嘛的？

↓ Agent Runtime

LLM：
我需要先找到 ProjectRepository

↓ Tool Call

find_symbol("ProjectRepository")

↓ Tool Result

backend/app/repositories/projects.py
line 10

↓ LLM

还需要读取真实源码

↓ Tool Call

read_file(
  "backend/app/repositories/projects.py"
)

↓ Tool Result

真实源码

↓ LLM

结合：
- 当前问题
- 当前学习任务
- 真实源码

↓
生成教学回答
```

---

## 与前面模块的关系

```text
Project Scanner
= 告诉 Agent 项目里有什么

Python AST
= 告诉 Agent 文件内部有什么 Symbol

Code Graph
= 告诉 Agent 代码之间有什么关系

Code Search
= 给 Agent 搜索真实项目的能力

Agent Core
= 决定下一步需要调用什么 Tool

AI Tutor
= Agent 面向用户表现出来的教学策略
```

Agent Core 不重新实现 Scanner、AST 和 Search，而是调用它们。

---

## V1 开发阶段

### Agent V0：普通 LLM 调用

理解：

```text
System Message
User Message
Assistant Message
```

完成最基础的模型调用。

### Agent V1：单 Tool

只实现：

```text
read_file()
```

让 LLM 可以主动请求读取文件。

### Agent V2：Tool Registry

支持多个工具统一注册和调用。

### Agent V3：Agent Loop

完成：

```text
LLM
↓
Tool Call
↓
Tool Result
↓
LLM
```

的循环。

### Agent V4：Agent State

加入当前：

```text
Project
Chapter
Task
Conversation
```

### Agent V5：Context Builder

根据当前问题动态选择项目上下文。

### Agent V6：Teaching Policy

加入：

```text
Guide
Explain
Review
```

三种教学模式。

---

## 第一版暂时不做

```text
多 Agent
Sub Agent
自动修改源码
自动提交 Git
自动执行高风险 Shell
复杂任务规划器
长期自主运行
复杂 Memory 系统
```

第一版重点是亲手理解并实现：

```text
LLM
+
Tool Calling
+
Agent Loop
+
Context
+
State
+
Teaching Policy
```

这构成 CodeVoyager 自己的最小 Agent Runtime。

---

# Module 10：学习路线生成

## 功能

根据项目自动生成学习顺序。

## 输入

```text
Project Overview
Code Structure
Architecture
README
Technology Stack
```

## 输出

```text
Learning Path

Chapter 1
项目整体认识

Chapter 2
启动流程

Chapter 3
核心模块 A

Chapter 4
核心模块 B

Chapter 5
核心调用链

Chapter 6
完整架构理解
```

## 每章包含

```text
title

goal

description

prerequisites

related_files

knowledge_points

tasks
```

## 要求

学习顺序应该从：

```text
宏观
 ↓
模块
 ↓
源码
 ↓
调用链
 ↓
整体理解
```

逐渐深入。

---

# Module 11：学习任务系统

## 功能

把每个 Chapter 转换成用户真正需要完成的任务。

## 任务类型

### 探索任务

```text
找到项目的程序入口。
```

### 搜索任务

```text
找到 FastAPI 类的定义。
```

### 阅读任务

```text
阅读 add_api_route。
```

### 理解任务

```text
解释这个函数负责什么。
```

### 调用链任务

```text
找到这个函数下一步调用的位置。
```

### 总结任务

```text
用自己的话总结路由注册流程。
```

### 实践任务

```text
运行项目并观察启动过程。
```

## 状态

```text
Not Started
In Progress
Completed
```

---

# Module 12：AI Tutor

## 功能

提供整个学习过程中的 AI 导师。

## AI 可以

* 解释代码
* 解释架构
* 回答问题
* 给提示
* 提出问题
* 检查用户理解
* 评价任务回答
* 推荐下一步
* 调用代码搜索工具

## 教学策略

默认：

```text
用户不会
 ↓
Hint 1
 ↓
Hint 2
 ↓
引导问题
 ↓
部分解释
 ↓
完整解释
```

而不是直接把答案扔给用户。

## 模式

### Guide

引导用户自己寻找答案。

### Explain

直接解释代码或概念。

### Review

评价用户自己的理解。

---

# Module 13：Agent Tools

## 功能

给 AI 提供操作 CodeVoyager 的能力。

## 第一版 Tools

```text
list_files()

read_file()

search_text()

find_symbol()

find_definition()

find_references()

get_project_structure()

get_current_task()

get_learning_progress()
```

## 后续

可以增加：

```text
git_history()

git_blame()

find_callers()

find_callees()
```

Agent 必须尽可能根据**真实项目数据**回答，而不是凭空回答。

---

# Module 14：学习进度

## 功能

记录用户学到了哪里。

## 保存

* 当前项目
* 当前 Chapter
* Chapter 状态
* 当前 Task
* Task 状态
* 完成时间
* 用户回答
* AI评价
* 整体进度

## 展示

例如：

```text
FastAPI

Overall Progress
████████████░░░░ 72%

✓ 项目结构
✓ 应用初始化
✓ 路由系统
→ 依赖注入
○ Middleware
○ Request Lifecycle
```

---

# Module 15：学习笔记

## 功能

用户可以在学习过程中记录自己的理解。

## 普通笔记

```text
FastAPI 的 Router 本质上负责……
```

## 源码笔记

绑定：

```text
文件
+
代码行
+
Symbol
```

例如：

```text
fastapi/routing.py
APIRoute

这里负责构造路由对象……
```

## 功能

* 创建
* 修改
* 删除
* 搜索
* 根据项目查看
* 根据源码位置查看

---

# Module 16：本地数据存储

## 技术

V1：

```text
SQLite
+
本地文件系统
```

## SQLite 保存

```text
Project

LearningPath

Chapter

Task

Progress

Note

AgentSession
```

## 文件系统保存

```text
Git Repository

Analysis Cache

Code Index

Temporary Files
```

## 数据目录

例如：

```text
~/.codevoyager/

├── projects/
├── database/
├── indexes/
├── cache/
└── config/
```

关闭 CodeVoyager 后学习记录仍然存在。

---

# Module 17：项目 Dashboard

## 首页

展示已经学习的项目：

```text
CodeVoyager

Continue Learning

FastAPI
72%
Routing System

Redis
31%
Event Loop

[ Import Repository ]
```

## 项目主页

展示：

* 项目简介
* 技术栈
* 学习进度
* 当前 Chapter
* 下一任务
* 项目结构
* 学习路线
* 最近笔记

---

# Module 18：设置系统

## 基础设置

* Workspace位置
* Git路径
* AI Provider
* API Key
* Model
* 语言
* Theme

## AI 设置

例如：

```text
Provider
OpenAI

Model
xxx

Teaching Style
Guided
```

API Key 不直接写进代码仓库。

---

# Module 19：缓存与空间管理

## 功能

显示每个学习项目占用的磁盘空间。

例如：

```text
FastAPI

Source          80 MB
Analysis        32 MB
Index           41 MB
Cache           17 MB

Total          170 MB
```

## 用户可以

* 清理 AI 缓存
* 清理分析缓存
* 重新建立索引
* 删除本地项目
* 查看 Workspace 总占用

---

# Module 20：错误与日志

## 功能

统一处理：

* Git Clone失败
* 网络错误
* LLM API错误
* 文件不存在
* 项目解析失败
* SQLite错误
* Agent Tool错误
* 前后端通信错误

## 日志

至少区分：

```text
INFO
WARNING
ERROR
```

方便开发阶段定位问题。

---

# Module 21：测试

## 单元测试

重点测试：

```text
文件扫描

语言识别

AST解析

Symbol查找

学习数据存储
```

## 集成测试

测试：

```text
导入仓库
 ↓
扫描
 ↓
分析
 ↓
生成学习路线
```

## 最终流程测试

完整模拟一个用户学习真实 GitHub 项目。

---

# V1 开发顺序

```text
01 工程基础
      ↓
02 项目导入
      ↓
03 项目文件扫描
      ↓
04 代码静态分析
      ↓
05 代码关系分析
      ↓
06 项目概要分析
      ↓
07 架构地图
      ↓
08 源码阅读器
      ↓
09 代码搜索
      ↓
10 Agent Core / Agent Runtime
      ↓
11 学习路线
      ↓
12 学习任务
      ↓
13 AI Tutor
      ↓
14 Agent Tools
      ↓
15 学习进度
      ↓
16 学习笔记
      ↓
17 本地存储
      ↓
18 Dashboard
      ↓
19 设置
      ↓
20 缓存管理
      ↓
21 错误处理与测试
```

# V1 暂时不开发

以下内容留给后续版本：

```text
注册 / 登录
云同步
社区
排行榜
团队空间
微服务
Kubernetes
故意制造 Bug
自动修 Bug
在线 Linux Sandbox
复杂多 Agent
商业付费
```

第一版最重要的不是模块数量，而是把下面这条链真正跑通：

```text
真实 GitHub 项目
        ↓
CodeVoyager 理解项目
        ↓
告诉用户怎么学
        ↓
让用户自己阅读和探索
        ↓
AI 在必要的时候提供帮助
        ↓
通过任务验证理解
        ↓
记录整个学习过程
```
