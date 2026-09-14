# Circular Timber Agent 完整项目总控方案

> 文档类型：项目定义 + 研究整理 + Agent 交互规范 + HTML Surface 产品规格 + 测试计划 + 作品集写作指南 + 校招能力证明清单  
> 当前版本：v1.0  
> 建立日期：2026-08-17  
> 原始项目：Circular Timber（2023）  
> 扩展项目：Circular Timber Agent-assisted Recovery Workflow（2026 AI 交互扩展）  
> 目标用途：大厂交互设计、AI 产品设计、用户体验设计、服务设计与产品策略校招作品集

---

## 0. 如何使用这份文档

这份文件是项目的唯一总控文档。后续无论由本人、Codex、其他 AI，还是协作者继续工作，都应先阅读本文件，再开始写作、设计或编码。

### 0.1 责任标签

- `【你】`：必须由本人提供事实、作出判断、联系参与者、确认设计立场或完成真实操作。AI 不得替代。
- `【AI】`：可以直接交给 AI 完成的机械性工作，例如整理、生成初稿、搭建代码、建立测试数据、检查一致性。
- `【共同加工】`：AI 可以先做初稿，但必须由本人审阅、修正、补充真实依据并最终确认。
- `【最终产出】`：该任务完成后必须留下的文件、页面、图表、界面或证据。
- `【验收标准】`：未达到这些条件，不得标记为完成。
- `【大厂能力】`：这一部分最终向招聘方证明的能力。
- `【禁止】`：不可虚构、不可越界或不可采用的做法。

### 0.2 状态标记

- `[ ]` 未开始
- `[-]` 进行中
- `[x]` 已完成并通过验收
- `[!]` 被阻塞，需要本人判断或外部信息

### 0.3 项目真相边界

本项目必须始终区分两个阶段：

1. **2023 原始项目**：热致变色色码、循环木材研究、利益相关者分析、关系数据库原型、材料生命周期流程。
2. **2026 AI 交互扩展**：Agent 工作流、HTML Surface、规则引擎、对话与主动机制、异常处理、数据治理、测试与迭代。

`【禁止】`

- 不得声称 Agent 是 2023 年原项目的一部分。
- 不得将演示规则写成真实法规。
- 不得将模拟数据写成真实行业数据。
- 不得声称系统可以认证木材安全、结构性能或化学成分。
- 不得虚构用户访谈、可用性测试或效率提升数字。
- 不得把 AI 生成的内容直接当作本人研究结论。
- 不得把普通聊天框包装成 Agent。

---

# 第一部分：项目总定义

## 1. 项目名称与一句话价值

### 1.1 推荐中文名

**Circular Timber｜循环木材追踪与 Agent 辅助回收决策系统**

### 1.2 推荐英文名

**Circular Timber: Agent-assisted Material Traceability and Recovery Decision Support**

### 1.3 一句话价值主张

> 原始设计通过色码与数据库让木材处理信息“看得见”；2026 年扩展进一步利用 Agent 将材料记录转化为可解释、可确认、可追溯的下一步行动。

### 1.4 核心转变

```text
2023：Colour cue → Material record → Human interpretation
2026：Colour / ID → Agent queries and validates → Candidate route → Human confirmation → Auditable update
```

### 1.5 项目类型

- 系统设计
- 可持续设计
- 信息架构
- Agent 交互设计
- 约束式生成 UI
- 数据治理
- 跨端体验
- HTML 高保真原型

`【共同加工】`

- [ ] 最终确认中英文项目名。
- [ ] 确认是否使用子产品名，例如 `TimberTrace Agent`。
- [ ] 将一句话价值主张调整为本人自然表达方式。

`【最终产出】`

- 项目名
- 中英文一句话价值主张
- 2023/2026 双时间标签
- 3 至 6 个项目能力标签

`【验收标准】`

- 面试官在 15 秒内能理解项目解决什么问题。
- 标题中没有夸大 AI 能力。
- 原项目与扩展项目时间清楚。

`【大厂能力】`

- 问题定义
- 产品定位
- 信息表达
- 项目边界管理

---

## 2. 目标用户与核心场景

### 2.1 第一目标用户

**拆除后木材回收站的材料分拣负责人**

### 2.2 用户任务

当一批回收木材进入分拣现场时，用户需要：

1. 确认材料身份。
2. 查询原始用途与处理历史。
3. 检查数据完整性。
4. 判断现场观察与数据库记录是否一致。
5. 确定下一步候选路径。
6. 在信息不足时创建人工检测任务。
7. 将结果写回材料记录。
8. 为下一角色生成可追溯的交接记录。

### 2.3 Jobs to Be Done

> 当拆除木材进入回收站时，我希望快速确认其身份、处理历史与记录完整性，从而决定下一步流程；当数据不足或相互冲突时，我希望系统明确告诉我缺少什么、应该找谁确认，而不是猜测一个安全结论。

### 2.4 次要角色

- 拆除人员：登记现场状态与来源。
- 供应商：创建或补充初始材料记录。
- 施工方：记录安装、用途与变更。
- 监管人员：查看审计链与未解决风险。
- 材料工程师或实验室：完成专业检测与结果确认。

`【你】`

- [ ] 确认第一目标用户是否符合原始项目逻辑。
- [ ] 用自己的语言描述分拣负责人的真实工作压力。
- [ ] 明确自己是否认识建筑、材料、回收或工程背景的人，可作为测试参与者。

`【AI】`

- [ ] 将目标用户信息整理为网页角色卡。
- [ ] 生成不带虚构姓名的岗位型画像初稿。
- [ ] 将 JTBD 转换为用户故事和任务列表。

`【共同加工】`

- [ ] 确认用户需求没有超出已有研究和合理推断。
- [ ] 删除过度生活化、无法证实的人物故事。

`【最终产出】`

- 1 张目标用户卡
- 1 条 JTBD
- 6 至 8 条核心任务
- 1 张主次角色关系图

`【验收标准】`

- 只有一个第一目标用户。
- 核心场景聚焦“拆除后分拣决策”。
- 不同时为六类角色开发完整产品。

`【大厂能力】`

- 用户中心设计
- 场景定义
- 需求优先级
- 产品范围控制

---

## 3. Agent 的定义

### 3.1 Agent 的工作目标

> 帮助用户完成材料信息查询、缺失与冲突识别、候选路径生成、人工检测任务创建、确认后写回和审计交接。

### 3.2 Agent 必须具备的六个条件

1. **目标**：完成材料分拣 Case，而不是回答孤立问题。
2. **状态**：知道当前用户、材料、生命周期阶段、任务和确认状态。
3. **工具**：查询数据库、检查字段、比较观察、查规则、建任务、写记录、导出报告。
4. **边界**：不能认证安全，不能替代工程师与实验室。
5. **行动**：能推动任务和记录发生变化。
6. **审计**：建议、确认和修改均可追溯。

