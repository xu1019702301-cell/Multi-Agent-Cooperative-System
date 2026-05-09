# 多智能体协同作业平台 - API 使用示例

本文档提供平台核心 API 的使用示例，帮助开发者快速上手。

## 基础信息

- Base URL: `http://localhost:8000/api/v1`
- 认证方式：Bearer Token（生产环境）
- 数据格式：JSON

---

## 1. 智能体管理

### 1.1 注册智能体

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "data-agent-001",
    "agent_name": "数据分析智能体",
    "agent_type": "data_analysis",
    "capabilities": ["data_processing", "statistical_analysis", "ml_inference"],
    "endpoint_url": "http://agent-service:9001",
    "auth_token": "agent-secret-token",
    "description": "负责数据处理和机器学习推理",
    "version": "1.0.0",
    "max_concurrent_tasks": 5
  }'
```

**响应示例：**
```json
{
  "id": 1,
  "agent_id": "data-agent-001",
  "agent_name": "数据分析智能体",
  "agent_type": "data_analysis",
  "capabilities": ["data_processing", "statistical_analysis", "ml_inference"],
  "status": "online",
  "current_load": 0.0,
  "success_rate": 100.0,
  "created_at": "2024-01-01T10:00:00Z"
}
```

### 1.2 查询可用智能体

```bash
curl "http://localhost:8000/api/v1/agents/available?required_capabilities=data_processing&max_load=50"
```

### 1.3 心跳上报

```bash
curl -X POST http://localhost:8000/api/v1/agents/data-agent-001/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "current_load": 35.5,
    "success_rate": 98.5,
    "avg_response_time": 120.5
  }'
```

---

## 2. 任务调度

### 2.1 创建任务

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "销售数据分析",
    "task_type": "data_analysis",
    "input_data": {
      "dataset": "sales_2024_q1.csv",
      "analysis_type": "trend_analysis"
    },
    "required_capabilities": ["data_processing", "statistical_analysis"],
    "priority": "high",
    "expected_output": {
      "format": "json",
      "include_charts": true
    }
  }'
```

**响应示例：**
```json
{
  "task_id": "task-550e8400-e29b-41d4-a716-446655440000",
  "task_name": "销售数据分析",
  "status": "pending",
  "priority": "high",
  "created_at": "2024-01-01T10:05:00Z"
}
```

### 2.2 创建带依赖的任务链

```bash
# 任务 1：数据清洗
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "数据清洗",
    "task_type": "data_preprocessing",
    "input_data": {"source": "raw_data.csv"},
    "required_capabilities": ["data_cleaning"]
  }'

# 任务 2：数据分析（依赖任务 1）
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "数据分析",
    "task_type": "data_analysis",
    "input_data": {},
    "required_capabilities": ["statistical_analysis"],
    "dependent_tasks": ["task-xxx-cleaning-id"]
  }'

# 任务 3：报告生成（依赖任务 2）
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "报告生成",
    "task_type": "report_generation",
    "input_data": {},
    "required_capabilities": ["document_generation"],
    "dependent_tasks": ["task-xxx-analysis-id"]
  }'
```

### 2.3 更新任务状态

```bash
curl -X PUT http://localhost:8000/api/v1/tasks/task-550e8400/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "executing",
    "progress": 45.0
  }'
```

### 2.4 查询任务统计

```bash
curl http://localhost:8000/api/v1/tasks/statistics
```

**响应示例：**
```json
{
  "total_tasks": 150,
  "status_distribution": {
    "pending": 10,
    "executing": 25,
    "completed": 110,
    "failed": 5
  },
  "avg_completion_time_seconds": 125.5,
  "success_rate": 95.5
}
```

---

## 3. 协同会话

### 3.1 创建协同会话

```bash
curl -X POST http://localhost:8000/api/v1/collaboration/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "智能制造协同任务",
    "participant_agents": [
      "vision-agent-001",
      "planning-agent-002",
      "control-agent-003"
    ],
    "initial_context": {
      "production_line": "line-A",
      "target_product": "widget-x",
      "quality_threshold": 0.99
    }
  }'
```

### 3.2 发送加密消息

```bash
curl -X POST http://localhost:8000/api/v1/collaboration/sessions/session-xxx/messages \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "vision-agent-001",
    "message_type": "data_sync",
    "payload": {
      "defect_detected": true,
      "defect_type": "surface_scratch",
      "confidence": 0.95,
      "location": {"x": 150, "y": 200}
    },
    "receiver_ids": ["planning-agent-002", "control-agent-003"]
  }'
```

