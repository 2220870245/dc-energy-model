# BigQuery 访问与成本检查清单

## 1. 目标

在进入数据抽取任务前，确认可以稳定访问 Google cluster-data 的相关数据表，并控制查询和导出成本。

## 2. 必查项

### GCP 与计费
- [ ] 已创建 GCP Project
- [ ] 已启用 Billing
- [ ] 已启用 BigQuery API
- [ ] 已确认当前账号拥有查询权限

### 数据访问
- [ ] 可访问 `ClusterData2019`
- [ ] 可访问 `PowerData2019`
- [ ] 可访问 `machine_to_pdu_mapping`
- [ ] 可执行最小样例查询并返回结果

### 本地与导出
- [ ] 已确定结果导出路径
- [ ] 已确定导出格式优先为 Parquet
- [ ] 已确认本地可读取导出结果
- [ ] 已估算样本导出体量

## 3. 最小查询策略

第一轮查询原则：
- 单个 cell
- 少量 PDU
- 短时间范围
- 只选必要字段

禁止行为：
- 未估算扫描量时做全表查询
- 未验证字段含义时直接导出大范围数据
- 在标签未冻结前抽取正式训练集

## 4. 成本控制策略

建议措施：
- 先写 `LIMIT` 与时间过滤版本查询
- 先做字段裁剪，再做时间扩展
- 优先生成中间聚合表，而不是反复扫原始大表
- 导出前统计样本数、列数和预估大小
- 为每次正式查询记录时间范围、字段范围与扫描量

## 5. 建议验证顺序

### Gate 2-A: 权限验证
验收条件：
- 可以运行最小 power trace 查询
- 可以运行最小 instance usage 查询
- 可以看到 machine 到 PDU 的映射结果

### Gate 2-B: 对齐验证
验收条件：
- 能确认 power 表时间字段
- 能确认 usage 表时间字段
- 能写出最小时间对齐查询思路

### Gate 2-C: 成本验证
验收条件：
- 有一份小规模查询的扫描量记录
- 有导出格式和落地路径方案
- 有单次查询上限的执行约束

## 6. 推荐导出规范

输出目录建议：
- `data/raw/bigquery_exports/`
- `data/interim/`
- `data/processed/`

文件命名建议：
- `cell_<id>_pdu_sample_<yyyymmdd>.parquet`
- `instance_usage_joined_<yyyymmdd>.parquet`
- `pdu_training_table_v1.parquet`

## 7. 当前状态

当前状态：
- Gate 1 已完成
- Gate 2 未执行

阻塞项：
- 尚未在本机确认 GCP 与 BigQuery 实际访问能力
- 尚未记录第一条样例查询的扫描量与导出路径
