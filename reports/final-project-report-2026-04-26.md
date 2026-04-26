# 数据中心 PDU 能耗预测项目最终报告

**日期**: 2026-04-26  
**项目主题**: 基于 Google ClusterData2019 / PowerData2019 的 PDU 级能耗预测与泛化验证

## 1. 项目目标

本项目的目标是基于 Google 公共集群数据与电力数据，构建以 PDU 为粒度的能耗预测数据集，比较传统机器学习模型与时序深度学习模型，并重点验证模型在未见 PDU、未见 cell 场景下的泛化能力。

最终交付目标不是单次跑通实验，而是形成：

- 可复现的数据抽取与训练流程
- 可追溯的实验结果
- 可直接用于导师汇报、论文撰写或答辩的结论材料

## 2. 研究问题

本项目围绕三个核心问题展开：

1. 能否用公开数据构建稳定的 PDU 级能耗建模样本表。
2. 时序深度模型能否优于传统机器学习基线。
3. 模型是否真正学到可迁移结构，而不是只记住训练中出现过的 PDU 或单一 cell 分布。

## 3. 数据与样本构建

### 3.1 数据来源

- `clusterdata_2019_*`
- `powerdata_2019`
- `machine_to_pdu_mapping`

### 3.2 样本定义

- 预测粒度：PDU 5 分钟时间窗
- 目标标签：`measured_power_util`
- 主要输入：CPU 使用统计、实例数量、机器数量、时间特征、上一时刻功率、上一时刻 CPU 使用量

### 3.3 特征合同

核心字段包括：

- `window_start`
- `cell`
- `pdu`
- `measured_power_util`
- `production_power_util`
- `instance_count`
- `collection_count`
- `machine_count`
- `total_cpu_usage`
- `avg_cpu_usage`
- `max_cpu_usage`
- `hour`
- `day_of_week`
- `is_weekend`
- `prev_measured_power_util`
- `prev_total_cpu_usage`

### 3.4 数据集版本

| 版本 | 含义 | 行数 |
|---|---|---:|
| `v1` | 初版 `cell=f` 多 PDU 开发集 | `864` |
| `v2_expanded_dev` | 扩展后的 `cell=f` 开发集 | `2983` |
| `v2_holdout_pdu` | `cell=f` 未见 PDU holdout | `1132` |
| `v3_cell_e_dev` | `cell=e` 开发集 | `8004` |
| `v3_cell_e_holdout_pdu` | `cell=e` 外部 holdout | `2991` |
| `v4_cell_b_dev` | `cell=b` 开发集 | `8004` |
| `v4_cell_b_holdout_pdu` | `cell=b` 第三轮外部 holdout | `2001` |

所有当前关键数据集均通过质量检查：

- 重复主键数为 `0`
- 关键字段缺失率为 `0`

## 4. 模型方案

### 4.1 基线模型

已实现并评估的基线包括：

- `persistence`
- `moving_average`
- `linear_regression`
- `ridge`
- `cpu_heuristic`
- `random_forest`

其中表现最强、最稳定的传统基线是 `random_forest`。

### 4.2 深度模型

已实现并比较的时序模型包括：

- `LSTM`
- `Transformer`

多轮实验后，当前最优路线为残差 LSTM，推荐配置为：

- `target_mode=residual`
- `context_length=12`
- `num_layers=1`
- `hidden_size=96`
- `weight_decay=1e-3`
- `loss=mse`
- `target_scaling=standard`

### 4.3 最终推荐模型

如果以单模型交付为主，推荐：

- **主模型**：残差 LSTM 单模型

如果以最终效果展示为主，推荐：

- **展示模型**：3-member residual LSTM ensemble

原因：

- 单模型已经稳定优于 `random_forest`
- 3-member ensemble 在三轮外部验证中都能进一步改善 holdout 指标

## 5. 方法演进过程

项目不是一次性得到最终结果，而是经过三层推进：

### 5.1 初版开发与基线建立

- 构建 `v1`
- 建立 baseline benchmark
- 完成 LSTM / Transformer 初步比较

### 5.2 同 cell 未见 PDU 泛化验证

- 扩展 `cell=f` 数据规模
- 构建 `v2_expanded_dev`
- 在 `pdu17, pdu25` 上做未见 PDU holdout
- 首次确认残差 LSTM 明显优于 `random_forest`

### 5.3 跨 cell 外部验证

- 在 `cell=e` 做第二轮外部验证
- 在 `cell=b` 做第三轮外部验证
- 三轮外部验证全部显示 LSTM 稳定优于 `random_forest`

## 6. 核心实验结果

### 6.1 `v1` 初版数据集

`v1` 上最强 baseline：

| model | test MAE | test RMSE | test R2 |
|---|---:|---:|---:|
| `random_forest` | `0.0038355` | `0.0048768` | `0.9165940` |

阶段结论：

- 最佳单次 LSTM 可以超过 `random_forest`
- 但 repeated-run 平均表现仍接近 baseline
- 当时主要问题是训练稳定性不足