### 3.3 更新共享上下文

```bash
curl -X PUT http://localhost:8000/api/v1/collaboration/sessions/session-xxx/context \
  -H "Content-Type: application/json" \
  -d '{
    "production_status": "paused",
    "reason": "quality_issue_detected",
    "action_required": "manual_inspection"
  }'
```

---

## 4. 监控指标

### 4.1 获取系统指标

```bash
curl http://localhost:8000/api/v1/monitoring/system
```

**响应示例：**
```json
{
  "cpu_usage_percent": 35.5,
  "memory_usage_percent": 52.3,
  "active_connections": 150,
  "request_rate_per_second": 250.0,
  "error_rate_percent": 0.1,
  "avg_response_time_ms": 45.5
}
```

### 4.2 获取仪表盘概览

```bash
curl http://localhost:8000/api/v1/monitoring/dashboard
```

### 4.3 查询日志

```bash
curl -X POST http://localhost:8000/api/v1/monitoring/logs/query \
  -H "Content-Type: application/json" \
  -d '{
    "level": "ERROR",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-01T23:59:59Z",
    "keyword": "task_failed",
    "limit": 100
  }'
```

---

## 5. 完整工作流示例

### 场景：多智能体协同完成数据分析报告

```bash
# Step 1: 注册三个专业智能体
# 1.1 数据采集智能体
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "collector-agent",
    "agent_name": "数据采集智能体",
    "agent_type": "data_collector",
    "capabilities": ["web_scraping", "api_integration"],
    "endpoint_url": "http://collector:9001",
    "auth_token": "token1"
  }'

# 1.2 数据分析智能体
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "analyzer-agent",
    "agent_name": "数据分析智能体",
    "agent_type": "data_analyst",
    "capabilities": ["statistical_analysis", "ml_inference"],
    "endpoint_url": "http://analyzer:9002",
    "auth_token": "token2"
  }'

# 1.3 报告生成智能体
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "reporter-agent",
    "agent_name": "报告生成智能体",
    "agent_type": "report_generator",
    "capabilities": ["document_generation", "visualization"],
    "endpoint_url": "http://reporter:9003",
    "auth_token": "token3"
  }'

# Step 2: 创建协同会话
curl -X POST http://localhost:8000/api/v1/collaboration/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "市场分析报告生成",
    "participant_agents": ["collector-agent", "analyzer-agent", "reporter-agent"],
    "initial_context": {"topic": "Q1 市场分析"}
  }'

# Step 3: 创建任务链
# 3.1 数据采集任务
TASK1=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "采集市场数据",
    "task_type": "data_collection",
    "input_data": {"sources": ["competitor_a", "competitor_b"]},
    "required_capabilities": ["web_scraping", "api_integration"]
  }' | jq -r '.task_id')

# 3.2 数据分析任务（依赖任务 1）
TASK2=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d "{
    \"task_name\": \"分析市场趋势\",
    \"task_type\": \"data_analysis\",
    \"input_data\": {},
    \"required_capabilities\": [\"statistical_analysis\"],
    \"dependent_tasks\": [\"$TASK1\"]
  }" | jq -r '.task_id')

# 3.3 报告生成任务（依赖任务 2）
TASK3=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d "{
    \"task_name\": \"生成分析报告\",
    \"task_type\": \"report_generation\",
    \"input_data\": {},
    \"required_capabilities\": [\"document_generation\"],
    \"dependent_tasks\": [\"$TASK2\"]
  }" | jq -r '.task_id')

# Step 4: 触发自动分配
curl -X POST http://localhost:8000/api/v1/tasks/auto-assign

# Step 5: 监控任务进度
curl http://localhost:8000/api/v1/tasks/$TASK3
```

---

## 错误处理

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "error": "invalid_request",
  "message": "请求参数验证失败",
  "detail": {
    "field": "agent_id",
    "error": "必须唯一"
  }
}
```

---

## 最佳实践

1. **批量操作**: 使用任务依赖功能创建任务链，避免手动编排
2. **负载均衡**: 定期调用心跳接口，确保调度器准确感知智能体负载
3. **错误恢复**: 监听任务状态，对 failed 状态的任务调用重试接口
4. **安全通信**: 敏感数据通过协同会话的加密通道传输
5. **性能监控**: 定期拉取监控指标，设置告警阈值