### 3.3 Agent 可以做

- 查询和筛选材料记录。
- 检查必填字段。
- 识别现场观察与记录冲突。
- 查询演示规则库。
- 生成候选处理路径。
- 解释建议使用了哪些数据。
- 创建人工检测任务。
- 生成交接报告。
- 在人工确认后更新状态。
- 记录操作日志。

### 3.4 Agent 不可以做

- 仅凭照片或色码确定化学成分。
- 自动认证结构强度或安全性。
- 替代专业检测。
- 在低置信度下给出“安全复用”结论。
- 未经确认覆盖关键字段。
- 删除历史记录。
- 越权读取供应商、项目或人员敏感数据。

`【你】`

- [ ] 对“可以做/不可以做”逐条确认。
- [ ] 明确本人在面试中能解释哪些 Agent 工具。

`【AI】`

- [ ] 生成 Agent 能力矩阵。
- [ ] 将能力边界转换为 HTML 卡片组件。
- [ ] 检查每项功能是否有对应工具、状态和界面。

`【共同加工】`

- [ ] 判断每项 Agent 行动是否需要人工确认。
- [ ] 为高风险动作增加阻止、升级和撤销。

`【最终产出】`

- Agent 能力矩阵
- Agent 边界矩阵
- Agent 工具清单
- 人工确认规则

`【大厂能力】`

- AI 产品理解
- Agent 交互框架
- 风险意识
- 人机协同设计
- 复杂系统拆解

---

# 第二部分：大厂招聘能力映射

## 4. 项目如何证明大厂需要的能力

| 大厂能力要求 | 本项目中的证据 | 最终展示载体 | 面试时可讲的重点 |
|---|---|---|---|
| 用户研究与洞察 | 原材料研究、生命周期、利益相关者、任务测试 | Research Foundation | 如何从“木材浪费”重构为“信息在生命周期中丢失” |
| 体验设计流程 | 研究→定义→架构→原型→测试→迭代 | 完整案例研究 | 每一步如何影响下一步设计 |
| 交互设计 | 任务流、状态机、对话、确认、异常、撤销 | HTML Surface | 为什么不是一个聊天框 |
| AI/Agent 能力 | 工具调用、状态、主动性、边界、HITL | Agent Definition | Agent何时行动、何时停止、何时转人工 |
| 生成式 UI | 结构化输出驱动固定组件组合 | Decision Card | 如何在生成能力与安全约束之间平衡 |
| 主动推荐 | 触发、优先级、抑制、打断层级 | Trigger Matrix | 为什么某些提醒弹出、某些进入任务中心 |
| 数据分析与指标 | 任务完成率、时间、恢复率、覆盖率、信任度 | Test Dashboard | 如何定义和分析体验指标 |
| 设计规范 | 状态、组件、颜色、文本、权限、错误规范 | Code-native Design System | 如何沉淀可复用交互标准 |
| 跨端多场景 | 桌面工作台、平板/移动录入、监管视图 | Responsive Surface | 不同角色和终端如何分工 |
| 逻辑与系统思维 | 数据模型、生命周期、规则、审计链 | Architecture | 从物理材料到信息系统的映射 |
| 沟通与协调 | 多角色交接、人工检测任务、审计责任 | Service Blueprint | 不同利益相关者如何协作 |
| 动手实践 | React/TypeScript/HTML/CSS真实原型 | Live Demo/GitHub | 设计如何直接变成可运行界面 |
| 商业与产业理解 | 减少无效查找、重复确认与信息断裂 | Before/After | 不夸大结果，说明业务价值假设 |
| 安全与合规 | 权限、审计、最小化、人工确认 | Governance | 高风险AI为何必须可解释和可撤销 |

### 4.1 对腾讯交互设计岗位的直接对应

- **跨端多场景交互**：角色工作台、移动现场录入、监管审计视图。
- **AI 驱动交互范式**：任务型 Agent、结构化生成 UI、主动与抑制机制。
- **人机交互框架**：状态机、工具调用、确认、异常恢复、权限。
- **体验指标与数据分析**：任务效率、错误恢复、错误安全建议、控制感和信任度。
- **设计标准与规范**：代码原生组件、状态和规则文档。
- **AI 协同工作**：AI参与整理、编码、检查，但关键判断由本人负责。
- **逻辑、主动和沟通**：复杂多角色系统、任务升级、交接与审计。
- **动手实践**：不依赖静态Figma，直接构建可操作HTML Surface。

`【共同加工】`

- [ ] 在项目完成后，为每项能力补上真实页面链接或截图。
- [ ] 删除没有实际证据的能力标签。

`【最终产出】`

- 大厂能力映射表
- 面试证据索引
- 项目页面锚点与技能标签

`【验收标准】`

- 每一项简历能力都能指向具体界面或研究证据。
- 面试追问时能够打开对应页面演示。
- 不使用“熟悉”“精通”替代证据。

---

# 第三部分：最终交付物总表

## 5. 必须交付的八类成果

| 编号 | 交付物 | 形式 | 责任 | 完成标准 |
|---|---|---|---|---|
| D1 | 原项目研究档案 | 网页板块 + 图片 | 【共同加工】 | 研究、材料、利益相关者、数据库来源清晰 |
| D2 | 2026扩展定义 | 网页板块 | 【共同加工】 | 清楚解释为什么需要Agent |
| D3 | 数据与规则包 | TypeScript/JSON | 【AI】+【共同加工】 | 数据字段、演示规则、免责声明完整 |
| D4 | HTML Agent Surface | React/HTML/CSS | 【AI】+【共同加工】 | Happy Path + 3个异常路径可运行 |
| D5 | Code-native Design System | 组件与规范页面 | 【AI】+【共同加工】 | 组件、状态、颜色、文案、响应式有规则 |
| D6 | 用户测试资料 | 脚本、记录、指标、报告 | 【你】+【共同加工】 | 5–8人，数据真实，问题与迭代可追溯 |
| D7 | 完整案例研究页 | Portfolio Web Page | 【共同加工】 | 研究到迭代闭环，Live Demo可进入 |
| D8 | 校招材料包 | 简历文案 + 面试提纲 | 【共同加工】 | 每条描述都能被项目证据支持 |

### 5.1 可选交付物

- Demo 视频，60–90 秒。
- GitHub README。
- 可下载的 Case Report PDF。
- 导出的交接报告样例。
- 组件状态页面。
- 测试前后界面对比短视频。

---

# 第四部分：完整执行阶段

## 6. 阶段 0｜冻结范围与成功标准

