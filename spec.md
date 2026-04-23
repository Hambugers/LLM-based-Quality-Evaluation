可以。下面是 **更新后的完整 Spec** ，已经把你刚提的 5 个点并进去，适合直接丢给另一个 AI 生成项目。

---

# 项目 Spec：大模型图文回复评估平台

## 1. 项目目标

开发一个 **本地运行的图文回复评估平台** ，用于展示和运行“ **大模型图文回复质量自动评估 workflow** ”。

用户在前端页面输入：

* 用户问题
* 模型文本回复
* 一张或多张图片

系统调用接入的 LLM / MLLM，对这条图文回复进行自动评估，并输出：

* 预处理结果
* 文本评估结果
* 图片基础质检结果
* 图文一致性评估结果
* 聚合评分结果
* 最终标签
  * 可用
  * 瑕疵
  * 不可用

同时，前端需要可视化展示整条 workflow，并在运行过程中实时显示当前执行到哪个节点、每个节点的状态、每个节点的产出摘要。

该项目用于演示评估系统设计与工程落地能力，要求能稳定启动、可本地运行、具备较好的鲁棒性，并支持后续继续扩展。

---

## 2. 核心要求更新

### 2.1 前端文案约束

前端页面中**禁止出现**以下文案，或任何语义非常接近、显得像占位 demo 的文案：

* “本地 Python 服务 + 前端页面。适合做面试展示、流程演示、后续接真实模型服务”
* “填入题目的对话2示例”
* “demo”
* “mock 页面”
* “占位逻辑”
* “后续可接模型”
* “仅供演示”

页面整体要更像一个真正可用的评估平台。

建议标题与模块名风格为：

* 图文回复评估平台
* 评估输入
* 执行流程
* 评估结果
* 运行日志
* 节点状态
* 最终结论

---

### 2.2 模型接入要求

项目必须支持 **OpenRouter** 模型接入，直接通过 OpenRouter 调用大模型完成评测。

要求支持：

* 文本裁判模型调用
* 多模态裁判模型调用
* 可配置模型名
* 可配置 API Base URL
* 可配置 API Key
* 请求超时
* 重试
* 错误兜底
* 日志记录
* 返回结果结构化解析

环境变量至少支持：

```env
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TEXT_MODEL=
OPENROUTER_VISION_MODEL=
OPENROUTER_TIMEOUT_SECONDS=120
OPENROUTER_MAX_RETRIES=2
```

后端需要封装统一的 OpenRouter Client，不允许在业务逻辑里到处散落请求代码。

---

### 2.3 前端技术栈

前端允许并推荐使用：

* React
* Vite
* Tailwind CSS
* TypeScript

要求：

* UI 简洁专业
* 深色主题优先
* 布局清晰
* 支持状态动画
* 支持节点高亮
* 支持错误提示
* 支持图片预览
* 支持滚动查看长结果

不要使用过重的组件库。
可以少量使用轻量库，例如：

* reactflow 用于流程图
* zod 用于前端表单校验
* lucide-react 用于图标
* clsx / tailwind-merge 用于类名处理

---

### 2.4 流程图与运行状态展示

前端必须展示一张清晰的 **评估流程图** ，节点至少包括：

1. 输入接收
2. 预处理
3. 文本评估
4. 图片基础质检
5. 图文一致性评估
6. 结果聚合
7. 最终裁决

运行时必须能够展示：

* 当前正在执行哪个节点
* 已完成节点
* 失败节点
* 等待中的节点
* 每个节点的开始时间、结束时间、耗时
* 每个节点的输出摘要
* 若节点失败，显示错误原因

流程图展示要求：

* 节点状态颜色区分明显
* 当前执行节点高亮
* 支持查看节点详情
* 支持根据接口返回动态刷新状态

推荐做法：

* 后端返回每个节点的状态
* 前端用 ReactFlow 或自定义流程组件渲染
* 提交后先进入 running 状态
* 后端串行执行各节点并实时返回状态，或提供轮询接口

