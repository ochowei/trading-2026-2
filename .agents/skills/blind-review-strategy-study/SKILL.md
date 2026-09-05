---
name: blind-review-strategy-study
description: 檢討 strategy-forward-replication-research--v001 的指定 Study，只使用研究設計、程式與 Development 證據，避免開啟正式 Evaluation 結果。使用者要求盲檢討、封存式檢討或在下一輪調整前審查該 workflow 的 Study 時使用；任何其他 workflow 或路徑都拒絕。
---

# Strategy Study 封存式檢討

檢查策略為什麼在設計上可能不穩、Development 是否已經出現警訊，以及下一輪應優先驗證什麼，同時保留正式 Evaluation 作為一次性、未揭露的驗證資料。

## 硬性範圍

- 只接受 repository 內 `workflows/strategy-forward-replication-research--v001/studies/<study-id>/` 的直接子目錄。
- 使用者必須指定一個 Study ID 或 Study 目錄。不要自行挑選，也不要一次檢討多個 Study。
- 不接受其他 workflow、`research/` 目錄本身、任意外部路徑、symlink 逃逸或 Study 內的單一檔案。
- 超出範圍時立即停止；不要改用相似目錄、複製資料或提供範圍外的部分檢討。

## 開始前的停止條件

先檢查目前對話內容與本 task 已取得的資訊。如果已經出現目標 Study 的正式 Historical Evaluation 或 Terminal 結果，包括 pass/fail、交易、指標、年度表現或失敗 gate：

1. 不得進行封存式檢討，也不得假裝忽略已知結果。
2. 告知使用者目前 task 已受到結果資訊影響。
3. 請使用者在沒有帶入結果的新 task 重新呼叫本 skill。

只知道 Study ID、資料期間、session 清冊或內容 digest，不算策略結果曝光。

## 必做的範圍檢查

在讀取目標 Study 的任何檔案前，從 repository 根目錄執行：

```bash
python3 .agents/skills/blind-review-strategy-study/scripts/check_scope.py <study-id-or-path>
```

只有輸出 `eligible` 且 exit code 為 0 才能繼續。檢查失敗時直接回報拒絕原因，不要先列檔、搜尋內容或嘗試繞過檢查。

範圍通過後，完整閱讀 [references/review-method.md](references/review-method.md)，並嚴格遵守其中的讀取白名單、禁止清單、分析方法和報告格式。

## 執行原則

- 只做唯讀檢討；除下方「Review 結果輸出」允許的報告檔外，不得修改現有 Study、策略、evidence、事件鏈或建立新 Study。
- 不得使用網路、broker、外部市場資料或任何 connector 補充結果。
- 不得執行涵蓋 Historical Evaluation 或 quarantine 日期的回測；Development 前資料只能作為指標 warmup。
- 不得把設計弱點寫成已證明的 Evaluation 失敗原因，也不得保證建議能改善正式結果。
- 發現實作與 preregistration 不一致時，清楚區分「程式錯誤」與「策略假說本身可能無效」。
- 若必要檔案缺失或角色不明，停止該項分析並說明限制，不要擴大讀取範圍。

## Review 結果輸出

- 完成盲檢討後，可以把 review 結果寫入對應 Study 的 `reviews/` 子目錄：`workflows/strategy-forward-replication-research--v001/studies/<study-id>/reviews/`。
- Review 檔是補充性的封存筆記，不是正式 stage evidence、candidate、source、event、journal、terminal evidence 或 outcome；不得把它加入事件鏈、用來改寫任何 digest，或作為下一次盲檢討的證據來源。
- 這是唯一允許寫入 Study 目錄的例外。不得因此修改 `study.yml`、`manifests/`、`evidence/`、`events/`、`journals/`、策略程式或測試。
- 檔名必須使用不可變的明確編號或版本，例如 `reviews/001-first-review.md`；不得使用 `latest`、覆寫既有 review，或建立可變的 latest pointer。
- Review 內容仍須遵守本技能的盲檢討限制與報告格式，並明確聲明沒有讀取或使用正式 Historical Evaluation 或 Terminal 結果。

## 完成標準

報告必須用繁體中文，先說明實際問題與影響，再補必要技術細節。結尾列出本次實際讀取的檔案，並明確聲明沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果。
