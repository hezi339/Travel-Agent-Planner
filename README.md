# AI旅行规划智能体 Travel-Agent-Planner

## 项目简介

基于自研 ReAct 推理架构的 AI 旅行规划智能体，不依赖 LangChain 封装好的 Agent，手动实现「思考 → 工具调用 → 观测反馈」完整闭环。

自动调用天气、地图第三方 API 获取真实数据，根据出行城市、天数、活动类型生成个性化行李清单、穿搭建议。

支持**命令行运行** + **Streamlit 网页可视化**双端交互，完整工程分层解耦，适配 AI 应用开发实习简历展示。

## 技术栈

- **语言 / 框架**：Python、LangChain、智谱 AI GLM-5.2、ReAct 自主推理
- **第三方 API**：和风天气、高德地图地理编码与景点检索
- **前端**：Streamlit
- **工程化**：环境变量密钥管理、接口缓存（lru_cache）、异常捕获、分层模块化、Git 规范

## 项目架构

```
Travel-Agent-Planner/
├── .env                 # 本地密钥（勿提交 Git）
├── .env.example         # 密钥模板
├── requirements.txt     # Python 依赖
├── web_demo.py          # Streamlit Web 入口
└── src/
    ├── llm_client.py    # LLM 统一封装
    ├── main_cli.py      # 命令行入口
    ├── agent/
    │   ├── agent_core.py  # ReAct 主循环
    │   └── parser.py      # 输出标签解析
    └── tools/
        ├── amap_api.py      # 高德地图
        ├── weather_api.py   # 天气查询
        ├── travel_tool.py   # 穿搭 / 行李工具
        └── tool_manager.py  # 工具统一调度
```

## 快速开始

### 1. 克隆并进入项目

```bash
cd Travel-Agent-Planner
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env   # Windows
# cp .env.example .env  # macOS / Linux
```

编辑 `.env`，填入：

| 变量 | 说明 |
|------|------|
| `ZHIPU_API_KEY` | [智谱开放平台](https://open.bigmodel.cn) 申请的 API Key |
| `QWEATHER_API_KEY` | [和风天气控制台](https://console.qweather.com) 申请的 API Key |
| `QWEATHER_API_HOST` | 和风控制台「设置」里的 API Host（新版账号必填） |
| `GAODE_KEY` | 高德 Web 服务 Key（景点搜索等扩展功能用） |

### 4. 运行

**Web 界面（推荐展示）：**

```bash
streamlit run web_demo.py
```

**命令行：**

```bash
python -m src.main_cli
```

## 环境变量说明

- `.env`：本地真实密钥，已在 `.gitignore` 中忽略
- `.env.example`：模板文件，可安全提交到 GitHub

## 注意事项

- 切勿将 `.env` 上传到 GitHub
- 若密钥曾泄露，请在智谱 / 高德控制台轮换 Key
- 运行命令时请在项目根目录 `Travel-Agent-Planner/` 下执行