---

### 2.5 健壮性与鲁棒性要求

代码必须具备较强的工程性和抗造能力。

要求覆盖以下方面：

#### 输入健壮性

* 空输入校验
* 超长文本限制
* 图片格式校验
* 图片数量限制
* 图片大小限制
* 错误输入提示明确

#### 后端鲁棒性

* 请求超时控制
* OpenRouter 调用失败重试
* JSON 解析失败兜底
* 非结构化模型输出兜底
* 节点级异常隔离
* 单节点失败时整体流程仍能产出部分结果
* 日志清晰
* 错误信息可追踪

#### 前端鲁棒性

* 接口报错可见
* 节点失败状态可见
* 页面不因为单个字段为空直接崩溃
* 加载中状态明确
* 结果区对空字段有容错展示

#### 工程要求

* 类型定义清晰
* 模块边界明确
* 前后端字段统一
* 配置集中管理
* Prompt 集中管理
* 结果结构统一
* 不允许魔法字符串散落在各处
* 不允许所有逻辑堆在一个文件里

---

## 3. 运行方式

项目需要支持本地启动，前后端分离运行。

### 后端

* Python 3.11 或 3.12
* 使用 `uv` 管理依赖
* FastAPI + Uvicorn

### 前端

* Node.js 20+
* Vite 启动

### 启动方式示例

#### 后端

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问：

```text
http://localhost:5173
```

后端默认访问：

```text
http://localhost:8001
```

需要处理跨域。

---

## 4. 推荐项目目录结构

```text
llm_eval_platform/
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ schemas.py
│  │  ├─ prompts/
│  │  │  ├─ text_judge.py
│  │  │  ├─ vision_judge.py
│  │  │  └─ aggregator.py
│  │  ├─ services/
│  │  │  ├─ __init__.py
│  │  │  ├─ openrouter_client.py
│  │  │  ├─ evaluator.py
│  │  │  ├─ image_tools.py
│  │  │  └─ parser.py
│  │  └─ utils/
│  │     ├─ logging.py
│  │     ├─ ids.py
│  │     └─ time.py
│  ├─ uploads/
│  ├─ pyproject.toml
│  ├─ .env.example
│  ├─ README.md
│  └─ .gitignore
├─ frontend/
│  ├─ src/
│  │  ├─ app/
│  │  ├─ components/
│  │  │  ├─ Layout/
│  │  │  ├─ InputPanel/
│  │  │  ├─ Workflow/
│  │  │  ├─ ResultPanel/
│  │  │  └─ LogPanel/
│  │  ├─ hooks/
│  │  ├─ lib/
│  │  ├─ types/
│  │  ├─ pages/
│  │  ├─ styles/
│  │  ├─ main.tsx
│  │  └─ index.css
│  ├─ public/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ tailwind.config.ts
│  ├─ postcss.config.js
│  ├─ tsconfig.json
│  └─ .gitignore
└─ README.md
```

---

## 5. 页面设计要求

前端页面建议采用三栏或双栏布局。

### 左侧

评估输入区：

* 用户问题
* 模型文本回复
* 图片上传
* 图片预览
* OpenRouter 模型配置区
  * 文本裁判模型
  * 视觉裁判模型
* 提交评估按钮
* 清空按钮

### 中间

流程图与运行状态区：

* workflow 图
* 节点状态
* 当前执行高亮
* 每个节点耗时
* 每个节点输出摘要
* 失败节点错误原因

### 右侧

结果区：

* 预处理结果
* 文本评估结果
* 图片评估结果
* 图文一致性评估结果
* 聚合结果
* 最终标签
* 结构化 JSON 展开查看
* 运行日志

---

## 6. 前端交互要求

### 表单字段统一

前后端字段必须统一使用：

* `user_question`
* `model_answer`
* `images`

如果有模型配置字段，可以增加：