### 目标

防止项目扩展成完整工业平台，确保能在作品集周期内完成。

### 工作项

`【你】`

- [ ] 确认目标是校招作品集，不是工业部署。
- [ ] 确认第一用户为回收分拣负责人。
- [ ] 确认核心场景为拆除后分拣。
- [ ] 确认不做真实安全认证。
- [ ] 确认预计可投入时间和截止日期。

`【AI】`

- [ ] 根据本文件生成项目看板。
- [ ] 为每个阶段建立文件和页面清单。
- [ ] 检查是否出现范围外功能。

`【共同加工】`

- [ ] 选择一个 Happy Path。
- [ ] 选择三个必须实现的异常路径。
- [ ] 决定是否做第二角色视图。

### 推荐范围

**Happy Path**：扫描正确ID→查到完整记录→生成候选路径→人工确认→写回→审计。

**异常路径A**：色码与数据库冲突→阻止复用→澄清→人工检测。

**异常路径B**：关键字段缺失→创建补录/检测任务。

**异常路径C**：数据库不可用→保持只读缓存→不允许修改。

`【最终产出】`

- Scope Statement
- Success Criteria
- Must/Should/Could/Won't 列表

`【验收标准】`

- Must功能不超过10项。
- 演示可在3分钟内完成。
- 不需要真实外部服务即可运行。

`【大厂能力】`

- 产品范围管理
- 优先级判断
- 项目推进

---

## 7. 阶段 1｜原项目材料审计

### 目标

识别哪些内容是原始证据，哪些内容需要重新整理，哪些内容不能继续使用。

### 需要准备的原始材料

- [ ] 2023课程项目说明。
- [ ] 研究笔记。
- [ ] 木材处理阶段图。
- [ ] 危险处理对照。
- [ ] 生命周期草图。
- [ ] 利益相关者图。
- [ ] 热致变色实验图片。
- [ ] 色码方案。
- [ ] Excel数据库截图或源文件。
- [ ] App/Website/Cloud Database概念图。
- [ ] 最终系统流程图。
- [ ] 教师或同伴反馈。
- [ ] 原始项目反思。

`【你】`

- [ ] 判断每个材料是否真实属于2023原项目。
- [ ] 说明当时本人实际完成了什么。
- [ ] 标记无法证明来源的内容。
- [ ] 写下原项目最明显的三个局限。

`【AI】`

- [ ] 读取现有项目文件和图像。
- [ ] 生成资产目录：文件名、内容、用途、证据等级。
- [ ] 检查图片重复、低清、文字错误和命名混乱。
- [ ] 建议每个素材应放在哪个案例板块。

`【共同加工】`

- [ ] 将素材分成Research、System、Prototype、Feedback、Archive。
- [ ] 为每张最终使用的图片写准确caption。

`【最终产出】`

- `CIRCULAR_TIMBER_SOURCE_MAP.md`
- 资产清单
- 证据等级表
- 原项目局限清单

`【验收标准】`

- 所有网页图片都能追溯到原始文件。
- 2023与2026素材不会混淆。
- 不使用无法解释的图片。

`【大厂能力】`

- 研究整理
- 信息架构
- 证据意识
- 项目复盘

---

## 8. 阶段 2｜研究综合与问题重构

### 目标

把“木材回收污染”重构为“材料信息无法跨生命周期存续”的系统问题。

### 核心研究问题

1. 哪些材料信息必须伴随木材移动？
2. 哪些处理方式会改变后续路径？
3. 信息在哪些交接点最容易丢失？
4. 回收人员需要哪些信息才能继续行动？
5. 哪些决定必须交给专业人员？

`【你】`

- [ ] 回看原研究，确认研究结论仍然准确。
- [ ] 标记哪些是事实、哪些是当时的设计推断。
- [ ] 补充本人对原方案局限的真实反思。

`【AI】`

- [ ] 将原始材料整理成“Evidence→Insight→Decision”。
- [ ] 生成研究摘要初稿。
- [ ] 从研究中提取数据库字段与交接点。

`【共同加工】`

- [ ] 将AI摘要与原材料逐条核对。
- [ ] 删除超出证据的强结论。
- [ ] 确认Agent机会点来自真实问题，而不是为了使用AI。

### 推荐研究综合表

| 证据 | 洞察 | 设计决定 | 证据等级 |
|---|---|---|---|
| 不同处理方式需要不同后续流程 | 不能仅凭外观判断 | 详细记录进入数据库 | 原研究 |
| 混合废物流难快速分拣 | 现场需要第一层提示 | 色码作为初筛信号 | 原研究+设计推断 |
| 数据在角色交接中丢失 | 材料身份必须长期绑定 | ID与生命周期事件 | 系统推断 |
| 用户仍需跨表查询并自行解释 | 被动数据库不能推动任务 | Agent作为行动层 | 2026扩展假设 |

`【最终产出】`

- Research Foundation网页板块
- 4至6条研究洞察
- Evidence→Insight→Decision表
- 原方案局限与Agent机会点

`【验收标准】`

- 每条洞察有来源。
- Agent机会明确解决被动查询和任务协调问题。
- 不以“AI很流行”作为动机。

`【大厂能力】`

- 研究到设计转化
- 问题本质提炼
- 逻辑推演

---

## 9. 阶段 3｜利益相关者与服务蓝图

### 目标

解释信息由谁创建、读取、修改和确认，以及Agent在哪一段介入。

`【AI】`

- [ ] 基于现有stakeholder列表生成生命周期信息流初稿。
- [ ] 生成Service Blueprint表格。
- [ ] 标出每个角色的读写权限草案。

`【你】`

- [ ] 判断角色关系是否符合原项目。
- [ ] 删除没有必要的角色。
- [ ] 确认专业检测和监管职责不能由Agent替代。

`【共同加工】`

- [ ] 确认每个生命周期阶段的数据输入与输出。
- [ ] 确认每个高风险动作的最终责任人。

### Service Blueprint必须包含

- 用户动作
- 前台界面
- Agent动作
- 数据库工具
- 后台角色
- 风险点
- 人工确认
- 审计记录

`【最终产出】`

- Stakeholder Map v2
- Lifecycle Information Flow
- Service Blueprint
- Role Permission Matrix

`【验收标准】`

- 每次数据库写入都有责任人。
- Agent不会成为最终安全责任人。
- 主用户流程不会被次要角色拖复杂。

`【大厂能力】`

- 服务设计
- 跨角色协作
- 复杂系统架构

---

## 10. 阶段 4｜用户旅程与任务流

### Before Journey

1. 接收材料。
2. 人工看色码或标签。
3. 打开Excel或记录系统。
4. 搜索材料ID。
5. 自己判断字段是否完整。
6. 自己解释处理方式。
7. 电话或消息联系其他人员。
8. 手工创建检测记录。
9. 手工更新材料状态。

