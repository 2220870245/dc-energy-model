# 导师汇报摘要

## 项目一句话

基于 Google 公开集群与电力数据，我构建了 PDU 级能耗预测数据集，并验证了残差 LSTM 在三轮外部 holdout 中都稳定优于 `random_forest`。

## 已完成内容

- 完成 BigQuery 抽取、PDU 映射、特征构建和质量检查
- 完成 baseline、LSTM、Transformer 训练与对比
- 完成三轮外部验证：
  - `cell=f` 未见 PDU holdout
  - `cell=e` 跨 cell holdout
  - `cell=b` 第三轮外部 holdout

## 最关键结果

三轮外部验证中，LSTM 对 `random_forest` 的 holdout 结果均为 `3/3` 全胜。

| round | LSTM holdout mean MAE | RF holdout mean MAE |
|---|---:|---:|
| `v2` | `0.0037103` | `0.0060611` |
| `v3` | `0.0032976` | `0.0041825` |
| `v4` | `0.0030404` | `0.0038786` |

## 当前主结论

- 残差 LSTM 已经不是单次偶然优于 baseline，而是在重复实验下稳定胜出。
- 模型优势不仅存在于原始 `cell=f`，还在 `cell=e` 和 `cell=b` 的外部验证中重复出现。
- 这说明模型学到的是可迁移结构，而不是只记住训练样本分布。

## 推荐模型

- 单模型推荐：残差 LSTM
- 展示结果推荐：3-member residual LSTM ensemble

## 现阶段价值

当前结果已经足以支撑：

- 阶段性项目汇报
- 论文初稿中的实验主线
- 答辩中“模型泛化能力”这一核心论点

## 后续建议

- 优先把当前结果整理成论文图表和答辩材料
- 如需继续扩展，可补误差可视化和案例分析
- 除非有新的研究问题，否则不建议继续无上限扩更多 cell
