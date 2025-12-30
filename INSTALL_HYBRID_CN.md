# MCP Memory Service Hybrid 模式本地安装指南

> **📅 安装日期**: 2025-12-31
> **🎯 安装环境**: Windows 11 + Python 3.13 + Cloudflare D1 + Vectorize
> **✅ 安装状态**: 成功

---

## 目录

1. [前置要求](#前置要求)
2. [Cloudflare 配置](#cloudflare-配置)
3. [PyTorch 安装](#pytorch-安装)
4. [项目安装](#项目安装)
5. [Git 配置](#git-配置)
6. [验证安装](#验证安装)
7. [常见问题](#常见问题)

---

## 前置要求

### 系统要求
- **操作系统**: Windows 11
- **Python**: 3.10+ (本文使用 3.13.9)
- **Git**: 最新版本
- **Node.js**: 16+ (用于 Wrangler CLI)

### 必需工具
```bash
# 检查 Python 版本
python --version

# 检查 pip
pip --version

# 安装 Wrangler (用于创建 Vectorize 索引)
npm install -g wrangler
```

---

## Cloudflare 配置

### 1. 创建 D1 数据库

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Workers & Pages** → **D1**
3. 点击 **Create database**
4. 输入数据库名称: `mcp-memory-d1`
5. 点击 **Create**
6. **复制 Database ID**（格式：`xxxx-xxxx-xxxx-xxxx`）

### 2. 创建 Vectorize 索引

使用 Wrangler CLI 创建索引：

```bash
# 登录 Cloudflare
npx wrangler login

# 创建 Vectorize 索引
npx wrangler vectorize create mcp-memory-index --preset @cf/baai/bge-base-en-v1.5
```

索引名称：`mcp-memory-index`

### 3. 创建 API Token

1. 在 Dashboard 点击右上角头像 → **My Profile**
2. 左侧菜单选择 **API Tokens**
3. 点击 **Create Token** → **Create Custom Token**
4. 配置权限：

   **Account 账户权限**：
   - `Cloudflare D1` → `Edit` ✅
   - `Workers AI` → `Edit` ✅（Vectorize 归类在这里）
   - `Account Settings` → `Read` ✅

5. **Account Resources**：
   - 选择 **Include** → **Specific account**
   - 选择你的账户 ID

6. 点击 **Continue to summary** → **Create Token**
7. **复制 Token**（只显示一次！）

### 4. 获取 Account ID

你的账户 ID 在 Cloudflare Dashboard URL 中：
```
https://dash.cloudflare.com/{YOUR_ACCOUNT_ID}/...
```

例如：`7e6529ba606faa5fd30b39286e7385b2`

---

## PyTorch 安装

### ⚠️ 重要：PyTorch DLL 错误修复

**问题**：Python 3.13 + PyTorch 2.9.1 可能出现 DLL 初始化失败

**解决方案**：使用 PyTorch 2.6.0 CPU 版本

```bash
# 卸载现有 PyTorch
pip uninstall torch torchaudio torchvision -y

# 安装 PyTorch 2.6.0 CPU 版本
pip install "torch==2.6.0+cpu" --index-url https://download.pytorch.org/whl/cpu

# 验证安装
python -c "import torch; print(f'PyTorch {torch.__version__} loaded successfully')"
```

---

## 项目安装

### 1. 克隆或进入项目目录

```bash
cd C:\App\AIMCP\mcp-memory-service
```

### 2. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```env
# Cloudflare 配置
CLOUDFLARE_ACCOUNT_ID=7e6529ba606faa5fd30b39286e7385b2
CLOUDFLARE_API_TOKEN=你的API_Token
CLOUDFLARE_D1_DATABASE_ID=你的D1数据库ID
CLOUDFLARE_VECTORIZE_INDEX=mcp-memory-index

# 可选：启用 HTTP 服务器（Web Dashboard）
MCP_HTTP_ENABLED=true
```

**替换以下值**：
- `CLOUDFLARE_ACCOUNT_ID`: 你的账户 ID
- `CLOUDFLARE_API_TOKEN`: 步骤 3 创建的 Token
- `CLOUDFLARE_D1_DATABASE_ID`: 步骤 1 获取的 Database ID

### 3. 安装项目

```bash
# 使用 pip 安装（推荐）
pip install -e .
```

---

## Git 配置

### Fork 工作流设置

将本地仓库的远程地址改为你的 fork，并添加上游仓库：

```bash
# 1. 更新 origin 为你的 fork
git remote set-url origin https://github.com/HeJiaYue520/mcp-memory-service.git

# 2. 添加上游仓库（原始仓库）
git remote add upstream https://github.com/doobidoo/mcp-memory-service.git

# 3. 验证配置
git remote -v
```

预期输出：
```
origin    https://github.com/HeJiaYue520/mcp-memory-service.git (fetch)
origin    https://github.com/HeJiaYue520/mcp-memory-service.git (push)
upstream  https://github.com/doobidoo/mcp-memory-service.git (fetch)
upstream  https://github.com/doobidoo/mcp-memory-service.git (push)
```

### 同步上游更新

```bash
# 从上游仓库拉取最新更新
git fetch upstream

# 合并上游 main 分支到本地
git checkout main
git merge upstream/main

# 推送到你的 fork
git push origin main
```

---

## 验证安装

### 1. 测试服务器启动

```bash
memory server
```

预期输出：
```
WARNING:mcp_memory_service.dependency_check:First run detected, extending timeout to 60.0s
Server started successfully
```

### 2. 测试存储连接

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import requests
import os

account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
api_token = os.getenv('CLOUDFLARE_API_TOKEN')
d1_id = os.getenv('CLOUDFLARE_D1_DATABASE_ID')

url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{d1_id}'
headers = {'Authorization': f'Bearer {api_token}'}

response = requests.get(url, headers=headers)
print(f'D1 API Status: {response.status_code}')
print(f'Connected: {response.json()[\"success\"]}')
"
```

### 3. 启动 Web Dashboard（可选）

```bash
# 在 .env 中设置 MCP_HTTP_ENABLED=true
memory-server
```

访问：http://127.0.0.1:8000

---

## Claude Desktop 配置

编辑 `~/.claude.json` (Windows: `%USERPROFILE%\.claude.json`)：

```json
{
  "mcpServers": {
    "mcp-memory-service": {
      "command": "memory",
      "args": ["server"],
      "env": {
        "MCP_MEMORY_STORAGE_BACKEND": "hybrid",
        "CLOUDFLARE_ACCOUNT_ID": "你的账户ID",
        "CLOUDFLARE_API_TOKEN": "你的API_Token",
        "CLOUDFLARE_D1_DATABASE_ID": "你的D1数据库ID",
        "CLOUDFLARE_VECTORIZE_INDEX": "mcp-memory-index"
      }
    }
  }
}
```

---

## 常见问题

### Q1: PyTorch DLL 初始化失败

**错误**：`OSError: [WinError 1114] 动态链接库(DLL)初始化例程失败`

**解决方案**：
```bash
pip uninstall torch -y
pip install "torch==2.6.0+cpu" --index-url https://download.pytorch.org/whl/cpu
```

### Q2: Hybrid backend 安装失败

**错误**：`[ERROR] Failed to install hybrid storage backend`

**解决方案**：直接使用 pip 安装
```bash
pip install -e .
```

### Q3: Cloudflare API 认证失败

**检查**：
1. API Token 权限是否包含 `D1` 和 `Workers AI`
2. Account ID 是否正确
3. Token 是否过期

**测试**：
```bash
curl -H "Authorization: Bearer 你的Token" \
  https://api.cloudflare.com/client/v4/user/tokens/verify
```

### Q4: Vectorize 索引不存在

**解决方案**：确保使用 Wrangler 创建了索引
```bash
npx wrangler vectorize list
```

### Q5: Python 3.13 兼容性问题

**建议**：降级到 Python 3.11 或 3.12 获得最佳兼容性

```bash
# 使用 pyenv 或 conda 切换版本
pyenv install 3.11.9
pyenv local 3.11.9
```

---

## 配置文件总览

### .env 文件位置
```
C:\App\AIMCP\mcp-memory-service\.env
```

### Claude 配置文件位置
```
C:\Users\{你的用户名}\.claude.json
```

---

## 安装完成后的下一步

1. **重启 Claude Desktop**（如果配置了）
2. **测试存储功能**：
   ```
   /memory-store "测试记忆存储"
   /memory-recall "测试"
   ```
3. **查看 Web Dashboard**：http://127.0.0.1:8000
4. **阅读完整文档**：[CLAUDE.md](./CLAUDE.md)

---

## 参考资源

- [项目主页](https://github.com/doobidoo/mcp-memory-service)
- [Cloudflare D1 文档](https://developers.cloudflare.com/d1/)
- [Cloudflare Vectorize 文档](https://developers.cloudflare.com/vectorize/)
- [完整配置指南](./CLAUDE.md)

---

**🎉 安装完成后，你的 AI 助手将拥有跨会话的记忆能力！**
