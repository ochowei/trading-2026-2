# Study Development 成果卡格式

## 用途

每個 Study 使用一份，讓未來開發新 Study 時能快速回答：這次測了什麼、Development 結果如何、學到什麼，以及下一次只要測什麼。

這份成果卡只整理 Development 階段，不包含正式 Historical Evaluation 欄位。它是給人閱讀的摘要，不是正式 evidence，也不能取代 `study.yml`、Study Event 或其他權威紀錄。

## 輸出方式

- 預設直接在對話中輸出，不建立檔案。
- 使用者明確要求寫檔時，必須先提供完整目標檔案路徑。
- 同一個檔案可以累積不同 Study 的 Development 成果卡；若目標檔已有舊卡片，保留原文，在檔案末尾追加新的日期與 Study ID 紀錄。
- 若無法確認目標檔是 Development-only 的成果卡集合，不要覆寫。

## 長度規則

- 正文控制在約 300–600 字。
- 結果表與證據連結不計入字數。
- 最多 3 個主要發現、2 個限制、1 個下一輪方向。
- 逐筆交易、完整參數、執行 log 與詳細分析留在 Development evidence 或 review。

## 成果卡模板

# `<study-id>`：Study Development 成果卡

- 成果卡狀態：`complete`／`failed`／`partial`／`evidence-unavailable`／`indeterminate`
- Development gate：`通過`／`失敗`／`尚不能判斷`／`未執行或部分執行`
- Provenance（來源可信狀態）：`verified-clean`／`known-contaminated`／`provenance-unknown`／`未確認`
- candidate_freeze_status：`已完成`／`未完成`／`不適用`／`尚不能判斷`
- 前一個 Study：`<study-id>`／無
- 記錄日期：`<YYYY-MM-DD>`

## 結論

> 在 `<可確認的資料期間、成本與主要門檻>` 下，本成果卡狀態為
> `<complete／failed／partial／evidence-unavailable／indeterminate>`；對原始假說
> `<支持／不支持／無法判定>`：`<一句話結論；證據不可用時改寫為缺口、影響與限制>`。

## 研究變更

- 研究問題或假說：`<這次想驗證什麼>`
- 相較上一個 Study 只改：`<主要變更>`
- 保持不變或比較基準：`<必要的對照>`

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | `<已完成／未執行：原因／證據不可用：原因／尚不能判斷：原因>` |  |  |  |  |  |
| Development / stress | `<已完成／未執行：原因／證據不可用：原因／尚不能判斷：原因>` |  |  |  |  |  |

- 填寫規則：只有合法且完整的 evidence 才填數值；「未執行」與「證據不可用」必須分開並附原因；資料存在但不足以判定時寫「尚不能判斷」，不得填零、猜測或重建數值。
- 交易年度覆蓋：`<數量；不可用時寫「證據不可用：原因」>`
- 失敗 gate：`<actual 對 threshold；evidence 不可用時寫「停止分析：原因」>`
- 未執行項目與原因：`<沒有則填無>`

## 主要發現

- 已確認：`<直接由 Development evidence 支持的事實>`
- 可能原因：`<推論及其證據強度>`
- 尚不能判斷：`<目前證據無法回答的問題>`
- 已確認的證據缺口、影響與限制：`<沒有則填無；evidence 不可用時必填>`

## 下一輪

- 建議處置：`<停止假說／修正可重現性問題／修正證據產製或 validator 流程／建立有限 follow-up Study>`
- 下一個 Study 只測：`<單一主要變更>`
- 成功／失敗條件：`<事前可判定的條件>`
- 不得沿用的問題：`<錯誤、未驗證假設或資料問題>`

## 允許讀取的 repository-relative 來源

- Preregistration：`<repository-relative path>`
- Candidate definition：`<repository-relative path>`
- Development evidence：`<repository-relative path>`
- 程式／測試：`<repository-relative path>`
- 詳細盲檢討：`<repository-relative path／無>`
- 來源限制：只列 Development-only 白名單來源；不得列出或引用 Historical Evaluation、Terminal Evidence、正式交易明細、正式結果或 `historical-evaluation-artifacts/`。
