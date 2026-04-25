# 数据中心能耗模型项目总计划

## 1. 项目目标

基于 Google `cluster-data` 公开数据集中的 `ClusterData2019` 与 `PowerData2019`，构建一个面向 `power domain / PDU` 的能耗预测系统。项目主目标是预测归一化电力利用率，优先选择 `measured_power_util` 作为监督标签，次选 `production_power_util` 作为业务负载剥离后的辅助标签。

项目最终应支持以下能力：
- 从 BigQuery 获取并整理可训练的时序样本。
- 基于资源利用率、作业事件和机器属性预测下一时间窗功率利用率。
- 对比线性模型、非线性模型与深度学习模型的效果。
- 输出可复现实验结果、图表、模型配置和推理脚本。

## 2. 建模范围

### 2.1 主任务

以 `PDU x 时间窗` 作为训练样本，建立以下预测任务：
- 单步预测：`P_{t+1} = g(X_{t-k+1:t})`
- 多步预测：预测未来 `h` 个时间窗的 power utilization
- 可选扩展：异常波动识别、削峰场景分析、what-if 仿真

### 2.2 标签定义

主标签：
- `measured_power_util`

辅助标签：
- `production_power_util`

能量指标：
- 使用离散积分近似 `E = sum(P_t * delta_t)` 将功率利用率序列转为能量消耗指标

### 2.3 非目标

当前阶段不追求：
- 冷却系统、PUE、CRAC、UPS 的全园区级建模
- 绝对 kW 的高精度还原
- GPU、磁盘、DRAM 通道级微结构功耗建模

## 3. 数据来源与字段映射

### 3.1 PowerData2019

核心字段：
- `cell`
- `pdu`
- `measured_power_util`
- `production_power_util`
- 时间戳字段
- `machine_to_pdu_mapping`

用途：
- 作为监督标签来源
- 提供机器到 power domain 的映射

### 3.2 ClusterData2019

重点使用的表与字段：
- `instance_usage`
  - `average_usage.cpus`
  - `maximum_usage.cpus`
  - `assigned_memory`
  - `page_cache_memory`
  - `cycles_per_instruction`
  - `memory_accesses_per_instruction`
  - CPU usage distribution 或 percentile 信息
- `instance_events`
  - submit、schedule、finish、evict 等事件计数
  - priority
- `machine_events`
  - 机器容量
  - 平台类型
  - switch 或 rack 相关信息
- `machine_attributes`
  - 稳定属性和变更信息
- `collection_events`
  - 作业级结构和调度背景

### 3.3 建模特征建议

按 `PDU x 时间窗` 聚合：
- CPU 利用率：平均、峰值、P90、P99
- 内存利用率：占用率、page cache 占比
- 微结构代理特征：CPI、MAI
- 工作负载强度：实例数、作业数、优先级分层占比
- 事件特征：提交、结束、驱逐、迁移计数
- 机器侧特征：机器数、平台类型分布、容量总和
- 时间特征：小时、星期、是否工作时段、节律特征
- 历史标签特征：过去若干窗口的 power utilization

## 4. 建模公式与方法选择

基于当前数据集，优先采用以下建模思路。

### 4.1 问题定义

主公式：
- `P_t = f(S_t, A_t, E_t)`
- `P_{t+1} = g(S_t, A_t, E_t)`

其中：
- `S_t` 表示系统状态和资源利用率聚合特征
- `A_t` 表示请求、作业和任务事件特征
- `E_t` 表示执行环境与机器属性

### 4.2 基线模型

第一层基线：
- 线性利用率模型：`P_u = (P_max - P_idle)u + P_idle`
- 经验非线性模型：`P_u = (P_max - P_idle)(2u - u^r) + P_idle`
- 资源加权模型：`P_t = C_cpu u_cpu,t + C_memory u_memory,t + C_disk u_disk,t + C_nic u_nic,t`
- 多变量回归模型

第二层基线：
- 树模型：XGBoost 或 LightGBM
- 时序统计基线：持久性预测、滑动平均、AR 风格回归

### 4.3 深度学习主模型

主模型候选：
- LSTM 或 GRU
- Temporal Convolution Network
- Temporal Transformer 或 PatchTST 风格时序模型

建议顺序：
1. 先做线性与树模型基线
2. 再做 LSTM
3. 再做 Transformer
4. 最后做多步预测与消融实验

## 5. 目标系统结构

建议的项目结构：

```text
project/
|-- configs/
|-- data/
|   |-- raw/
|   |-- interim/
|   +-- processed/
|-- notebooks/
|-- sql/
|   |-- extraction/
|   +-- validation/
|-- src/
|   |-- data/
|   |-- features/
|   |-- models/
|   |-- training/
|   |-- evaluation/
|   +-- serving/
|-- reports/
|-- scripts/
+-- .trellis/
```

## 6. 分阶段实施计划

### Phase 0: 项目定义与环境初始化

目标：
- 明确研究问题、目标标签、评价指标和实验边界
- 配置 GCP、BigQuery、账单与权限
- 确认本地开发环境和依赖管理方式

交付物：
- 项目 README 初稿
- 环境配置说明
- 数据访问清单

完成标准：
- 可以稳定查询样例数据
- 明确成本上限和导出策略