### Agent Journey

1. 扫描或输入ID。
2. Agent查询材料记录。
3. 检查必填字段。
4. 比较现场观察与数据库。
5. 根据演示规则生成候选路径。
6. 信息不足时澄清或升级。
7. 用户确认下一步。
8. Agent创建任务或更新状态。
9. 自动生成审计与交接记录。

`【AI】`

- [ ] 生成Before/After旅程图。
- [ ] 生成Happy Path任务流。
- [ ] 生成三个异常任务流。
- [ ] 检查每一步是否有进入条件和退出条件。

`【你】`

- [ ] 确认所有流程都能在面试时解释。
- [ ] 判断哪些步骤应由用户主动，哪些可由Agent主动。

`【共同加工】`

- [ ] 将抽象步骤转成具体界面状态。
- [ ] 删除只为展示技术而增加的步骤。

`【最终产出】`

- Before/After Journey
- Happy Path Flow
- Error Flow A/B/C
- 用户任务优先级

`【大厂能力】`

- 用户旅程
- 任务流
- 跨场景交互
- 复杂流程简化

---

## 11. 阶段 5｜数据库与信息架构

### 数据表

#### Materials

- `materialId`
- `species`
- `description`
- `originalPurpose`
- `hazardClass`
- `durabilityClass`
- `strengthClass`
- `preservative`
- `preservativeId`
- `expectedColour`
- `supplier`
- `currentStage`
- `recordStatus`
- `lastVerifiedAt`

#### LifecycleEvents

- `eventId`
- `materialId`
- `stage`
- `actorRole`
- `organisation`
- `location`
- `action`
- `timestamp`
- `notes`

#### Observations

- `observationId`
- `materialId`
- `observedColour`
- `surfaceCondition`
- `damageLevel`
- `photo`
- `enteredBy`
- `timestamp`

#### Rules

- `ruleId`
- `conditionField`
- `operator`
- `expectedValue`
- `riskLevel`
- `recommendationType`
- `requiredAction`
- `requiresConfirmation`
- `sourceNote`
- `isDemoRule`

#### AgentCases

- `caseId`
- `materialId`
- `status`
- `detectedIssues`
- `recommendation`
- `confidenceBand`
- `requiredActions`
- `userDecision`

#### AuditEvents

- `auditId`
- `caseId`
- `actor`
- `action`
- `beforeValue`
- `afterValue`
- `timestamp`
- `reason`

`【AI】`

- [ ] 将原Excel字段映射到TypeScript类型。
- [ ] 创建5至8条演示材料。
- [ ] 创建完整、缺失、冲突、高风险四类测试Fixture。
- [ ] 为所有模拟字段增加`demo`说明。
- [ ] 编写数据校验函数。

`【你】`

- [ ] 检查字段是否来自原项目或合理扩展。
- [ ] 确认演示数据没有被误写成真实行业数据。

`【共同加工】`

- [ ] 确认哪些字段是关键字段。
- [ ] 确认哪些字段缺失时必须停止推荐。
- [ ] 确认每个字段的来源、修改权限和更新时间。

`【最终产出】`

- `materials.ts`
- `lifecycleEvents.ts`
- `rules.ts`
- `demoScenarios.ts`
- Data Dictionary网页板块

`【验收标准】`

- 所有界面内容都从结构化数据读取。
- 不把空值伪装成已知信息。
- 每条演示规则有`sourceNote`或明确标为Demo。

`【大厂能力】`

- 信息架构
- 数据意识
- 产品技术协作
- 可追溯性设计

---

## 12. 阶段 6｜Agent工具、状态和决策协议

### 工具函数

```text
getMaterialById
searchMaterials
checkRequiredFields
compareObservationWithRecord
lookupHandlingRules
generateCandidateRoute
createInspectionTask
updateMaterialStatus
exportHandoffReport
appendAuditEvent
```

### 状态机

```text
idle
→ identifying
→ retrieving
→ analysing
→ needs_clarification
→ generating_recommendation
→ awaiting_confirmation
→ creating_task
→ updating_record
→ completed
→ failed
```

### 决策输出协议

```ts
type AgentDecision = {
  status:
    | "reuse_candidate"
    | "requires_test"
    | "requires_treatment"
    | "special_handling"
    | "insufficient_data";
  confidence: "high" | "medium" | "low";
  evidence: string[];
  conflicts: string[];
  missingFields: string[];
  recommendedActions: string[];
  requiresHumanConfirmation: boolean;
  allowedActions: string[];
};
```

`【AI】`

- [ ] 编写TypeScript类型。
- [ ] 编写工具函数。
- [ ] 编写确定性decision engine。
- [ ] 为每个状态生成UI映射。
- [ ] 为核心规则写单元测试。

`【你】`

- [ ] 能够用非技术语言解释每个工具。
- [ ] 确认状态名称和用户体验一致。

`【共同加工】`

- [ ] 确认Agent不会显示内部思维链。
- [ ] 只展示证据、规则、调用工具与操作结果。
- [ ] 确认所有写入动作需要确认。

`【最终产出】`

- Agent State Diagram
- Tool Contract
- Decision Schema
- Rule Engine
- Unit Tests

`【验收标准】`

- 相同输入产生稳定结果。
- 决策可以被解释和复现。
- 断网时核心Demo仍能工作。

`【大厂能力】`

- Agent框架
- 状态设计
- 产品与工程协作
- 可解释AI

---

## 13. 阶段 7｜对话、主动触发与抑制

### 必须准备的对话

1. 正常查询与确认。
2. 色码冲突澄清。
3. 关键字段缺失。
4. 创建人工检查任务。
5. 用户否决Agent建议。
6. 用户撤销数据库修改。

### 触发矩阵

| 信号 | Agent行为 | 打断等级 | 人工确认 |
|---|---|---|---|
| 普通字段缺失 | 角标提示 | 0 | 否 |
| 关键字段缺失 | 展开任务卡 | 1 | 是 |
| 色码与记录冲突 | 阻止提交并澄清 | 2 | 是 |
| 高风险类别 | 警告并升级 | 3 | 是 |
| 记录过期 | 建议重新验证 | 1 | 是 |
| 混合批次 | 建议拆分批次 | 2 | 是 |
| 未确认材料准备复用 | 阻止操作 | 3 | 是 |

### 抑制规则

- 用户正在编辑时不重复提醒。
- 已确认提示不重复出现。
- 非紧急信息进入任务中心。
- 同一Case只保留一个主行动。
- 连续建议有打扰预算。
- 高风险问题不能静默跳过。

`【AI】`

