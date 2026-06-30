# 多 Agent 电商助手

一个基于 FastAPI + LangGraph 规划边界的学生数码电商导购与交易辅助 Demo。当前 V1 使用确定性服务和工具层支撑 Agent 流程，避免由 Agent 编造价格、库存、优惠券或订单状态。

## V1 能力

- 商品导购和参数对比
- 优惠券可用性判断和最优优惠计算
- 订单创建、支付模拟、超时回滚
- Human-in-the-loop 高风险动作确认
- RAG MCP Server 接入边界和 KnowledgeQA 适配层
- Agent Trace 展示

## 启动

```bash
$env:UV_CACHE_DIR='D:\dev\EcomMutiAgent\.uv-cache'
uv run uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000
```

## 验收

```bash
$env:UV_CACHE_DIR='D:\dev\EcomMutiAgent\.uv-cache'
uv run pytest -v -p no:cacheprovider
```

手动演示脚本：

```text
我预算 4000，想买适合上课记笔记的平板，有没有优惠
帮我下单
确认
模拟支付超时
平板激活后还能七天无理由退货吗
这个订单能退款吗
```

## RAG 接入

默认接入配置：

```text
RAG_MCP_SERVER_PATH=D:\dev\MODULAR-RAG-MCP-SERVER
RAG_MCP_COLLECTION=ecommerce_qa
RAG_MCP_QUERY_TOOL=query_knowledge_hub
```

不要提交 RAG 项目的 API Key。