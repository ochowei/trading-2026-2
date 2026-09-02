# 共用市場資料

這裡保存可供多個 Study 參考的、由 Yahoo Finance 下載的日線市場資料。每份 CSV
的檔名都包含資料內容的 SHA-256，沒有會隨時間變動的 `latest.csv`；新的 Study
應記錄它實際引用的完整檔名與 digest。

下載工具位於 [`research/tools/download_market_data.py`](../tools/download_market_data.py)。
它把 `--start` 和 `--end` 視為含頭含尾日期，預設使用 XNYS 交易所日曆，並在保存
前檢查：

- 交易日是否缺漏、重複或排序錯誤。
- OHLC 是否有缺值、非有限值、非正價格、負成交量。
- `Low <= Open/Close <= High` 與 `Low <= High` 是否成立。

只有不超過 `1e-10` 的浮點 round-off 可以自動校正；較大的價格關係錯誤會拒絕
保存。每份資料旁邊的 `.quality.yml` 會留下檢查結果。

例如下載 TSM 的完整區間：

```bash
uv run python research/tools/download_market_data.py \
  --ticker TSM \
  --start 2013-01-02 \
  --end 2025-12-31
```

目前已保存的 TSM 共用快照是 [`TSM-2013-01-02-2025-12-31-auto-adjust--sha256-50178c8f2965b76b37f60e906901d2ec06e997e3c647df6b885bb99464788e95.csv`](yahoo/TSM-2013-01-02-2025-12-31-auto-adjust--sha256-50178c8f2965b76b37f60e906901d2ec06e997e3c647df6b885bb99464788e95.csv)，共有 3,270 個 XNYS session；品質報告在同目錄的 [`.quality.yml`](yahoo/TSM-2013-01-02-2025-12-31-auto-adjust--sha256-50178c8f2965b76b37f60e906901d2ec06e997e3c647df6b885bb99464788e95.quality.yml)。檢查結果為通過，High 和 Low 都沒有需要校正的資料。

這份共用快照是原始完整區間。`strategy-forward-replication-research--v001` 的正式 Study
應優先 reference 這類公用 immutable snapshot，不要為每個 Study 再複製一份相同 CSV。Study
仍須在 workflow 的 `data-snapshot-set.yml` 內建立 `warmup-only`、`development`、`quarantine`、
`historical-evaluation` 和 `retrospective-execution-replay` 五個不重疊的 role entry，並維持
原本 `data-snapshot.schema.yml` 的固定欄位與 `data_digest`。source path、source digest、品質
報告、XNYS session inventory 與 view digest 應另記在 Study 的 acquisition/lineage manifest。
若 runner
不能解析完整快照的日期 view，才先在公用資料目錄建立不可覆寫的 role snapshot；Study-local
副本只作為相容性 fallback。不能在正式執行時重新連線 Yahoo 或自動跟隨會改變的資料。