- [ ] 根据状态和工具生成对话初稿。
- [ ] 编写触发和抑制逻辑。
- [ ] 生成对话UI状态。

`【你】`

- [ ] 朗读所有对话，删除机械或过度AI化语言。
- [ ] 确认用户始终知道下一步。

`【共同加工】`

- [ ] 检查主动提醒是否有真实触发证据。
- [ ] 检查高风险提示是否明确但不过度恐吓。

`【最终产出】`

- Conversation Map
- Trigger Matrix
- Suppression Rules
- Interruption Levels

`【验收标准】`

- 对话不是问一句答一句。
- 至少有一次澄清、一次升级、一次撤销。
- 主动行为都有触发和停止条件。

`【大厂能力】`

- 对话式交互
- 主动式Agent
- 打扰控制
- 用户控制感

---

## 14. 阶段 8｜约束式生成UI与设计规范

### 生成UI原则

1. Agent只输出结构化决策对象。
2. 前端从固定组件库组合界面。
3. 一个界面只有一个主行动。
4. 低置信度必须显示不确定性。
5. 高风险信息必须显示证据和确认。
6. 不允许仅凭颜色表达状态。
7. 所有生成结果支持撤销或转人工。

### 组件库

- MaterialIdentityCard
- StatusBadge
- EvidenceList
- ConflictAlert
- MissingDataCard
- CandidateRouteCard
- ConfirmationBar
- InspectionTaskCard
- SourceTimestamp
- AuditPreview
- EmptyState
- OfflineState
- PermissionState

### 设计Token

- Timber Brown：材料身份
- Forest Green：可继续的候选路径
- Amber：需要确认
- Brick Red：高风险或阻止
- Slate：数据库、日志、系统信息
- Warm Off-white：背景

### 无障碍

- 颜色必须配合文字、图标和形状。
- 状态有可读标签。
- 键盘可操作。
- 焦点状态清楚。
- 错误信息与字段关联。
- 动效支持减少动态偏好。
- 对比度满足WCAG基本要求。

`【AI】`

- [ ] 在HTML/CSS中建立设计Token。
- [ ] 创建所有组件和状态。
- [ ] 创建组件展示页。
- [ ] 运行可访问性检查。

`【你】`

- [ ] 确认视觉语言符合Circular Timber，而不是通用AI蓝色界面。
- [ ] 确认风险颜色和文案不会引起误解。

`【共同加工】`

- [ ] 逐个检查组件的Normal/Loading/Empty/Error/Disabled状态。
- [ ] 确认桌面、平板、手机布局。

`【最终产出】`

- Code-native Design System
- Component State Gallery
- Generative UI Rules
- Responsive Spec
- Accessibility Checklist

`【验收标准】`

- 不依赖Figma也能清楚展示设计规范。
- 相同决策对象在不同角色视图中有合理差异。
- 高风险内容不会被装饰性视觉弱化。

`【大厂能力】`

- 生成式UI
- 设计系统
- 跨端设计
- 无障碍
- 规范沉淀

---

## 15. 阶段 9｜异常、纠错、权限与审计

### 必须实现的异常

- Material not found
- Multiple records found
- Colour-record conflict
- Missing critical field
- Database unavailable
- Permission denied
- Update failed
- Record changed by another user
- User rejects recommendation
- User requests undo

### 每个异常必须回答

1. 发生了什么？
2. 系统没有做什么？
3. 哪些数据仍然安全？
4. 用户现在可以做什么？
5. 是否需要转人工？
6. 是否留下审计记录？

### 权限原则

- 最小权限。
- 读取和写入权限分开。
- 关键修改显示Before/After。
- 用户身份和时间被记录。
- 原始记录不可静默覆盖。
- 供应商和项目敏感信息按角色显示。

`【AI】`

- [ ] 编写异常Fixture和界面。
- [ ] 编写权限矩阵。
- [ ] 创建审计日志组件。
- [ ] 创建撤销逻辑。

`【你】`

- [ ] 确认异常文案清晰且不甩锅给用户。
- [ ] 确认隐私在此项目中主要体现为数据治理，而非虚构个人隐私场景。

`【共同加工】`

- [ ] 对每条高风险路径进行桌面推演。
- [ ] 确认失败时不会写入错误状态。

`【最终产出】`

- Error State Matrix
- Permission Matrix
- Audit Log
- Undo Flow
- Data Governance说明

`【大厂能力】`

- 异常恢复
- 隐私与安全
- 企业级权限思维
- 可信AI设计

---

# 第五部分：HTML Agent Surface 界面规格

## 16. 全局布局

### 顶部栏

- 项目名称
- 当前角色
- 当前站点
- 数据库状态
- Demo Mode
- Reset Demo
- Back to Case Study

### 左侧栏

- Material Queue
- 搜索
- 模拟扫描
- 批次筛选
- Case状态
- 最近任务

### 中央区域

- Material Record
- Lifecycle Timeline
- Observation
- Agent Analysis
- Generated Route

### 右侧区域

- Agent目标
- 对话与澄清
- Evidence
- Conflict
- Next Action
- Human Confirmation

### 底部抽屉

- Audit Log
- Source
- Change History
- Export

---

## 17. Screen 01｜Demo Start

### 给用户看的内容

> You are a recycling-site sorting supervisor. A recovered timber batch has arrived with incomplete and potentially conflicting information. Use the Agent to identify the record and decide the next responsible action.

### 界面组件

- Start Demo
- Scenario Picker
- Role Picker
- What This Demo Proves
- Prototype Data Disclaimer

### 场景选择

- Complete Record
- Missing Critical Information
- Colour-record Conflict
- High-risk Escalation

`【AI】`

- [ ] 搭建启动页和场景切换。
- [ ] 场景切换后载入对应Fixture。

`【你】`

- [ ] 确认启动说明真实、易懂。

`【最终产出】`

- 可进入四个场景的Demo Start页面。

`【大厂能力】`

- 场景化演示
- 产品Onboarding

---

## 18. Screen 02｜Material Queue

### 必须显示

- ID
- Species
- Hazard class
- Current stage
- Data completeness
- Case status
- Last verified

### 交互

- 选择材料
- 搜索ID
- 按风险筛选
- 按待人工处理筛选
- 查看最近任务

`【AI】`

- [ ] 搭建列表、筛选、空状态、加载状态。

`【共同加工】`

- [ ] 确认排序优先级反映工作风险，而非视觉偏好。

`【最终产出】`

- 可筛选的材料队列。

`【大厂能力】`

- B端信息密度
- 列表与筛选
- 任务优先级

---

## 19. Screen 03｜Scan or Identify

### 必须显示

- 模拟摄像头区域
- ID输入
- 观察颜色
- Demo图片选择
- 批次号
- Continue

