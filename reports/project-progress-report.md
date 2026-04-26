# 数据中心能耗建模项目进度报告

**更新日期**: 2026-04-26

## 1. 项目目标

基于 Google ClusterData2019、PowerData2019 和 `machine_to_pdu_mapping`，构建以 PDU 为粒度的能耗建模数据集，比较传统机器学习与深度学习时序模型，并评估模型在未见 PDU 上的泛化能力，最终形成可复现、可汇报的项目交付物。

## 2. 当前总体状态

项目核心实验链路已经打通，当前已从“脚手架搭建”进入“结果固化与报告收口”阶段。

- 已完成范围定义、BigQuery 访问验证、SQL 抽取、训练数据集构建、baseline 训练、深度模型训练和 holdout 泛化评估。
- 已得到当前最强实验结论：`v2` 残差 LSTM 在未见 PDU holdout 上优于 `random_forest`，是当前主模型候选。
- 当前主要剩余工作不是继续打通流程，而是统一复现入口、整理图表和输出最终汇报材料。

## 3. 里程碑进展

| 日期 | 阶段 | 进展 |
|---|---|---|
| 2026-04-24 | 项目初始化 | 完成 Trellis 任务拆解、规范沉淀、SQL/数据/训练脚手架搭建，准备 `dc-energy` 环境 |
| 2026-04-25 | 数据接入 | 打通 Google Cloud CLI 与 BigQuery 访问，验证数据源可用性 |
| 2026-04-25 | 第一版数据集与 baseline | 构建 `data/processed/v1`，完成 baseline benchmark |
| 2026-04-25 | 深度模型优化 | 完成 LSTM/Transformer 对比、LSTM 消融、regularization、loss/normalization 筛选 |
| 2026-04-25 | 泛化评估 | 构建 `v2_expanded_dev` 与 `v2_holdout_pdu`，完成未见 PDU holdout 评估 |
| 2026-04-26 | 交付收口 | 开始整理项目进度、复现流程和最终报告材料 |

## 4. 已完成工作

### 4.1 范围定义与数据访问

- 明确主标签为 `measured_power_util`。
- 明确样本粒度为 PDU 时间窗样本，并固定训练/验证/测试切分策略。
- 完成 BigQuery 访问验证，确认可访问 `clusterdata_2019_*`、`powerdata_2019` 与映射表。
- 形成项目边界与访问规则，支撑后续抽取和建模。

### 4.2 SQL 抽取与数据集构建

- 实现 power trace 抽取、machine-to-PDU 映射、instance usage 关联、时间对齐与聚合 SQL。
- 构建首版多 PDU 开发数据集 `data/processed/v1`。
- 进一步扩展得到 `data/processed/v2_expanded_dev` 和 `data/processed/v2_holdout_pdu`。
- 数据质量报告显示当前关键数据集无重复主键、关键字段缺失率均为 `0`。

当前关键数据集规模：

| 数据集 | 用途 | 规模 |
|---|---|---:|
| `v1` | 初版开发集 | 864 行 |
| `v2_expanded_dev` | 扩展开发集 | 2983 行 |
| `v2_holdout_pdu/full.parquet` | 未见 PDU 外部评估集 | 1132 行 |

### 4.3 Baseline 建模

- 已完成 persistence、线性模型、树模型等 baseline 训练和统一 benchmark 输出。
- 在 `v1` 上，最强 baseline 为 `random_forest`。
- 在 `v2_expanded_dev` 上，`persistence` 在开发集内部测试上非常强，但在未见 PDU holdout 上明显退化。

### 4.4 深度模型建模

- 已完成 LSTM 与 Transformer 的训练流程和对比实验。
- 已修正深度学习训练管道中的关键问题，包括 train-split 标准化、val/test 历史上下文继承、默认训练参数和早停策略。
- 已完成残差预测路线、层数、隐藏维度、正则化、loss 和目标归一化筛选。
- 当前最佳单模型配置为残差 LSTM 路线，核心特征为：
  - `target_mode=residual`
  - `context_length=12`
  - `num_layers=1`
  - `hidden_size=96`
  - `weight_decay=1e-3`

## 5. 关键实验结果

### 5.1 初版开发集 `v1`

`v1` baseline 最优结果：

| 模型 | test MAE | test RMSE | test R2 |
|---|---:|---:|---:|
| `random_forest` | 0.0038355 | 0.0048768 | 0.9165940 |

`v1` 深度模型阶段结论：

