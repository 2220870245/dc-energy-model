# Holdout Generalization Summary

## Setup

- development dataset: `data/processed/v2_expanded_dev`
- holdout dataset: `data/processed/v2_holdout_pdu/full.parquet`
- development PDUs: `pdu20, pdu21, pdu22, pdu23, pdu24`
- unseen holdout PDUs: `pdu17, pdu25`
- label: `measured_power_util`

## Development-Test Performance

| model | dev test_mae | dev test_rmse | dev test_r2 |
|---|---:|---:|---:|
| `persistence` | `0.0021626373626373635` | `0.002902064441389616` | `0.9952788859310215` |
| `random_forest` | `0.005244745450727983` | `0.008794527925699442` | `0.956643376358224` |
| `lstm_residual_h96_wd1e3` | `0.0021204082295298576` | `0.0027021152175776154` | `0.99590703404911` |

## Unseen-PDU Holdout Performance

| model | holdout_mae | holdout_rmse | holdout_r2 |
|---|---:|---:|---:|
| `persistence` | `0.004128091872791518` | `0.027605611530735298` | `0.6575220054753952` |
| `random_forest` | `0.006086088313678801` | `0.008717445055781486` | `0.9658479824650014` |
| `lstm_residual_h96_wd1e3` | `0.003698076121509075` | `0.005011821217281058` | `0.9886599759530615` |

## Interpretation

- On the internal development test split, both `persistence` and the tuned residual LSTM are very strong.
- On the unseen-PDU holdout, `persistence` degrades sharply, especially on RMSE and R2.
- `random_forest` generalizes much better than `persistence`, but still trails the tuned residual LSTM.
- The current best result is the tuned residual LSTM, which keeps `holdout_r2` near `0.989` and clearly beats the strongest baseline on all main holdout metrics.

## Current Conclusion

- Inside the expanded development set, the deep model is competitive with the strongest simple baselines.
- On unseen PDUs, the tuned residual LSTM is now the clearest winner.
- This is the strongest evidence so far that the sequence model is learning transferable structure rather than only fitting seen PDUs.
