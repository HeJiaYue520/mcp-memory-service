# MCP Memory Service 用户指南

> **📅 更新日期**: 2025-12-31
> **🎯 适用场景**: 多用户协作、记忆隔离、数据管理

---

## 目录

1. [核心概念](#核心概念)
2. [记忆是如何被捕获的](#记忆是如何被捕获的)
3. [如何在项目中使用](#如何在项目中使用)
4. [查看存储的数据](#查看存储的数据)
5. [多用户记忆隔离](#多用户记忆隔离)
6. [常见问题](#常见问题)

---

## 核心概念

### 什么是 MCP Memory Service？

MCP Memory Service 是一个**语义记忆服务**，它：
- ✅ 自动捕获你在项目中的重要决策和上下文
- ✅ 跨会话记住你的项目架构和代码模式
- ✅ 支持语义搜索，不用精确匹配关键词
- ✅ 多设备同步（Hybrid 模式）

### 数据存储在哪里？

**Hybrid 模式**（你当前使用的）：
- **本地**: SQLite-vec 数据库（快速访问，~5ms）
- **云端**: Cloudflare D1 + Vectorize（跨设备同步）

```
┌─────────────────┐     ┌─────────────────┐
│   本地 SQLite    │ ←→  │  Cloudflare D1  │
│   (快速访问)      │     │  (云端同步)      │
└─────────────────┘     └─────────────────┘
```

---

## 记忆是如何被捕获的

### ⚠️ 重要：不会记录所有内容！

**自动捕获规则**（Session-end Hooks）：

| 条件 | 说明 |
|------|------|
| **触发时机** | 会话结束时（`/exit` 或关闭终端） |
| **内容长度** | 至少 100 字符 |
| **置信度阈值** | > 0.1（避免存储无关对话） |
| **内容类型** | 技术决策、架构变更、bug 修复、配置更改 |

**会被捕获**：
```
✅ "我们决定使用 Hybrid 后端，因为它支持离线模式"
✅ "修复了 PyTorch 2.9.1 的 DLL 错误，降级到 2.6.0"
✅ "Cloudflare API Token 需要 D1 和 Workers AI 权限"
```

**不会被捕获**：
```
❌ "好的，谢谢"
❌ "明白了"
❌ "继续"
```

### 手动存储记忆

如果某些重要内容没有被自动捕获，你可以手动存储：

**在 Claude Desktop 中**：
```
/memory-store "重要决策：使用 PostgreSQL 而不是 MySQL，因为 JSON 支持" --tags "database,architecture"
```

**使用 API**：
```python
from mcp_memory_service import MemoryStorage

store_memory(
    content="项目配置基准：使用 Hybrid 后端",
    metadata={"tags": "configuration,hybrid-backend"}
)
```

---

## 如何在项目中使用

### 1. 确保服务正在运行

```bash
# 启动 MCP 服务器
memory server
```

### 2. 配置 Claude Desktop

编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "mcp-memory-service": {
      "command": "memory",
      "args": ["server"],
      "env": {
        "MCP_MEMORY_STORAGE_BACKEND": "hybrid",
        "CLOUDFLARE_ACCOUNT_ID": "你的ID",
        "CLOUDFLARE_API_TOKEN": "你的Token",
        "CLOUDFLARE_D1_DATABASE_ID": "你的D1 ID",
        "CLOUDFLARE_VECTORIZE_INDEX": "mcp-memory-index"
      }
    }
  }
}
```

### 3. 自动记忆检索

重启 Claude Desktop 后，记忆会**自动注入**到新会话中：

```
[系统检测到项目上下文]
上次会话决策：使用 Hybrid 后端
配置状态：Cloudflare D1 已连接
```

### 4. 手动搜索记忆

```
# 语义搜索
/memory-recall "Cloudflare 配置"

# 按标签搜索
/memory-recall "tags:configuration"

# 按时间搜索
/memory-recall "created:last-7days"
```

---

## 查看存储的数据

### 方法 1: Web Dashboard（推荐）

```bash
# 启动 Web Dashboard
export MCP_HTTP_ENABLED=true
memory-server
```

访问：**http://127.0.0.1:8000**

**功能**：
- 📊 查看所有记忆
- 🔍 语义搜索、标签搜索、时间筛选
- 📈 质量分析（v8.45.0+）
- 🗑️ 删除不需要的记忆

### 方法 2: Cloudflare D1 控制台

1. 访问：https://dash.cloudflare.com/7e6529ba606faa5fd30b39286e7385b2/workers/d1
2. 选择数据库：`mcp-memory-d1` 或 `my_team_data_mcp-memory-d1`
3. 点击 **Console**
4. 执行 SQL 查询：

```sql
-- 查看所有记忆
SELECT * FROM memories ORDER BY created_at DESC LIMIT 10;

-- 按标签搜索
SELECT m.content, t.name as tag
FROM memories m
JOIN memory_tags mt ON m.id = mt.memory_id
JOIN tags t ON mt.tag_id = t.id
WHERE t.name = 'configuration'
ORDER BY m.created_at DESC;

-- 查看记忆统计
SELECT
    COUNT(*) as total_memories,
    AVG(content_size) as avg_size,
    MAX(created_at) as latest_memory
FROM memories;
```

### 方法 3: API 查询

```bash
# 搜索记忆
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Cloudflare 配置"}'

# 按标签搜索
curl http://127.0.0.1:8000/api/search/by-tag?tag=configuration

# 按时间搜索
curl "http://127.0.0.1:8000/api/search/by-time?hours=24"
```

---

## 多用户记忆隔离

### ⚠️ 当前状态：默认无用户隔离

**数据库结构**（当前）：
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    content_hash TEXT UNIQUE,
    content TEXT,
    memory_type TEXT,
    created_at REAL,
    metadata_json TEXT,
    -- 注意：没有 user_id 字段！
);
```

这意味着：**所有用户共享同一个记忆库**。

### 如何实现用户隔离？

#### 方案 1: 使用标签隔离（推荐）

**给每个用户的记忆打标签**：

```bash
# 用户 A 存储
/memory-store "我的决策..." --tags "user:alice,project:x"

# 用户 B 存储
/memory-store "我的决策..." --tags "user:bob,project:x"
```

**查询时过滤**：
```python
# 只查询特定用户的记忆
search(
    query="架构决策",
    filters={"tags": ["user:alice"]}
)
```

#### 方案 2: 独立数据库（彻底隔离）

**为每个用户创建独立的 D1 数据库**：

| 用户 | D1 Database ID |
|------|----------------|
| Alice | `alice-memories-xxx` |
| Bob | `bob-memories-yyy` |

**配置不同 `.env` 文件**：

```bash
# Alice 的配置
export CLOUDFLARE_D1_DATABASE_ID=alice-memories-xxx

# Bob 的配置
export CLOUDFLARE_D1_DATABASE_ID=bob-memories-yyy
```

#### 方案 3: 修改数据库添加 user_id（高级）

需要修改数据库 schema：

```sql
ALTER TABLE memories ADD COLUMN user_id TEXT;
CREATE INDEX idx_memories_user_id ON memories(user_id);
```

然后配置环境变量：

```env
MCP_MEMORY_USER_ID=alice@company.com
```

**注意**：这需要修改代码，不推荐新手使用。

### 团队协作最佳实践

#### 场景 1: 小团队共享记忆

**配置**：所有成员使用同一个 D1 数据库

**隔离方法**：使用标签区分用户和项目

```bash
# 开发者 A
/memory-store "修复了登录 bug" --tags "user:alice,project:auth,bug-fix"

# 开发者 B
/memory-store "优化了数据库查询" --tags "user:bob,project:api,performance"
```

**查询**：
```bash
# 查看所有项目相关记忆（跨用户）
/memory-recall "project:auth"

# 只看我的记忆
/memory-recall "user:alice"
```

#### 场景 2: 大团队需要完全隔离

**推荐**：每个团队使用独立的 D1 数据库

```
团队 Alpha → mcp-alpha-d1
团队 Beta  → mcp-beta-d1
团队 Gamma → mcp-gamma-d1
```

**优点**：
- ✅ 完全隔离
- ✅ 性能更好（数据量小）
- ✅ 独立配额和计费

---

## 常见问题

### Q1: 如何知道哪些是我的记忆？

**方法 1：使用标签**
```bash
# 存储时添加用户标签
/memory-store "我的决策" --tags "user:alice"

# 查询时过滤
/memory-recall "user:alice"
```

**方法 2：查看 Web Dashboard**
- 访问 http://127.0.0.1:8000
- 使用标签过滤

**方法 3：Cloudflare D1 控制台**
```sql
-- 查看你存储的记忆（通过标签）
SELECT m.content, m.created_at
FROM memories m
JOIN memory_tags mt ON m.id = mt.memory_id
JOIN tags t ON mt.tag_id = t.id
WHERE t.name = 'user:alice'
ORDER BY m.created_at DESC;
```

### Q2: 别人会看到我的记忆吗？

**当前配置**：如果使用同一个 D1 数据库，**可以**看到。

**解决方案**：
1. 使用标签标记私有记忆：`user:alice,private`
2. 为敏感项目创建独立的 D1 数据库
3. 修改代码添加 user_id 字段（高级）

### Q3: 如何删除敏感记忆？

**方法 1：Web Dashboard**
```
访问 → 找到记忆 → 点击删除
```

**方法 2：API**
```bash
# 通过 content_hash 删除
curl -X DELETE http://127.0.0.1:8000/api/memories/{hash}
```

**方法 3：Cloudflare D1 控制台**
```sql
DELETE FROM memories
WHERE content LIKE '%敏感内容%';
```

### Q4: 记忆会占用多少空间？

**估算**：
- 每条记忆：~1-5 KB
- 1000 条记忆：~1-5 MB
- Cloudflare D1 免费额度：5 GB

**查询当前使用量**：
```sql
SELECT
    COUNT(*) as memory_count,
    SUM(content_size) as total_bytes,
    SUM(content_size) / 1024 / 1024 as total_mb
FROM memories;
```

### Q5: 如何导出记忆？

**方法 1：API 导出**
```bash
curl http://127.0.0.1:8000/api/memories/export > memories.json
```

**方法 2：Cloudflare D1 导出**
```sql
-- 导出为 JSON
SELECT json_object(
    'content', content,
    'tags', (SELECT GROUP_CONCAT(t.name) FROM tags t
             JOIN memory_tags mt ON t.id = mt.tag_id
             WHERE mt.memory_id = memories.id),
    'created_at', created_at_iso
) as memory_data
FROM memories;
```

---

## 推荐配置

### 个人开发者

```env
# 单用户，单项目
MCP_MEMORY_STORAGE_BACKEND=hybrid
CLOUDFLARE_D1_DATABASE_ID=your-database-id
```

**标签策略**：
- 项目名称：`project:mcp-memory-service`
- 内容类型：`architecture`, `configuration`, `bug-fix`

### 小团队（2-5人）

```env
# 共享数据库，标签隔离
MCP_MEMORY_STORAGE_BACKEND=hybrid
CLOUDFLARE_D1_DATABASE_ID=team-database-id
```

**标签策略**：
- 用户标识：`user:alice`, `user:bob`
- 项目标识：`project:frontend`, `project:backend`
- 内容类型：`decision`, `bug-fix`, `meeting`

### 大团队（10+人）

```env
# 每个团队独立数据库
MCP_MEMORY_STORAGE_BACKEND=hybrid
# 团队 Alpha
CLOUDFLARE_D1_DATABASE_ID=alpha-database-id
# 团队 Beta
CLOUDFLARE_D1_DATABASE_ID=beta-database-id
```

---

## 总结

| 功能 | 方法 |
|------|------|
| **存储记忆** | 自动（会话结束）或手动 `/memory-store` |
| **查看记忆** | Web Dashboard、D1 控制台、API |
| **搜索记忆** | `/memory-recall`、语义搜索、标签过滤 |
| **用户隔离** | 标签隔离（推荐）或独立数据库 |
| **删除记忆** | Web Dashboard、API、SQL |

**最佳实践**：
1. ✅ 使用标签组织记忆（用户、项目、类型）
2. ✅ 定期清理不需要的记忆
3. ✅ 敏感信息使用独立数据库或标签标记 `private`
4. ✅ 团队协作前制定标签规范

---

**🎉 现在你可以高效使用 MCP Memory Service 了！**
