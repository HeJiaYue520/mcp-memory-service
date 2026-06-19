# MCP Memory Service 凭证

## OAuth 客户端凭证

```
client_id: mcp_client_c2dvkH-OlVytWzZJBwZmhA
client_secret: Nks-J9e0NE8QqhTd4_aB1QQ6umhs1sm_yv8RRco-e9M
```

## 如何使用

### 方式 1：获取 Access Token（推荐）

```bash
curl -X POST http://127.0.0.1:8888/oauth/token \
  -u "mcp_client_c2dvkH-OlVytWzZJBwZmhA:Nks-J9e0NE8QqhTd4_aB1QQ6umhs1sm_yv8RRco-e9M" \
  -d "grant_type=client_credentials" \
  -d "scope=read write"
```

返回：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read write"
}
```

### 方式 2：直接用 API 调用

```bash
# 获取所有记忆
curl -H "Authorization: Bearer <access_token>" \
     http://127.0.0.1:8888/api/memories

# 添加新记忆
curl -X POST http://127.0.0.1:8888/api/memories \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "我的重要记忆"}'
```

## 重要说明

### 凭证有效期

| 项目 | 有效期 | 说明 |
|------|--------|------|
| client_id / client_secret | **永久** | 除非手动删除 |
| access_token | 1 小时 | 过期后重新获取 |

### 如果忘记了怎么办？

1. **client_secret 忘记**：无法找回，需要重新注册
2. **access_token 过期**：用上面的命令重新获取即可

### 安全建议

- ⚠️ 不要把这个文件上传到公开仓库
- ⚠️ client_secret 相当于密码，妥善保管
- ✅ 可以定期更换凭证（删除旧的，注册新的）

### 删除客户端

如果需要更换凭证：

```bash
# 查看 OAuth 存储（SQLite）
sqlite3 C:\App\AIMCP\mcp-memory-service\memory_http.db "SELECT * FROM oauth_clients;"
```

---

**生成时间**: 2025-12-31
**Dashboard 地址**: http://127.0.0.1:8888/
