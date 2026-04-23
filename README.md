# 图文回复评估平台

本项目是一个本地运行的图文回复质量评估平台。前端提供评估输入、图片预览、流程状态、节点详情、结构化结果和运行日志；后端通过 OpenRouter 调用 Gemma 4 31B 多模态模型，并以代码规则聚合输出“可用 / 瑕疵 / 不可用”。

## 技术栈

- 后端：FastAPI、Pydantic、httpx、Pillow、uv
- 前端：React、Vite、TypeScript、Tailwind CSS、React Flow、Zod、Lucide
- 模型服务：OpenRouter OpenAI-compatible Chat Completions

## 目录

```text
backend/   FastAPI 服务、评估 workflow、OpenRouter client、Prompt
frontend/  React 工作台、流程图、结果面板、样例加载
images/    题目内置样例图片，后端以 /sample-assets 暴露
model.txt  本地 OpenRouter 默认配置
```

## 后端启动

```powershell
cd "D:\AI\LLM  Evaluation Demo\backend"
uv sync --group dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

健康检查：

```text
http://localhost:8001/health
```

## 前端启动

推荐使用你已安装的 Bun 管理依赖：

```powershell
cd "D:\AI\LLM  Evaluation Demo\frontend"
$env:HTTP_PROXY="http://127.0.0.1:10811"
$env:HTTPS_PROXY="http://127.0.0.1:10811"
bun install
bun run dev
```

访问：

```text
http://localhost:5173
```

如果当前 shell 的 `node` 命令命中 WindowsApps 并出现 `Access is denied`，把 bundled Node 放到 PATH 前面：

```powershell
$env:PATH="C:\Users\18935\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;$env:PATH"
```

## 验证命令

后端：

```powershell
cd "D:\AI\LLM  Evaluation Demo"
uv run --project backend --group dev pytest backend/tests
```

前端可直接运行：

```powershell
cd "D:\AI\LLM  Evaluation Demo\frontend"
bun run test
bun run build
```

若 Bun 在当前环境无法 remap `node_modules/.bin`，可用 Node 入口验证：

```powershell
$env:PATH="C:\Users\18935\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;$env:PATH"
node .\node_modules\vitest\vitest.mjs run
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

## OpenRouter 配置

`model.txt` 当前格式会被后端自动解析：

```text
API:<OPENROUTER_API_KEY>
model="google/gemma-4-31b-it:free"
```

环境变量优先级更高，可覆盖 `model.txt`：

```env
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TEXT_MODEL=google/gemma-4-31b-it:free
OPENROUTER_VISION_MODEL=google/gemma-4-31b-it:free
OPENROUTER_TIMEOUT_SECONDS=120
OPENROUTER_MAX_RETRIES=2
```

## 常见问题

- `/api/evaluate` 返回图片格式错误：确认图片为 PNG/JPG/JPEG/WEBP，单张不超过 10MB。
- 前端无法加载样例图片：确认后端已启动，且 `images/` 目录存在。
- 模型调用失败：检查 `model.txt` 或环境变量中的 API Key、模型名、代理网络。
- 流式通道失败：前端会自动回退到同步接口，并在运行日志中记录切换原因。