### Phase 1: 数据抽取与样本表构建

目标：
- 编写 SQL 将 `instance_usage`、`instance_events`、`machine_events` 与 `machine_to_pdu_mapping` 关联
- 形成统一时间粒度的 `PDU x 时间窗` 样本表
- 处理重复、缺失、异常和时钟对齐问题

交付物：
- BigQuery SQL 脚本
- 原始导出数据字典
- `processed` 训练样本表

完成标准：
- 训练样本表可直接被 Python 训练管道读取
- 标签与特征时间严格对齐

### Phase 2: EDA 与数据质量分析

目标：
- 分析标签分布、周期性、突变点和长尾问题
- 验证 CPU、内存、事件特征和功率的相关关系
- 确定归一化、缺失值填充和异常值策略

交付物：
- EDA notebook
- 数据质量报告
- 特征保留或剔除清单

完成标准：
- 明确最终特征集合
- 明确时间窗口长度 `k` 和预测跨度 `h`

### Phase 3: 基线模型

目标：
- 构建持久性预测基线
- 构建线性回归、Ridge 或 Lasso、XGBoost 或 LightGBM 基线
- 构建利用率驱动的物理启发式模型

交付物：
- baseline 训练脚本
- baseline 结果表
- 误差对比图

完成标准：
- 建立稳定、可复现的 baseline
- 明确深度学习模型相对基线的提升目标

### Phase 4: 深度学习建模

目标：
- 设计时序窗口数据集
- 实现 LSTM 与 Transformer 主模型
- 加入历史标签、时间编码和机器结构特征

交付物：
- dataset 类与 dataloader
- 模型定义与训练配置
- checkpoint 与训练日志

完成标准：
- 在验证集上稳定优于主要 baseline
- 训练过程可复现

### Phase 5: 评估、消融与解释

目标：
- 评估单步、多步预测误差
- 进行特征消融和窗口长度实验
- 分析不同 cell、PDU、负载强度下的误差表现

推荐指标：
- MAE
- RMSE
- MAPE 或 sMAPE
- R2
- 峰值误差和高分位误差

交付物：
- 实验表格
- 消融实验图
- 误差分桶分析

完成标准：
- 形成可写入论文或报告的核心结果

### Phase 6: 工程化与成果沉淀

目标：
- 固化训练入口、推理入口和配置文件
- 统一日志、模型版本和输出目录结构
- 输出论文图表、方法章节、实验章节

交付物：
- CLI 训练脚本
- 推理脚本
- 报告或论文草稿

完成标准：
- 新环境可复现实验
- 最终结果可直接汇报

## 7. 评价指标与验收标准

### 7.1 模型效果验收

最低验收：
- 深度学习模型优于持久性预测和线性回归基线
- 对主要 PDU 的 MAE 或 RMSE 改善具有统计稳定性

理想验收：
- LSTM 或 Transformer 在大多数 power domains 上显著优于树模型和线性模型
- 多步预测在短期窗口内保持可接受误差

### 7.2 工程验收

- 数据抽取脚本可复用
- 特征工程和训练配置参数化
- 实验结果自动写入固定目录
- 可以在本地或云端完成一次端到端重跑

## 8. 风险与对策

### 风险 1: 数据量过大，下载和本地存储成本高

对策：
- 不下载全量原始数据
- 先在 BigQuery 做过滤、聚合、采样，再导出 Parquet

### 风险 2: 缺少绝对功率、制冷和环境变量

对策：
- 将研究目标限定为 `IT workload -> normalized power utilization`
- 不夸大为全数据中心总能耗建模

### 风险 3: 标签与特征时间错位

对策：
- 在 SQL 层统一时间粒度和时间戳对齐逻辑
- 在样本表内保存窗口起止时间与版本信息

### 风险 4: 不同 cell 或 PDU 分布差异大

对策：
- 做分层验证
- 支持全局模型与按 cell 微调两种路线

### 风险 5: 深度学习收益不明显

对策：
- 强化 baseline
- 引入事件特征、历史标签和多尺度时间特征
- 若收益仍弱，优先保留树模型作为主交付

## 9. 建议的近期执行顺序

第一周：
- 完成 GCP 或 BigQuery 配置
- 写出第一版 SQL
- 导出一个小规模样本子集

第二周：
- 完成 PDU 级样本表
- 完成 EDA 和数据质量分析
- 明确最终特征列表

第三周：
- 跑完持久性预测、线性回归、XGBoost 基线
- 形成第一版实验记录

第四周：
- 实现 LSTM 主模型
- 调整窗口长度、归一化和损失函数

第五周：
- 实现 Transformer 或 TCN
- 做消融实验和多步预测实验

第六周：
- 整理报告、论文图表和工程交付物
- 固化推理脚本与配置

## 10. 当前建议的第一落地点

下一步最应该先做的不是训练深度学习，而是先完成下面 3 件事：
1. 明确使用 `measured_power_util` 还是 `production_power_util` 作为主标签。
2. 写第一版 BigQuery SQL，把 `machine_to_pdu_mapping` 和 `instance_usage` 关联起来。
3. 先导出一个单 cell、少量 PDU、短时间范围的样本，验证字段可用性和成本。

只有这一步跑通后，后面的 LSTM 或 Transformer 才不会建立在错误样本表上。