### 6.2 第一轮外部验证：`cell=f`

开发集：`v2_expanded_dev`  
holdout：`pdu17`, `pdu25`

| model | holdout mean MAE | holdout mean RMSE | holdout mean R2 |
|---|---:|---:|---:|
| `lstm_residual_h96_wd1e3` | `0.0037102647` | `0.0050186245` | `0.9886073640` |
| `random_forest` | `0.0060610662` | `0.0087285977` | `0.9657566403` |

结论：

- LSTM 在三次重复实验中 `3/3` 全面优于 `random_forest`
- 这是第一次形成可靠的外部泛化证据

### 6.3 第二轮外部验证：`cell=e`

开发集：`pdu26, pdu27, pdu30, pdu31`  
holdout：`pdu28, pdu29`

| model | holdout mean MAE | holdout mean RMSE | holdout mean R2 |
|---|---:|---:|---:|
| `lstm_residual_h96_wd1e3` | `0.0032975996` | `0.0041938260` | `0.9933083234` |
| `random_forest` | `0.0041824505` | `0.0052685854` | `0.9895525012` |

结论：

- 在新 cell 上，LSTM 仍然稳定优于 `random_forest`
- 说明模型优势并非只存在于原始 `cell=f`

### 6.4 第三轮外部验证：`cell=b`

开发集：`pdu11, pdu12, pdu13, pdu14`  
holdout：`pdu15`

| model | holdout mean MAE | holdout mean RMSE | holdout mean R2 |
|---|---:|---:|---:|
| `lstm_residual_h96_wd1e3` | `0.0030404069` | `0.0038973598` | `0.9743562430` |
| `random_forest` | `0.0038785667` | `0.0049205475` | `0.9590908819` |

结论：

- 第三轮外部验证仍然是 `3/3` 全面胜出
- 进一步压实了模型的迁移有效性

### 6.5 三轮外部验证汇总

| round | holdout setup | LSTM vs RF outcome |
|---|---|---|
| `v2` | `cell=f`, unseen PDU | `3/3` 全胜 |
| `v3` | `cell=e`, cross-cell holdout | `3/3` 全胜 |
| `v4` | `cell=b`, third external holdout | `3/3` 全胜 |

### 6.6 Ensemble 结果

3-member ensemble 在三轮 holdout 上均优于单模型均值：

| round | ensemble MAE | ensemble RMSE | ensemble R2 |
|---|---:|---:|---:|
| `v2` | `0.0036813214` | `0.0049790579` | `0.9888077557` |
| `v3` | `0.0032374905` | `0.0041258109` | `0.9935250758` |
| `v4` | `0.0029996755` | `0.0038512212` | `0.9749633744` |

## 7. 最终结论

本项目当前最强、最有价值的结论有三条：

1. 基于公开 Google 数据可以构建稳定、可训练、可复现的 PDU 级能耗样本集。
2. 残差 LSTM 已经稳定优于 `random_forest`，不再只是单次偶然胜出。
3. 这种优势不仅存在于原始 `cell=f`，也在 `cell=e` 和 `cell=b` 的外部 holdout 中重复出现。

因此，当前可以较有把握地判断：

- 模型已经学到具有迁移性的时序结构
- 结论已经超出“只适用于单一数据切片”的阶段

## 8. 局限性

虽然结果已经较强，但仍有边界：

- 当前仍只覆盖了部分 cell，而不是全部机房分区
- 外部验证是按人工筛选的高质量 PDU 进行，不代表所有弱质量 PDU 都同样成立
- 目前主要指标仍是回归误差，缺少更深入的误差分布解释和异常场景分析
- 目前图表类材料还不多，若用于论文投稿，建议后续补误差分布图、时间序列对比图和案例图

## 9. 可复现性说明

当前已具备：

- SQL 抽取模板
- 动态 `target_cell` 导出模板
- 数据集构建脚本
- baseline 与 LSTM 训练脚本
- repeated-run 验证脚本
- ensemble holdout 评估脚本

关键路径：

- SQL 抽取：`sql/extraction/`
- 数据集构建：`src/data/build_training_dataset.py`
- 深度模型训练：`src/training/train_deep_models.py`
- repeated-run 验证：`src/training/run_holdout_stability.py`
- ensemble 评估：`src/training/evaluate_sequence_ensemble.py`

## 10. 建议的汇报口径

汇报时建议突出以下逻辑：

1. 先说明问题背景：PDU 级能耗预测不仅要拟合，还要验证能否迁移到未见对象。
2. 再说明方法：从同 cell 未见 PDU 开始，再扩到跨 cell 外部 holdout。
3. 最后强调结论：三轮外部验证中，残差 LSTM 全部稳定优于 `random_forest`。

最推荐的一句话总结是：

> 当前最佳残差 LSTM 不仅在开发集上有效，而且在三轮外部 holdout 验证中都稳定优于最强传统基线，说明模型已经学到具有可迁移性的能耗时序结构。
