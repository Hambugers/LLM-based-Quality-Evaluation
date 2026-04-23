# 图文回复评估平台后端

## 启动

```powershell
uv sync --group dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 配置

后端按以下顺序读取 OpenRouter 配置：

1. 环境变量
2. 仓库根目录 `model.txt`
3. 缺失必填项时报错

核心变量见 `.env.example`。