* `text_model`
* `vision_model`

### 提交方式

前端通过 `fetch` 或 `axios` 提交到：

```text
POST /api/evaluate
```

支持 `multipart/form-data`。

### 提交后的体验

点击评估后：

1. 表单禁用
2. 流程图进入运行态
3. 节点按顺序更新状态
4. 日志区追加运行事件
5. 完成后恢复表单可用状态

### 错误处理

任何错误都要在页面上明确显示：

* 表单校验错误
* 上传失败
* 后端异常
* OpenRouter 调用失败
* 模型返回结构异常

禁止只有浏览器 `alert`。

---

## 7. 后端接口要求

## 7.1 `GET /health`

返回：

```json
{"ok": true}
```

---

## 7.2 `POST /api/evaluate`

请求类型：

```text
multipart/form-data
```

字段：

* `user_question: str`
* `model_answer: str`
* `images: List[UploadFile] = []`
* `text_model: Optional[str]`
* `vision_model: Optional[str]`

返回结构需要包含完整的节点执行状态：

```json
{
  "ok": true,
  "run_id": "xxx",
  "workflow": {
    "status": "completed",
    "started_at": "",
    "ended_at": "",
    "duration_ms": 0,
    "nodes": [
      {
        "node_key": "preprocess",
        "node_name": "预处理",
        "status": "completed",
        "started_at": "",
        "ended_at": "",
        "duration_ms": 0,
        "summary": "已识别为强视觉依赖任务",
        "error": null,
        "output": {}
      }
    ]
  },
  "preprocess": {},
  "text_eval": {},
  "image_eval": {},
  "cross_modal_eval": {},
  "final_eval": {},
  "uploaded_images": [],
  "logs": [
    {
      "time": "",
      "level": "info",
      "message": "开始执行预处理节点"
    }
  ]
}
```

---

## 7.3 可选增强接口

如果希望前端更流畅展示运行过程，可以增加：

### `POST /api/evaluate/stream`

返回 SSE 流，逐步推送每个节点状态更新。

或者：

### `POST /api/evaluate`

先返回 `run_id`

### `GET /api/runs/{run_id}`

轮询获取状态

二选一即可。
如果实现难度可控，优先推荐  **SSE** 。

---

## 8. 评估 Workflow 设计要求

评估链路至少包含以下节点：

### 节点1：输入接收

负责表单解析、文件保存、基础字段校验。

### 节点2：预处理

识别任务类型、抽取关键实体、判断是否强视觉依赖任务。

### 节点3：文本评估

通过 OpenRouter 文本模型对文本进行裁判，输出结构化分数和证据。

### 节点4：图片基础质检

先做本地规则校验，包括：

* 格式
* 数量
* 大小
* 基础元信息
* 可选 OCR / hash / 分辨率检测

### 节点5：图文一致性评估

通过 OpenRouter 视觉模型进行图文联合评测，输出一致性、支撑度、误导风险。

### 节点6：聚合

综合多节点结果，计算总分、应用硬规则、给出最终标签。

### 节点7：最终裁决

输出最终标签、结论摘要、建议。

---

## 9. Prompt 设计要求

Prompt 必须集中管理，不允许散落在业务逻辑里。

至少包含：

* 文本裁判 prompt
* 多模态裁判 prompt
* 聚合裁判 prompt

每个 prompt 需要满足：

* 角色定义清晰
* 输出 JSON
* 字段固定
* 分数范围固定
* 要求给出证据
* 有失败兜底逻辑

建议让模型输出类似：

```json
{
  "score": 0.72,
  "label": "中等",
  "evidence": ["..."],
  "summary": "..."
}
```

后端需要对模型输出做结构化解析，解析失败时进入 fallback 逻辑。

---

## 10. OpenRouter Client 要求

封装单独的 `openrouter_client.py`，要求支持：

