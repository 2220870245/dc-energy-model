# 最终汇报提纲

## 第 1 页：项目背景

- 数据中心能耗优化需要更细粒度、更可迁移的预测模型
- 公开数据可以支持方法验证，但难点在于 PDU 级样本构建和泛化证明

## 第 2 页：研究目标

- 构建 PDU 级能耗预测数据集
- 比较传统机器学习与时序深度学习
- 重点验证模型在未见 PDU、未见 cell 上是否仍有效

## 第 3 页：数据与样本构建

- 数据来源：ClusterData2019 + PowerData2019 + machine_to_pdu_mapping
- 样本粒度：PDU 5 分钟时间窗
- 标签：`measured_power_util`
- 特征：CPU 使用统计、实例数、时间特征、上一时刻功率等

## 第 4 页：模型方案

- baseline：`persistence`、`linear`、`ridge`、`random_forest`
- 深度模型：`LSTM`、`Transformer`
- 最终最佳路线：残差 LSTM

## 第 5 页：方法演进

- `v1`：初版开发集与 baseline
- `v2`：同 cell 未见 PDU holdout
- `v3`：跨 `cell=e` 外部验证
- `v4`：跨 `cell=b` 第三轮外部验证

## 第 6 页：第一轮外部验证结果

- `cell=f`
- holdout：`pdu17`, `pdu25`
- LSTM repeated-run mean 优于 `random_forest`

## 第 7 页：第二轮外部验证结果

- `cell=e`
- holdout：`pdu28`, `pdu29`
- LSTM repeated-run mean 继续优于 `random_forest`

## 第 8 页：第三轮外部验证结果

- `cell=b`
- holdout：`pdu15`
- LSTM repeated-run mean 再次优于 `random_forest`

## 第 9 页：三轮汇总

- 三轮外部验证全部 `3/3` 全胜
- ensemble 在三轮中都进一步改善 holdout 指标

## 第 10 页：结论

- 模型已学到可迁移结构
- 残差 LSTM 是当前主模型
- 项目已具备可复现、可汇报、可写论文的完整材料

## 第 11 页：局限与后续

- 仍可补误差分析和图表展示
- 仍可补更多 cell，但当前证据已足够强
- 后续重点应转为论文表达和结果呈现