### 状态

- Waiting
- Scanning
- Match Found
- No Match
- Multiple Matches
- Poor Signal

`【AI】`

- [ ] 使用预设数据模拟扫描。
- [ ] 不请求真实摄像头权限。

`【最终产出】`

- 六种识别状态。

`【大厂能力】`

- 多模态入口设计
- 状态反馈

---

## 20. Screen 04｜Material Record

### 必须显示

- Material ID
- Species
- Purpose
- Hazard class
- Durability
- Strength
- Preservative
- Supplier
- Expected colour
- Source
- Last verified

### 交互

- 展开字段来源
- 查看生命周期
- 查看修改历史
- 标记现场观察

`【AI】`

- [ ] 所有字段从数据对象读取。
- [ ] 缺失字段显示Missing，不使用空白。

`【共同加工】`

- [ ] 确认颜色不是唯一标识。

`【最终产出】`

- 可追溯的Material Record界面。

`【大厂能力】`

- 信息架构
- 数据可解释性

---

## 21. Screen 05｜Agent Analysis

### 必须显示

- 当前目标
- 已检查字段数
- 缺失字段
- 冲突
- 使用的工具
- 使用的证据
- 下一步候选操作

### 禁止显示

- 模型内部思维链
- 虚构的确定性
- 没有来源的安全结论

`【AI】`

- [ ] 显示工具和证据摘要。
- [ ] 将decision engine结果转成组件。

`【最终产出】`

- 可解释的Agent Analysis界面。

`【大厂能力】`

- AI可解释性
- 复杂状态表达

---

## 22. Screen 06｜Conflict Clarification

### 典型文案

> Observed colour does not match the linked material record. I will not recommend a reuse route until the identity or record is verified.

### 用户选项

- Re-scan ID
- Confirm observed colour
- Add photo
- Search similar records
- Create inspection task
- Cancel case

`【AI】`

- [ ] 冲突未解除前禁用复用确认。
- [ ] 所有用户选择写入Case历史。

`【最终产出】`

- 冲突澄清与升级流程。

`【大厂能力】`

- 异常处理
- 对话澄清
- 安全约束

---

## 23. Screen 07｜Generated Decision Card

### 必须显示

- Status
- Confidence
- Evidence
- Conflicts
- Missing fields
- Candidate route
- Required action
- Human confirmation
- Source and timestamp

### 允许的操作

- Accept next step
- Request manual review
- Edit observation
- Reject suggestion
- View evidence
- Export case

`【AI】`

- [ ] 由AgentDecision对象生成组件组合。
- [ ] 不同状态使用不同组件，但遵循相同结构。

`【共同加工】`

- [ ] 确认状态名不被误解为安全认证。

`【最终产出】`

- 五种决策状态卡。

`【大厂能力】`

- 生成式UI
- 决策支持
- 信息层级

---

## 24. Screen 08｜Inspection Task

### 字段

- Task type
- Material ID
- Reason
- Required test
- Assigned role
- Priority
- Due date
- Attachments
- Notes

### Agent自动填写

- Material ID
- 当前问题
- 冲突字段
- 建议检测项目

### 用户确认

- 负责人
- 优先级
- 是否创建

`【AI】`

- [ ] 创建表单、校验、成功和失败状态。

`【最终产出】`

- 人工检查任务创建流程。

`【大厂能力】`

- Agent任务闭环
- 表单设计
- 人机协作

---

## 25. Screen 09｜Confirmation and Write-back

### Before/After

- 原状态
- 新状态
- 原字段
- 修改字段
- 新建Case/Task
- 修改理由
- 操作者

### 操作

- Confirm update
- Edit
- Cancel
- Save draft

`【AI】`

- [ ] 实现Before/After Diff。
- [ ] 实现确认、失败和撤销。

`【最终产出】`

- 可确认和撤销的写回流程。

`【大厂能力】`

- 高风险确认
- 数据修改体验
- 可撤销设计

---

## 26. Screen 10｜Audit Log

### 显示

- 谁执行了操作
- Agent调用了什么
- 使用了什么证据
- 给出什么建议
- 用户是否接受
- 创建了什么任务
- 修改了什么字段
- 时间和理由

`【AI】`

- [ ] 实现时间线、筛选和详情。

`【最终产出】`

- 完整Case审计时间线。

`【大厂能力】`

- 企业级审计
- 可信AI
- 数据治理

---

## 27. Screen 11｜Dashboard

### 演示指标

- Total materials
- Reuse candidates
- Requires test
- Requires treatment
- Special handling
- Insufficient data
- Open tasks
- Human overrides

### 注意

所有数据标为Demo，不写真实效率结论。

`【AI】`

- [ ] 从本地Fixture实时计算卡片。

`【最终产出】`

- Demo Dashboard。

`【大厂能力】`

- 数据可视化
- 运营视角
- 指标意识

---

# 第六部分：技术实现计划

## 28. 推荐目录

```text
src/
  circular-timber-agent/
    CircularTimberAgentPage.tsx
    circular-timber-agent.css

    components/
      AgentHeader.tsx
      MaterialQueue.tsx
      MaterialScanner.tsx
      MaterialRecord.tsx
      LifecycleTimeline.tsx
      AgentPanel.tsx
      AgentDecisionCard.tsx
      ConflictCard.tsx
      InspectionTaskForm.tsx
      ConfirmationDiff.tsx
      AuditLog.tsx
      DemoScenarioPicker.tsx
      StatusBadge.tsx

    data/
      materials.ts
      lifecycleEvents.ts
      rules.ts
      demoScenarios.ts

    agent/
      types.ts
      tools.ts
      decisionEngine.ts
      scenarioEngine.ts
      audit.ts

    hooks/
      useAgentCase.ts
      useDemoScenario.ts

    utils/
      format.ts
      validation.ts
```

## 29. 实现原则

- 使用现有React、TypeScript、Vite。
- 第一版不增加复杂状态库。
- 使用`useReducer`管理Case状态。
- 使用本地JSON/TypeScript数据。
- 使用`localStorage`保存Demo会话。
- 提供Reset Demo。
- 使用CSS Grid完成桌面布局。
- 平板两栏，手机单栏+Agent抽屉。
- 核心Demo断网可运行。
- 不在前端保存真实API Key。

## 30. LLM接入策略

### 第一版：不接LLM

Agent决策由透明规则完成。

### 可选第二版：只处理语言

LLM可以：

- 将自然语言转换为筛选条件。
- 将结构化结果转成易读解释。
- 生成交接报告初稿。

LLM不可以：

- 判断安全。
- 生成危险等级。
- 修改原始数据。
- 决定结构复用。

`【验收标准】`