- 最佳单次残差 LSTM 已能超过 `random_forest` 单次结果。
- 但 repeated-run 平均结果仍与 `random_forest` 接近，且方差更高。
- 说明深度模型路线有效，但在 `v1` 上仍存在稳定性问题。

`v1` repeated-run 对比：

| 模型 | mean test MAE | mean test RMSE | mean test R2 |
|---|---:|---:|---:|
| `lstm_residual_h96` | 0.0040782 | 0.0048765 | 0.9164583 |
| `random_forest` | 0.0038061 | 0.0048310 | 0.9181447 |

### 5.2 扩展开发集 `v2_expanded_dev`

扩展开发集内部测试结果：

| 模型 | dev test MAE | dev test RMSE | dev test R2 |
|---|---:|---:|---:|
| `persistence` | 0.0021626 | 0.0029021 | 0.9952789 |
| `random_forest` | 0.0052447 | 0.0087945 | 0.9566434 |
| `lstm_residual_h96_wd1e3` | 0.0021204 | 0.0027021 | 0.9959070 |

结论：

- 扩展数据后，残差 LSTM 在开发集内部测试上已经成为最优模型。
- `random_forest` 在 `v2` 内部测试上明显落后于 LSTM。

### 5.3 未见 PDU Holdout 泛化结果

holdout 评估设置：

- 开发 PDU: `pdu20`, `pdu21`, `pdu22`, `pdu23`, `pdu24`
- 未见 holdout PDU: `pdu17`, `pdu25`

holdout 结果：

| 模型 | holdout MAE | holdout RMSE | holdout R2 |
|---|---:|---:|---:|
| `persistence` | 0.0041281 | 0.0276056 | 0.6575220 |
| `random_forest` | 0.0060861 | 0.0087174 | 0.9658480 |
| `lstm_residual_h96_wd1e3` | 0.0036981 | 0.0050118 | 0.9886600 |

当前最重要结论：

- `persistence` 只在开发集内部有效，跨 PDU 泛化能力明显不足。
- `random_forest` 具备一定泛化能力，但仍明显落后于残差 LSTM。
- 残差 LSTM 是当前未见 PDU 泛化表现最强的模型，也是目前最有价值的主模型候选。

## 6. 当前判断

从当前实验结果看，项目已经完成了从“可运行”到“有结论”的关键跨越。

- 如果目标是完成一轮有效的建模研究，核心目标已经达到。
- 如果目标是形成论文或答辩材料，当前最值得强调的结论不是 `v1` 的单次最优，而是 `v2` 未见 PDU holdout 上残差 LSTM 的泛化优势。
- 当前建议将 `v2` 残差 LSTM 作为主模型候选，并以 holdout 结果作为主结论支撑。

## 7. 风险与局限

- 当前 holdout 评估仅覆盖 `pdu17` 和 `pdu25`，外部泛化结论仍需要更多 PDU 验证。
- `v1` repeated-run 结果表明 LSTM 方差高于 `random_forest`，训练稳定性仍有改进空间。
- 目前结果产物分散在 `reports/benchmarks/`、`reports/deep-models/`、`reports/comparisons/` 下，尚未完全统一为单一复现入口。
- Trellis 任务状态与实际实验进展存在不同步现象，任务面板还没有完全反映实验已完成的部分。

## 8. 下一阶段待办

### 高优先级

- 统一训练、评估、推理入口和配置说明。
- 整理最终图表、结果表和报告结论，形成导师汇报版本。
- 明确主模型选择，并固定最终推荐配置。

### 可选增强

- 补做 `v2` holdout 多 seed 稳定性验证。
- 继续扩展 holdout PDU 范围，验证泛化结论是否稳定。
- 增加误差可视化和案例分析，支撑论文叙述。

## 9. 关键产物位置

- 工作日志：`.trellis/workspace/刘智康/journal-1.md`
- 任务说明：`.trellis/tasks/04-24-package-results-and-report/`
- 数据质量报告：`reports/data-quality/`
- baseline 结果：`reports/benchmarks/`
- 深度模型结果：`reports/deep-models/`
- 对比与 holdout 结果：`reports/comparisons/`

## 10. 一句话结论

截至 2026-04-26，项目已经完成数据接入、样本构建、baseline 与深度模型训练以及未见 PDU 泛化验证；当前最强结论是 `v2` 残差 LSTM 在 holdout 上优于 `random_forest`，项目已进入复现流程和汇报材料的最终收口阶段。
