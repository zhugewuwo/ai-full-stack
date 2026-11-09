---
name: feature-link-test-writer
description: API 测试链撰写规范。在编写后端接口测试脚本、生成接口文档时激活，确保测试覆盖完整、文档自动生成。
metadata:
  model: manual
  last_modified: Tue, 13 May 2026 00:00:00 GMT

---

# Link Test Writer — API 测试链撰写规范

> Github 仓库持续维护: 纯 Markdown 文件可访问下面链接下载  
 [skills/feature/ffeature-link-test-writer/SKILL.md](https://github.com/toly1994328/skills/blob/master/feature/feature-link-test-writer/SKILL.md)


## 角色定位

你是一名 API 测试链编写者。基于已有的后端接口（design.md 或 routes.rs），为指定功能模块编写测试链 Python 脚本，脚本运行后自动测试所有接口并生成接口文档。

## 核心原则

- 一个功能模块 = 一个 Python 脚本（`{module}.py`）
- 脚本既是测试工具，也是文档生成器
- 每次运行自动生成最新的接口文档（含真实 token 和响应）
- 测试步骤按业务流程串联，形成有意义的"链"
- 错误场景（4xx）也是测试链的一部分
- 文档描述使用中文

## 目录结构

```
docs/features/{feature}/api/
├── {module}/
│   ├── request/
│   │   └── {module}.py          # Python 测试脚本
│   └── doc/
│       ├── 00_link.md           # 大纲表格，可跳转到各接口文档
│       ├── 01_{name}.md         # 接口文档（自动生成）
│       ├── 02_{name}.md
│       └── ...
├── {module2}/
│   ├── request/
│   │   └── {module2}.py
│   └── doc/
│       └── ...
└── ...
```

命名规则：
- `{feature}` = 功能域（如 im/group）
- `{module}` = 具体模块（如 group、conversation）
- `{name}` = 接口简称（如 create_group、search）
- 文档按执行顺序编号：`01_`、`02_`...
- `00_link.md` 固定为大纲
- 脚本生成的文档输出到同级的 `doc/` 目录

## 脚本结构

### 通用骨架

每个脚本包含三部分：

1. **Curl 处理器**：封装 curl.exe 调用，返回状态码、响应体、curl 命令字符串
2. **测试框架**：step/fail/ok/write_doc/write_link 等辅助函数
3. **测试步骤**：pre（前置登录）+ 编号步骤（1~N）

### Curl 处理器要求

- 使用 `subprocess` 调用 `curl.exe`（Windows 自带，避免 Python requests 依赖）
- `-s` 静默模式，`-w "\n%{http_code}"` 获取状态码
- 返回字典：`{"status": int, "body": str, "data": dict/list, "curl": str}`
- `curl` 字段是完整可复制的 curl 命令（带真实 token）
- 封装 get/post/delete 快捷方法

### 测试框架要求

```python
# ANSI 颜色
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def step(n, desc):    print(f"{CYAN}========== [{n}] {desc} =========={RESET}")  # 不加空行
def fail(msg):        print(f"{RED}[FAIL] {msg}{RESET}"); sys.exit(1)
def ok():             print(f"{GREEN}[PASS]{RESET}")
write_doc(...)        # 生成单个接口文档 md
write_link()          # 生成 00_link.md 大纲
```

### DOCS_DIR 规范

脚本放在 `{module}/request/` 下，文档输出到 `{module}/doc/`：

```python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "..", "doc")
os.makedirs(DOCS_DIR, exist_ok=True)
```

## 每个测试步骤的模式

```python
step(1, "POST /conversations - create private")
j = json.dumps({"peer_user_id": uid_b})
r = Curl.post(f"{BASE}/conversations", j, token_a)
if r["status"] != 200: fail(f"create failed: {r['status']}")
conv_id = r["data"]["id"]
print(f"conversation_id: {conv_id}")
ok()
write_doc("01_create_private.md", "POST", "/conversations",
    "创建私聊会话。", j, r["status"], r["body"], token_a,
    params_desc=[
        {"name": "peer_user_id", "type": "int", "required": "是", "desc": "对方用户 ID"},
    ])
```

## 接口文档格式

每个 `NN_{name}.md` 包含：

```markdown
# {METHOD} {path}

{一句话中文描述}

## Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| peer_user_id | int | 是 | 对方用户 ID |

```json
{请求体}
```

## Response `{status_code}`

```json
{实际响应}
```

## curl

```bash
{完整可执行的 curl 命令，带真实 token}
```

> {备注}（可选）
```

关键要求：
- 描述和备注使用中文
- 有请求参数时，先展示参数表格，再展示 JSON 请求体
- curl 必须是完整可执行的，带真实 token
- Response 是实际运行的真实响应
- 错误场景的响应如果为空，写 `(empty body)`

## 00_link.md 格式

```markdown
# {module} - API test link

Base URL: `{base_url}`

| # | Interface | Status | Result | Doc |
|---|-----------|--------|--------|-----|
| 1 | `POST /conversations` | `200` | PASS | [01_create_private.md](01_create_private.md) |
| 2 | ... | ... | ... | ... |
```

## 测试链设计原则

### 步骤编排

1. 前置步骤（pre）：获取 token 等认证依赖，不编号
2. 正常流程优先：先测 CRUD 的正常路径
3. 错误场景跟随：紧跟在对应正常步骤后面
4. 最终验证收尾：如删除后验证列表、对方视角验证

### 断言策略

- 成功响应：检查关键字段值
- 错误响应：只检查 HTTP 状态码（404、409、401 等）
- 前置条件：检查 token 非空、user_id 存在

### 前置依赖

如果模块需要认证，在 `pre` 步骤中：
1. POST /auth/login（type=password，credential=111111）获取 token
2. 如需特定会话，POST /conversations 幂等创建
3. 将 token、user_id、conversation_id 存入变量供后续步骤使用

## 参考模板

现有模板文件：
- Python: `docs/features/im/friend/api/friend/request/friend.py`
- Python: `docs/features/im/group/api/group/request/group.py`

编写新模块时，复制模板的 Curl 类和测试框架函数，只需替换测试步骤。

## 使用方式

用户触发：`/link-test-writer {module_name} {design.md路径或routes.rs路径}`

AI 执行：
1. 读取接口定义（design.md 或 routes.rs）
2. 设计测试链步骤（正常 + 错误场景）
3. 生成 `{module}.py`
4. 运行脚本验证全部通过
5. 确认文档正确生成