- 删除LLM后核心任务仍然成立。
- Agent价值来自工作流和工具，不是聊天文案。

---

# 第七部分：用户测试与指标

## 31. 测试参与者

推荐5至8人：

- 3至4名普通用户，测试理解和操作。
- 2至4名设计、工程、建筑、材料或相关背景参与者，测试逻辑可信度。

`【你】`

- [ ] 招募参与者。
- [ ] 说明测试用途。
- [ ] 获得录音或记录同意。
- [ ] 主持任务测试。

`【AI】`

- [ ] 生成测试脚本初稿。
- [ ] 生成记录表。
- [ ] 整理匿名化测试记录。
- [ ] 对反馈进行初步编码。

`【共同加工】`

- [ ] 检查AI编码是否符合原始记录。
- [ ] 确认最终问题与改进由本人判断。

## 32. 测试任务

1. 找到材料001。
2. 判断记录是否完整。
3. 处理颜色冲突。
4. 查看Agent建议依据。
5. 创建人工检测任务。
6. 确认并写回状态。
7. 找到修改历史。
8. 撤销一次操作。

## 33. 体验指标

- 任务完成率
- 完成时间
- 错误点击数
- 澄清次数
- 冲突识别率
- 创建任务成功率
- 错误恢复成功率
- 撤销成功率
- 建议依据发现率
- Agent边界理解正确率
- 人工覆盖率
- 不恰当主动提醒率
- 控制感评分
- 信任度评分
- 易用性评分

### 安全关键指标

- 错误地将信息不足材料呈现为可安全复用：零容忍。
- 未经确认写入关键记录：零容忍。
- 高风险冲突未升级：零容忍。

## 34. 测试报告结构

1. Participants
2. Tasks
3. Metrics
4. Observed Problems
5. Quotes（匿名且不超过必要长度）
6. Severity
7. Design Changes
8. Before/After
9. Remaining Limitations

`【最终产出】`

- Test Plan
- Test Script
- Observation Sheet
- Anonymised Notes
- Findings Matrix
- Before/After
- UX Metrics Dashboard

`【验收标准】`

- 所有数字来自真实测试。
- 测试问题导致至少一次界面迭代。
- 不把5至8人测试外推成行业结论。

`【大厂能力】`

- 可用性测试
- 体验指标
- 数据分析
- 迭代能力

---

# 第八部分：案例研究网页写作

## 35. 页面内容顺序

1. Hero
2. Original Project
3. Research Foundation
4. Stakeholder and Information Flow
5. Original System
6. Opportunity Gap
7. Focus User and JTBD
8. Before/After Journey
9. Service Blueprint
10. Agent Definition
11. Data Architecture
12. Tools and State Machine
13. Dialogue and Proactivity
14. Generative UI System
15. Exceptions and Governance
16. HTML Surface
17. User Testing
18. Iterations
19. Outcome
20. Reflection

## 36. 必须由本人确认的文字

`【你】`

- [ ] 本人在2023项目中的真实贡献。
- [ ] 原项目的真实局限。
- [ ] 为什么决定在2026扩展Agent。
- [ ] 哪些研究结论来自原项目。
- [ ] 哪些是2026设计假设。
- [ ] 测试中真实发生了什么。
- [ ] 最终反思。

## 37. 可以交给AI初稿的文字

`【AI】`

- [ ] 页面标题和副标题。
- [ ] 图片Caption。
- [ ] 数据字段说明。
- [ ] 组件状态说明。
- [ ] Before/After摘要。
- [ ] 测试报告格式。
- [ ] 英文翻译与语言润色。

## 38. 必须共同加工的文字

`【共同加工】`

- [ ] 项目概述，100至150字。
- [ ] 原问题与原方案，200至300字。
- [ ] 研究洞察，每条30至60字。
- [ ] Agent机会点，100至150字。
- [ ] 用户与JTBD，100字左右。
- [ ] Agent能力边界。
- [ ] 三至六段关键对话。
- [ ] 测试发现。
- [ ] 反思，150至250字。

## 39. 不需要写成长文的部分

- 数据模型：用表格和界面展示。
- 状态机：用图和动态Demo展示。
- Trigger Matrix：用表格展示。
- 组件规范：用Code-native Design System展示。
- 异常状态：直接用可操作界面展示。
- 测试指标：用Dashboard和Before/After展示。

`【验收标准】`

- 页面以视觉、界面和证据为主。
- 每个长段落不超过约150字。
- 每一板块回答一个问题。
- 没有空泛AI行业背景。

`【大厂能力】`

- 叙事能力
- 书面表达
- 设计沟通
- 信息层级

---

# 第九部分：AI工作指令

## 40. 每次交给AI前使用的总提示词

```text
请先完整阅读 CIRCULAR_TIMBER_AGENT_MASTER_PLAN.md。

当前只执行阶段：[填写阶段编号与名称]。
你的责任标签是：【AI】。

执行前先输出：
1. 你理解的本阶段目标；
2. 你将读取的文件；
3. 你将修改的文件；
4. 你不会触碰的范围；
5. 本阶段验收标准。

执行要求：
- 不虚构用户研究、行业数据、法规或测试结果；
- 明确区分2023原项目与2026 AI扩展；
- 不把Agent描述为安全认证系统；
- 不添加未经确认的产品功能；
- 所有高风险写入需要人工确认与审计；
- 使用本地演示数据时明确标注Demo；
- 完成后运行适当测试并报告结果；
- 只在当前阶段范围内修改文件。
```

## 41. AI完成工作后的报告格式

```text
阶段：
完成内容：
修改文件：
新增文件：
验证方式：
通过的验收项：
仍需本人确认：
发现的风险：
下一阶段建议：
```

## 42. 本人审核AI工作的检查表

`【你】`

- [ ] 是否出现虚构事实？
- [ ] 是否混淆2023和2026？
- [ ] 是否替本人做了必须由本人作出的判断？
- [ ] 是否加入了本人无法解释的技术？
- [ ] 是否把Demo规则写成真实规则？
- [ ] 是否存在安全结论过度确定？
- [ ] 是否所有修改可追溯？
- [ ] 是否通过当前阶段验收？

---

# 第十部分：15个有效工作日计划

## 43. 日程

