# Timber-Data AI 助手 Harness 设计：意图识别 → 路由 → 扶正 → HITL 闸门

> 适用范围：对话式数据分析助手（圆木回收数据工作台）。
> 配套实现：`config/intent_schema.json`（意图预设）、`src/new/intent_recognizer.py`（识别引擎）、`src/new/chat_service.py`（路由接入）。

## 1. 为什么需要 harness

一个开放对话式 AI 助手如果不加约束，LLM 容易出现三类失控：

- **臆测取数**：没有真实数据时编造数字；
- **误触工具**：闲聊也被诱导去调用数据查询；
- **混淆事实与推测**：把外推/假设当成确定结论输出。

harness 的思路是：用**预设意图**作为第一道"扶正"开关，把开放的自然语言先收敛到可控的推理路径上，再让 LLM 在约束内发挥。意图不是写死在模型里，而是写在**可配置 schema** 中——加场景、调语气、加新意图都不用改代码。

## 2. 五阶段流水线

```
用户消息
  │
  ▼
[1] 意图识别      config/intent_schema.json + intent_recognizer.py
  │               本地字符 bigram 相似度 → (低分) LLM 兜底 → (仍低) 澄清
  ▼
[2] 意图路由      依据意图的 tool_policy / needs_data / system_constraint 决定
  │               暴露哪些工具、注入什么系统约束、是否直接澄清
  ▼
[3] 扶正推理      provider 在"被约束的 system + 裁剪后的工具集"下生成回答
  │               空库提示 / 推测强制标注 等红线在此生效
  ▼
[4] HITL 闸门     高影响意图先返回"待确认计划"，用户 approve 后才执行/导出
  ▼
[5] 渲染          前端展示回答 + 意图标签 + 工具使用痕迹
```

## 3. 阶段 1 — 意图识别（已实现）

- **配置驱动**：`config/intent_schema.json`，当前 13 个意图，可分场景增删改。
- **识别引擎**：`src/new/intent_recognizer.py`，**纯标准库**（无 numpy / sklearn / jieba）。
  - 主路：字符级 bigram + 余弦相似度，对每条意图的 `examples` + `keywords` 取最高分，毫秒级、零成本；
  - 兜底：低于 `local_threshold`(0.25) 时，复用已配置的 LLM 做 schema-prompted zero-shot 分类（要求返回 `{"intent","confidence"}`）；
  - 终裁：LLM 置信度仍低于 `global_confidence`(0.6) 则落入 `clarify_abstain`，由 harness 反问，绝不臆测。
- **验证**：`scripts/verify_intent.py` —— EXACT 13/13、PARAPHRASE 12/12。

## 4. 阶段 2 — 意图 → 推理路径路由（核心设计）

每条意图在 schema 中携带路由字段，harness 据此约束后续推理：

| 意图 | tool_policy | needs_data | 系统约束要点 | 低置信动作 |
|---|---|---|---|---|
| 专题分析 / 即时分析 / 取数 / 对比 / 趋势 / 异常归因 / 可视化 / 报表导出 / 数据推测 | `full` | 是 | "基于真实数据、禁止编造；推测须标注【推测/非实测】" | 澄清反问 |
| 总结 | `none` | 否 | "基于上下文归纳，不重新取数" | 澄清反问 |
| 闲聊 / 帮助引导 | `none` | 否 | "直连 LLM，不调用任何数据工具" | 澄清反问 |
| 澄清 / 拒答 | `none` | 否 | "不臆测意图去取数，友好反问" | 直接反问 |

三类路由语义：

- **`full`**：向 provider 暴露全部 grounding 工具（`get_dashboard_summary` 等 7 个），并强约束"只基于工具返回的真实数据"；
- **`none`**：传空工具集，**切断数据工具链**——闲聊/总结不会误触取数；
- **澄清**：识别置信度过低时直接返回 `clarification_prompt`，不浪费一次 LLM 作答（harness 扶正点）。

`chat_service.py` 已在 `chat()` 开头调用识别器，按 `tool_policy` 裁剪 `tools`、把 `system_constraint` 注入 system prompt、对 `needs_data` 且工作区为空时追加"请先上传"提示、低置信直接澄清返回，并在响应里带回 `intent` 字段。

## 5. 阶段 3 — 扶正推理（红线）

- **诚实红线**：`data_inference`（数据推测）的 `system_constraint` 强制在回答开头标注【推测 / 非实测】并说明假设前提，禁止把推测写成确定事实。
- **空库保护**：需要数据但工作区未上传时，提示先上传，避免无谓的工具调用与编造。
- **工具即边界**：模型只能调用白名单工具，拿不到原始 SQL / 文件系统，从机制上杜绝越权取数。

## 6. 阶段 4 — HITL 闸门（设计 + 当前状态）

部分意图的结论具有**高影响 / 不可逆 / 含假设**，不应由模型直接定稿，需人工确认：

| 意图 | 为何需闸门 | 闸门形式 |
|---|---|---|
| 异常归因 `anomaly_rootcause` | 归因结论易被误读为定论 | 先给"异常点 + 可能原因候选 + 待确认"，用户确认后才正式归因 |
| 报表导出 `reporting_export` | 导出物会离开对话、对外传播 | 先给"报告大纲 + 取数范围"，确认后再生成/导出 |
| 数据推测 `data_inference` | 含假设前提 | 先明示"假设 X 下推得 Y"，确认前提后再展开 |

**当前状态**：意图路由与系统约束已落地（阶段 1–3 可用）；显式 HITL 闸门（前端"确认/修改"交互）为下一步。建议前端在 `chat` 响应里读取 `intent` 字段，对上表意图渲染一个 confirm 卡片，用户 approve 后再触发实际取数/导出。

## 7. 边界与排查点

- **本地匹配依赖 keywords 覆盖**：强 paraphrase 若未命中，会走 LLM 兜底（需配置 API Key）；未配置 LLM 时安全降级为澄清，不臆测。
- **新增意图零代码**：在 `intent_schema.json` 加一条（含 `examples`/`keywords`/`tool_policy`/`system_constraint`），识别器自动加载。
- **识别质量调优**：调 `local_threshold`（本地采纳门槛）与 `global_confidence`（LLM 采纳门槛），或在意图下补充 `examples`/`keywords` 即可，无需动引擎。
- **迟滞风险**：`intent_recognizer` 为模块级单例懒加载，改 schema 后新进程生效（开发期重启后端即可）。

## 8. 后续增强路线

1. 多轮对话的意图保持与切换（当前每轮独立识别最新一条）；
2. 前端展示意图标签与置信度，提升可解释性；
3. HITL 闸门 confirm 卡片（阶段 4 落地）；
4. 识别结果埋点，用真实流量反哺 `examples`/`keywords`。
