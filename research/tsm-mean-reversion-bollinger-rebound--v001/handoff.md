# TSM 布林均值回歸 Study 交接

本次已完成一個新假說的預先登記、合成驗證與唯一 Development Trial。候選未達
「更多交易且壓力成本後績效改善」的事前條件，因此以 `fail` 結束，沒有凍結候選。

這次只把 v009 的固定跌幅加 RSI 跌深偵測改為布林位置：20 日中線、正負 2 個
母體標準差，收盤位置 %b 不高於 0.25。成交量比率 1.05、收盤高於前收、2% 風險
預算、4% 停損／停利、10 日持有與退場後 5 日冷卻保持固定。
布林公式參照[指標原作者說明](https://www.bollingerbands.com/bollinger-bands)，
止跌確認參考[使用原則](https://www.bollingerbands.com/bollinger-band-rules)。
本規格受既有 Development 筆記啟發，不能視為尚未見過資料的獨立驗證。

| 封存項目 | 已驗證內容 |
| --- | --- |
| Study ID | `tsm-mean-reversion-bollinger-rebound--v001` |
| 登記的候選 ID | `tsm-mr-bollinger-rebound-v001`；未成為 frozen candidate |
| Development | 2014–2018，25 筆；base 報酬 27.5895%、PF 3.76644；stress 報酬 20.9880%、PF 3.08780 |
| 未通過門檻 | 交易數 25 < 30；stress PF 3.08780 < 3.20558；stress 報酬 20.9880% 未高於 26.5904% |
| 已完成診斷 | 五個 signal year 分段、逐年剔除、3／5 筆交易區塊各 50,000 次重抽樣、63／126 日區塊各 10,000 次重抽樣、持倉 Low 估值 |
| 資料引用 | 公用 immutable source；僅解析 2013 warmup 與 2014–2018 Development；其他角色只保存 reference metadata |
| 正式歷史評估 | 未讀取、未執行；runner 只以合成 folds 與合成 CLI inputs 測試 |
| 正式結果資料夾 | 本 task 未開啟、搜尋、讀取或寫入 `historical-evaluation-artifacts/`；亦未存取 `.super-admin/` |
| 驗證 | 285 項測試通過，包含 16 項新測試；Ruff 通過；17 份 Source Bundle 檔案 digest 全數相符 |
| 測試 warnings | 8 個既有 workflow 合成測試的 NumPy infinity 分位數警告，測試仍通過；不是本次正式 Development 警告 |
| 建立前檢查 | authority 新 Study preflight、ID eligibility、`studyctl precreate` 全部通過；建立後 contract 與 synthetic guard 亦通過 |
| 最後檢查 | 帶固定 authority root 的 `studyctl freeze` 通過；狀態 `terminal-without-candidate`；唯一 warning 為候選凍結不適用 |
| Outcome | `fail`，`authority: none`；不是尚未產生結果的 setup failure |
| Authority root | `/Users/william/.codex/worktrees/994f/trading-2026-2/.authority` |
| Checkpoints | 6 個；與 6 個事件逐一相符 |

Source Bundle digest：
`10aed0264a5ee5e90dcd615c8cee046b8b7e0c3159ef82de17c3cc8dedb3f215`

最後事件 head：
`1118e4a15118b944b203947bcbf7433eabc91056f4baa796a62559708b25d00c`

最後 authority checkpoint digest：
`464ac4e946968c214641950a35f429ac128c39d570b1012c40eb92d3ca2daaa2`

Development 提前終止 evidence digest：
`d4cef0043ea5fd299f2e46b193ce109bc24cd7c4d2e89e02f34ac9ca89be5cdd`

[Development evidence](evidence/development.yml)、[預先登記](preregistration.yml)、
[實作契約](implementation-contract.yml)、[合成測試已驗證的歷史評估 runner](run_historical_evaluation.py)、
[最後 preflight](audit/terminal-state-preflight.yml)、[authority 驗證](audit/terminal-authority-check.yml)。

Authority checkpoints、研究檔與 writer 發布的 Study 記錄應一同納入本次本機 Git commit。
`studyctl all` 的候選凍結路徑不適用本次失敗 Study；沒有製造 selection evidence 或
candidate-frozen 事件。後續不得在這個 Study 上調參或接續正式歷史評估。