| Day | 阶段 | 【你】 | 【AI】 | 【共同加工】 | 当日交付 |
|---|---|---|---|---|---|
| 1 | 范围冻结 | 确认用户与场景 | 建看板 | 选Happy/Error Path | Scope |
| 2 | 资产审计 | 确认来源 | 扫描文件 | 分类与Caption | Source Map |
| 3 | 研究综合 | 核对结论 | 生成矩阵 | Evidence→Insight | Research Foundation |
| 4 | 用户与服务 | 判断角色 | 画流程初稿 | 完成Blueprint | Journey/Blueprint |
| 5 | 数据模型 | 确认字段 | 建类型与Fixture | 定关键字段 | Data Package |
| 6 | Agent定义 | 确认边界 | 编工具与状态 | 审核动作 | Agent Contract |
| 7 | 规则引擎 | 审核规则 | 编decision engine | 桌面推演 | Tested Rules |
| 8 | Surface框架 | 审核布局 | 搭三栏结构 | 调信息层级 | App Shell |
| 9 | Happy Path | 体验演示 | 完成功能 | 调对话 | Working Flow |
| 10 | 异常路径 | 审核文案 | 实现3异常 | 检查恢复 | Error Flows |
| 11 | 生成UI/规范 | 审核视觉 | 组件与状态 | 调整规范 | Design System |
| 12 | 权限与审计 | 判断权限 | 实现日志/撤销 | 高风险检查 | Governance |
| 13 | 内部测试 | 自测 | 修Bug | 完成脚本 | Test-ready Build |
| 14 | 用户测试 | 主持5–8人 | 整理记录 | 归纳问题 | Findings |
| 15 | 案例整合 | 写反思 | 整合网页 | 完成叙事与简历 | Final Case Study |

---

# 第十一部分：简历与面试材料

## 44. 项目完成前的简历写法

> **Circular Timber｜循环木材追踪系统**　个人项目｜2023  
> 2026年正在进行Agent辅助回收决策与HTML交互原型扩展。

不得写“已构建Agent系统”。

## 45. 项目完成后的简历写法模板

> **Circular Timber｜循环木材追踪与Agent辅助回收决策系统**　个人项目｜2023，AI交互扩展于2026

- 基于木材处理方式、风险类别与多角色生命周期研究，设计热致变色色码和关系数据库，使材料种类、处理历史及复用相关信息能够随材料流转。
- 面向拆除后回收分拣场景，构建Agent任务流程与HTML交互原型，通过数据库查询、缺失与冲突检测、分级主动提醒、人工确认和审计记录，将被动材料数据转化为可执行的候选路径。
- 建立约束式生成UI、异常恢复、角色权限与体验指标体系，并通过真实可用性测试迭代关键状态与风险文案。【完成测试后补充真实样本和结果】

## 46. 面试必须能回答的问题

1. 为什么原数据库还需要Agent？
2. 为什么这不是一个普通聊天机器人？
3. Agent调用了哪些工具？
4. 哪些决定由规则完成，哪些由人完成？
5. 为什么不让LLM直接判断木材安全？
6. 什么情况下Agent会主动打断？
7. 什么情况下Agent必须保持安静？
8. 生成式UI如何受到约束？
9. 数据冲突时系统如何恢复？
10. 谁可以修改数据库？
11. 修改如何被撤销和审计？
12. 测试指标如何定义？
13. 用户测试发现了什么？
14. 哪部分是2023原作，哪部分是2026扩展？
15. AI在项目中帮助你做了什么？
16. 哪些判断坚持由你本人完成？
17. 如果再做一个月，最先验证什么？

`【你】`

- [ ] 为每个问题准备60至90秒真实回答。

`【AI】`

- [ ] 根据最终项目模拟面试追问。
- [ ] 检查回答是否有项目证据。

`【共同加工】`

- [ ] 删除无法展示或无法解释的简历描述。

---

# 第十二部分：最终完成定义

## 47. Definition of Done

只有全部满足以下条件，项目才可以作为校招第一项目：

### 真实性

- [ ] 2023与2026时间清楚。
- [ ] 无虚构研究、测试、法规和结果。
- [ ] 演示数据和规则均明确标注。
- [ ] 本人贡献清楚。

### 研究

- [ ] 原始研究能够追溯。
- [ ] 有Evidence→Insight→Decision。
- [ ] Agent机会来自真实流程缺口。

### Agent

- [ ] 有目标、状态、工具、边界、行动和审计。
- [ ] 不是普通聊天框。
- [ ] 有主动触发和抑制规则。
- [ ] 有人工确认和转人工。

### 交互

- [ ] 一个完整Happy Path可运行。
- [ ] 三个异常路径可运行。
- [ ] 有澄清、拒绝、撤销和恢复。
- [ ] 所有状态有明确反馈。

### 生成UI与规范

- [ ] 结构化决策驱动组件组合。
- [ ] 有Code-native Design System。
- [ ] 有桌面、平板和手机适配。
- [ ] 不只依赖颜色。

### 数据与安全

- [ ] 数据模型完整。
- [ ] 写入动作需要确认。
- [ ] 修改可审计、可撤销。
- [ ] Agent不输出安全认证。

### 测试

- [ ] 完成5至8人真实测试。
- [ ] 指标和发现真实。
- [ ] 至少完成一轮设计迭代。
- [ ] 有Before/After证据。

### 作品集

- [ ] 案例研究逻辑完整。
- [ ] Live Surface可进入。
- [ ] GitHub或源码可查看。
- [ ] 简历描述与项目一致。
- [ ] 面试15问可以回答。

---

# 第十三部分：当前下一步

## 48. 下一步只做这五件事

`【你】`

1. [ ] 确认第一目标用户和主场景。
2. [ ] 确认预计投入时间与截止日期。
3. [ ] 确认是否愿意进行5至8人测试。
4. [ ] 确认本人2023原项目的真实贡献范围。
5. [ ] 确认项目最终以中文、英文或双语展示。

`【AI】`

1. [ ] 完成阶段1资产审计。
2. [ ] 创建Source Map。
3. [ ] 建立开发目录骨架。
4. [ ] 生成Scope与任务看板。
5. [ ] 在本人确认前不开发范围外功能。

`【共同加工】`

1. [ ] 冻结Happy Path与三个异常路径。
2. [ ] 冻结关键字段与演示规则。
3. [ ] 冻结案例研究页面信息架构。

---

## 附录 A｜推荐项目标签

- Agent Interaction Design
- Human-in-the-loop
- Constraint-based Generative UI
- Material Traceability
- Circular Systems
- Information Architecture
- Data Governance
- HTML Prototype
- UX Metrics
- Error Recovery

## 附录 B｜推荐项目主线

> Invisible material history → Visible traceability → Passive database limitation → Agent-assisted action → Human confirmation → Auditable circular handoff

## 附录 C｜最高优先级设计原则

1. 数据不足时不猜测。
2. 高风险时优先升级而不是自动化。
3. 每个建议都显示证据。
4. 每个关键修改都需要确认。
5. 每个操作都可追溯。
6. 每个失败都有恢复路径。
7. Agent帮助用户行动，但不替用户承担专业责任。