* 文本模型调用
* 多模态模型调用
* 统一 headers
* 超时控制
* 重试机制
* 错误分类
* 结构化日志
* 响应原文保留
* 解析结果与原始结果分离

支持的调用形式建议兼容 OpenAI-style chat completions。

多模态调用要支持：

* 纯文本消息
* 文本 + base64 图片
* 文本 + 图片 URL

---

## 11. 图片处理要求

上传图片后保存到本地 `uploads/`。
后端需要挂载 `/uploads` 静态路由，前端可直接回显图片。

允许格式：

* png
* jpg
* jpeg
* webp

限制建议：

* 单张不超过 10MB
* 最多上传 8 张

需要对非法格式返回明确错误。

---

## 12. 结果聚合规则

最终输出至少包含：

```json
{
  "hard_fail": false,
  "hard_fail_reason": "",
  "final_score": 0.67,
  "final_label": "瑕疵",
  "final_reason": "图文相关性一般，存在一定误导风险。"
}
```

标签规则：

* `final_score >= 0.75` => `可用`
* `0.45 <= final_score < 0.75` => `瑕疵`
* `< 0.45` => `不可用`

硬规则示例：

* 强视觉依赖任务中，高相关图片比例过低
* 图文一致性过低
* 误导风险过高
* 核心字段缺失
* 模型评测失败且无法兜底

---

## 13. 页面文案风格要求

整体文案要专业、克制、产品化。
避免任何“这是个练手项目”的感觉。

推荐文案方向：

* 图文回复评估平台
* 输入待评估内容
* 执行流程
* 节点状态
* 评估结果
* 最终结论
* 风险提示
* 结构化输出

不要出现任何“示例按钮写死为题目对话2”的文案。
如果要提供快捷填充能力，可用更通用的文案：

* 加载示例数据
* 使用预置样例

---

## 14. README 要求

README 需要说明：

* 项目用途
* 技术栈
* 目录结构
* 环境变量配置
* 后端启动方式
* 前端启动方式
* OpenRouter 配置说明
* 常见问题
* 错误排查方式

必须包含 `.env.example` 示例。

---

## 15. 验收标准

项目必须满足以下条件：

### 基础运行

* 后端可启动
* 前端可启动
* 前后端可联通
* 健康检查正常
* CORS 正常

### 页面功能

* 可输入文本
* 可上传图片
* 可预览图片
* 可发起评估
* 可看到流程图
* 可看到运行中状态
* 可看到节点结果
* 可看到最终结果

### 模型接入

* 能调用 OpenRouter
* 文本评估节点可运行
* 图文一致性节点可运行
* 请求失败时有明确报错
* 超时、重试、fallback 生效

### 稳定性

* 不应轻易出现 500
* 不应因字段名不一致导致 422
* 不应因单节点失败导致整页崩溃
* 错误可见、日志可见、状态可见

### 工程质量

* 代码结构清晰
* 模块划分合理
* 类型定义完整
* 配置集中
* Prompt 集中
* 有基本注释
* 有错误处理
* 有健壮性设计

---

## 16. 输出要求

请直接生成完整项目代码，包含前后端全部文件。
要求开箱可跑，字段统一，流程图可展示，支持 OpenRouter 调用，具备基本鲁棒性和良好错误处理。
不要只返回片段。
不要省略关键文件。
不要使用占位文案。
不要把所有逻辑写进一个文件。

---

## 17. 给生成 AI 的最终指令

请基于以上 spec，生成一个完整的前后端项目。

后端使用 FastAPI + uv。
前端使用 React + Vite + Tailwind CSS。
接入 OpenRouter 进行文本与多模态评测。
前端必须显示 workflow 流程图，并在执行时展示节点运行状态。
代码需要具有较好的健壮性、鲁棒性、错误处理能力与模块化结构。
页面文案要专业，不要出现“本地 Python 服务”“面试展示”“题目对话2示例”等字样。
请保证前后端字段一致，接口可用，运行后不会因为模板或字段不匹配而报错。

---

