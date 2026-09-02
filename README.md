# trading-2026-2

Python 3.11 project managed with uv.

## 目前研究

- [`fxi-deep-pullback-no-closepos-cd7-v001`](research/fxi-deep-pullback-no-closepos-cd7-v001/README.md)：FXI 深度回檔、超賣、短期波動擴張與七-session cooldown 的可否證研究。2020--2024 Historical Evaluation 未通過，Study 已正式終止為 `fail`，假說遭否證。

## Study 前置檢查

`research/tools/studyctl.py` 是 Study 的唯讀 preflight（前置檢查）工具。它不會寫入 Event，也不會取代正式 writer；用途是把 copy-forward 的舊 Study 路徑、規格與程式不同步、指標尚未 ready 就被使用，以及 synthetic 邊界案例提早攔下來。

在建立或凍結 Study 前，從 repository 根目錄執行：

```bash
uv run python research/tools/studyctl.py --repository-root . all <study-id>
```

需要分開定位問題時，可執行 `identity`、`contract`、`synthetic` 或 `freeze`。輸出固定是 JSON；找到問題時 exit code 為 `1`，命令或環境無法執行時為 `2`。正式 freeze 前若要連同本機 authority checkpoint 一起核對，再加上 `--authority-root <path>`。

`contract` 需要一份明確的 implementation contract。可以放在 `research/<study-id>/implementation-contract.yml`（並把它加入 Source Bundle），內容至少要說清楚：

```yaml
schema_version: 1
engine:
  path: src/trading_2026_2/example_strategy.py
  spec_constant: DEFAULT_SPEC
  cost_constant: BASE_COST
indicator_contract:
  required_history_sessions: 25
  columns:
    sma: sma_20
    rsi: rsi_2
    volume_lead: prior_volume_spike_ratio
  sma:
    lookback: 20
    min_periods: 20
    not_ready: null
  rsi:
    length: 2
    formula: simple-rolling-mean
    min_periods: 2
    not_ready: null
    zero_gain_and_loss: 50
    zero_loss_only: 100
    zero_gain_only: 0
  volume_lead:
    volume_average_length: 20
    average_min_periods: 20
    prior_session_window: 5
    lead_min_periods: 5
    uses_prior_sessions_only: true
```

`freeze` 仍以 Workflow validator 和 guarded writer 為權威；terminal 且沒有 candidate 的 Study 會被標成不適用，不會因為沒有 candidate freeze 後才需要的 evidence 而誤報。
