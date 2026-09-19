---
name: blind-review-strategy-study-v002
description: 盲檢討 strategy-forward-replication-research--v002 的單一 Study，使用研究設計、程式及各 Trial 的 Development candidate／baseline 證據。僅超級管理者或 study 開發者使用，不讀正式 Evaluation／Terminal 結果，不適用 v001。
---

# v002 Study 盲檢討

只回答設計風險、實作一致性、Development 警訊及下一輪可否證方向。這是唯讀研究檢討，不建立 Study、不重跑 runner、不修改策略或正式 artifacts。

## 角色、範圍與盲性

目前對話角色必須是 **超級管理者** 或 **study 開發者**，不自行切換。使用者須指定唯一 Study ID 或 repository 內 `workflows/strategy-forward-replication-research--v002/studies/<id>/` 的直接目錄。拒絕其他版本、research 目錄本身、外部路徑、單一檔案與 symlink；不要自行挑選或比較其他 Study。

先檢查本次對話已取得的資訊。若目標 Study 的正式 Evaluation 結果或帶 outcome 的 Terminal 內容已曝光，停止盲檢討，說明應在未帶入結果的新 task 進行；不能假裝忽略已知結果。只有「已 terminal」、階段名稱、日期或 digest 不代表結果曝光。不得為判定曝光而開啟結果；若 exposure 事實不明，先釐清，不宣稱已確認未曝光。

## 唯讀入口

先讀根目錄 AGENTS.md，確認角色及唯一 Study，再執行本 skill 的工具：

```bash
python .agents/skills/blind-review-strategy-study-v002/scripts/check_development.py <study-id-or-path> --repository-root <repo> --role 'study 開發者'
```

超級管理者使用對應 role 值；role 參數不是身分認證。已明確曝光時可用 `--outcome-exposed`，或兩種個別曝光旗標；工具在讀任何 Study 內容前拒絕。exit code 2 為範圍／盲性拒絕；exit code 0 表示可在指定範圍檢討，**不代表 evidence、候選資格或整條事件鏈通過**。

工具不讀 study.yml、events、journals、operations 或正式結果 store。它使用 v002 的 envelope validator 與 raw evidence 重算，依 preregistered family 定位每個 Trial 的 publication、candidate、baseline、inputs，檢查內容指紋及 Study／規格綁定。它只驗證 Development artifacts 彼此一致，不驗證 authority／事件登錄；不能把結果說成完整 Study 驗證或 candidate 已凍結。

不要改用 `operations/cli.py status`、完整 `validate`、writer 或 v001 status tool 完成本次盲讀：即使只輸出 Development 摘要，完整事件解析仍不屬於本技能的讀取白名單。

## 讀取白名單

- 指定 Study 的 `manifests/preregistration.yml`、`source-bundle.yml`、`prepare-report.yml`（核對 frozen settings）、存在時的 candidate-definition、qualification-spec、implementation-contract、snapshot metadata；不可沿 metadata 開啟 Evaluation／quarantine／full 價格資料。
- `evidence/trials/<registered-trial-id>/{publication,candidate,baseline,inputs}.yml`，以工具的逐 Trial 驗證結果決定能否分析數值。不可退回固定 `evidence/development.yml`，也不使用 `/tmp`、runtime 或相似研究補缺口。
- 必要的 Development authorization、provenance、selection：只作補充，沒有完整鏈驗證就不能宣稱事件已完成或 provenance 已被正式接受。
- Source Bundle 明確綁定、位於 `src/`、`tests/` 或 `research/<id>/` 的研究規格與 Development 程式。先核對路徑不含 symlink／逃逸，再核對 digest；規格若只由 prepare settings 綁定，按該指紋核對。缺件或漂移時停止該項結論，不擴大搜尋。
- 必要的 v002 workflow／rules／schemas／validator 與本技能工具程式。

禁止讀取、搜尋、雜湊或複製 `historical-evaluation-artifacts/`，以及任何位置的正式 Evaluation／Terminal 結果、Study／research README、study.yml、events、journals、operations、舊 review／成果卡或全域搜尋／Git 歷史輸出。Source Bundle 中的路徑不是任意讀取授權。不使用網路、connector、broker 或新回測補充資料。

## 檢討與輸出

1. 把假說對照訊號、setup／trigger、進出場、成本、部位、cooldown、warmup 與日期切割；區分已確認實作錯誤與尚未驗證的經濟假說。
2. 逐 Trial 整理已驗證 candidate／baseline 的 base／stress、交易覆蓋、年度集中、leave-one-year-out 與既有 bootstrap。保留完整 family，baseline 不列入候選排名，不自行擴張參數搜尋。
3. 分開呈現 formal gates、research targets、evidence validity、candidate freeze eligibility 與 blind review exposure。target-only fail 不改稱 formal fail；無交易可能是合法 evidence，但統計不可估計且不合格。實際 candidate freeze status 預設「尚不能判斷」。
4. 缺少／損壞 evidence 不取消整個盲檢討：只停止該 Trial 的數值與 gate 結論，保留可支持的設計／程式分析，明示 unavailable 及原因；不把缺 evidence 解讀成沒看過資料或 Evaluation 未執行。
5. 以繁體中文交付範圍、最重要問題與影響、證據強度、限制、下一輪可否證建議及讀取紀錄。列出實際讀取與讀取失敗的檔案，聲明沒有使用正式 Evaluation／Terminal 結果；不得推測它們的成敗原因。

可在對話交付，或新增該 Study 的 `reviews/<明確編號>-<名稱>.md`。新檔必須不存在，拒絕 symlink；不得覆寫舊 review、建立 latest pointer、修改事件／digest 或把 review 當正式 evidence。建議只供新 Study 預先登記，不回寫本 Study。
