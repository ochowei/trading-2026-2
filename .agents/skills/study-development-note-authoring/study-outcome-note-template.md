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

- Development 判定：`通過`／`未通過`／`不可判定`／`未完成`
- Provenance（來源可信狀態）：`verified-clean`／`known-contaminated`／`provenance-unknown`／`未確認`
- 前一個 Study：`<study-id>`／無
- 記錄日期：`<YYYY-MM-DD>`

## 結論

> 在 `<資料期間、成本與主要門檻>` 下，本 Study 的 Development 結果
> `<支持／不支持／無法判定>` 原始假說：`<一句話結論>`。

## 研究變更

- 研究問題或假說：`<這次想驗證什麼>`
- 相較上一個 Study 只改：`<主要變更>`
- 保持不變或比較基準：`<必要的對照>`

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base |  |  |  |  |  |
| Development / stress |  |  |  |  |  |

- 交易年度覆蓋：`<數量>`
- 失敗 gate：`<actual>` 對 `<threshold>`
- 未執行項目與原因：`<沒有則填無>`

## 主要發現

- 已確認：`<直接由 Development evidence 支持的事實>`
- 可能原因：`<推論及其證據強度>`
- 尚不能判斷：`<目前證據無法回答的問題>`

## 下一輪

- 建議處置：`<停止假說／修正可重現性問題／建立有限 follow-up Study>`
- 下一個 Study 只測：`<單一主要變更>`
- 成功／失敗條件：`<事前可判定的條件>`
- 不得沿用的問題：`<錯誤、未驗證假設或資料問題>`

## 證據連結

- Preregistration：`<repository-relative path>`
- Candidate definition：`<repository-relative path>`
- Development evidence：`<repository-relative path>`
- 程式／測試：`<repository-relative path>`
- 詳細盲檢討：`<repository-relative path／無>`
