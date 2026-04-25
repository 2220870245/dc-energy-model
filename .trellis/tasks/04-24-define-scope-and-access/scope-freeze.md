# 建模范围冻结说明

## 1. 任务目标

本项目聚焦于使用 Google cluster-data 中的 `ClusterData2019` 与 `PowerData2019`，建立面向 `PDU x 时间窗` 的归一化电力利用率预测模型。

主任务定义：
- 输入：过去一段时间窗内的 workload、resource usage、machine 属性与历史 power utilization 特征
- 输出：下一时间窗的 power utilization

数学定义：
- 单步预测：`P_{t+1} = g(X_{t-k+1:t})`

## 2. 标签冻结

主标签：
- `measured_power_util`

辅助标签：
- `production_power_util`

标签策略：
- 所有正式 benchmark 与主模型训练默认使用 `measured_power_util`
- `production_power_util` 只用于对照实验、业务负载剥离分析或补充实验

冻结结论：
- 未经明确变更，不切换主标签

## 3. 样本粒度冻结

样本主键：
- `cell`
- `pdu`
- `window_start`
- `window_end`

样本粒度：
- `PDU x 时间窗`

默认时间粒度：
- 与 power trace 原始时间粒度保持一致后再决定是否重采样
- 第一版实验默认采用 5 分钟窗口

历史窗口与预测跨度：
- 历史窗口长度 `k` 初始设为 12
- 预测步长 `h` 初始设为 1
- 即默认利用过去 12 个窗口预测下一个窗口

后续允许调参，但必须记录为实验变量，不得改变样本定义。

## 4. 数据切分冻结

推荐切分方式：
- 按时间顺序切分，禁止随机打散

默认切分：
- 训练集：前 70%
- 验证集：中间 15%
- 测试集：后 15%

约束：
- 不允许未来信息泄漏到过去
- 同一次实验的所有模型必须使用相同切分

## 5. 输入特征冻结

第一版保留特征：
- CPU 使用：平均、最大、P90、P99
- 内存使用：assigned memory、page cache、内存占用率
- 微结构代理：CPI、MAI
- 工作负载强度：实例数、作业数、优先级分布
- 事件计数：submit、schedule、finish、evict
- 机器侧特征：机器数、平台类型分布、容量总和
- 时间特征：小时、星期、周期编码
- 历史标签：过去窗口的 `measured_power_util`

第一版不纳入：
- 冷却、PUE、CRAC、环境温度
- 绝对 kW 重建
- GPU 细粒度功耗

## 6. 评价指标冻结

主指标：
- MAE
- RMSE

辅助指标：
- MAPE 或 sMAPE
- R2
- 峰值误差
- 高分位误差

验收原则：
- 深度学习模型必须至少稳定优于持久性预测与线性回归
- 最终是否采用深度学习，以其相对最强 baseline 的提升为准

## 7. 模型路线冻结

允许的建模顺序：
1. 持久性预测、滑动平均
2. 线性回归、Ridge、Lasso
3. XGBoost 或 LightGBM
4. LSTM 或 GRU
5. Transformer、TCN 或同类时序模型

约束：
- 在 baseline 未建立前，不进入深度学习结论阶段
- 在数据集版本未冻结前，不进入正式 benchmark

## 8. 非目标冻结

本项目当前不解决：
- 园区级总能耗建模
- 冷却链路与设施能耗建模
- 芯片级、DRAM 通道级、磁盘级微结构能耗建模
- 面向实时生产部署的在线推理系统

## 9. 当前 Gate 1 结论

已冻结内容：
- 主标签：`measured_power_util`
- 辅助标签：`production_power_util`
- 样本粒度：`PDU x 5分钟时间窗`
- 默认历史窗口：12
- 默认预测步长：1
- 默认切分：70/15/15 时间顺序切分

Gate 1 状态：
- 已完成文档冻结，等待 BigQuery 访问验证后进入 Gate 2
