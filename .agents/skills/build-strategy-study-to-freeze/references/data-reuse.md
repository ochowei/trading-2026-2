# 資料重用與 shared reference 規格

這份規格只處理「資料檔案怎麼重用與綁定」，不授權在 candidate freeze 前讀取
Historical Evaluation、quarantine 或 replay 的策略結果。

## reference 的定義

`reference` 是在 acquisition/lineage manifest 內保存 repository-relative 的 source path、內容
SHA-256、品質報告與 role view，讓新的 Study 讀取同一份既有檔案。它不是 symlink，也不是外部 URL、浮動的
`latest.csv` 或只記錄檔名而不記錄 digest。

workflow 的 `data-snapshot-set.yml` 另有嚴格的 `data-snapshot.schema.yml`。因此下列
`data_source` 區塊是 acquisition/lineage manifest 的語意示例，不得直接新增到
`data-snapshot-set.yml` 的 role entry；該 role entry 必須繼續只保存 workflow 要求的固定欄位，
包括該 role 實際 view 的 `sessions` 與 `data_digest`。

直接引用公用 role snapshot 時，可使用下列語意：

```yaml
data_source:
  digest: <source-csv-sha256>
  kind: shared-reference
  path: research/market-data/yahoo/<content-addressed-role-snapshot>.csv
  quality_path: research/market-data/yahoo/<matching-quality-report>.yml
  view:
    kind: direct-file
```

如果公用資料是一份完整快照，可由多個 role 引用同一 source，再各自指定不重疊的日期 view：

```yaml
data_source:
  digest: <full-source-csv-sha256>
  kind: shared-reference
  path: research/market-data/yahoo/<content-addressed-full-snapshot>.csv
  quality_path: research/market-data/yahoo/<matching-quality-report>.yml
  view:
    calendar: XNYS
    end_inclusive: '2018-12-31'
    kind: date-range
    start_inclusive: '2014-01-01'
    view_digest: <canonical-role-view-sha256>
```

既有 workflow 的 `data_digest` 仍須保留在 role entry：直接檔案時它等於 source digest；
date-range view 時它等於依 repository 的固定 CSV 序列化規則
（`Date,Open,High,Low,Close,Volume`、UTF-8、LF）從 source 選出該 role 後的 view digest。
Reference lineage manifest 的 `view_digest` 必須與該 role 的 `data_digest` 對得上。若目前
runner 或 validator 不能驗證 view digest，不得假裝支援 date-range reference；應先建立公用
role snapshot，或使用物化副本並記錄原因。

## 選擇順序

每次建立 Study 都依以下順序尋找資料：

1. `research/market-data/<provider>/` 的公用 immutable snapshot；
2. 舊 Study 的內容定址 snapshot，僅在沒有相容公用檔案時使用；若會被多個 Study 重用，先
   依原始 digest 不可覆寫地登錄到公用資料目錄；
3. 使用共用下載工具把缺少的區間下載到公用資料目錄，完成品質檢查後 reference 新檔案；
4. 只有 consumer 確實無法解析 reference 時，才把檔案物化到新 Study，並記錄
   `source_path`、`source_digest`、`materialization_reason` 與物化時間。

資料相容性必須同時符合 ticker、日期範圍或可驗證 view、provider、calendar、頻率、調整方式、
欄位、品質狀態、session inventory 與實際 digest。任何一項不符都要換來源或重新下載，不能
靜默拼接不同 snapshot。

## 建立與驗證 checklist

- shared path 位於 repository 內，沒有絕對路徑、外部 URL 或浮動檔名。
- source CSV 與 quality report 都存在；source digest 與實際 bytes 相符。
- workflow `data-snapshot-set.yml` 的五個 role entry 仍通過原 schema；其 session inventory
  不重疊且符合 XNYS。
- acquisition/lineage manifest 對每個 role 保存 source path、source digest、品質報告、view
  範圍與 view digest，且與 role entry 的 `data_digest` 一致。
- 若使用 date-range view，view digest 是由固定序列化重新計算，不是 source digest 的別名。
- Development inputs 與 runner 都讀取同一份 reference/view；不能由未記錄的 wrapper 偷換成
  Study-local 副本。
- 若不得不物化，Study 仍保存原始 reference lineage，並在 provenance 說明為何不能直接引用。
- candidate freeze 綁定 snapshot set manifest digest；未來若公用檔案內容變動，content digest
  drift 必須使驗證失敗，而不是自動跟隨新內容。
