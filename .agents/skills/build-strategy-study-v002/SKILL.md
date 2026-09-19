---
name: build-strategy-study-v002
description: 為 strategy-forward-replication-research--v002 建立或接續 Development Study，透過版本固定的 CLI 完成 prepare、授權後建立、Development 與 candidate freeze。僅 study 開發者使用；不執行 Historical Evaluation，不適用 v001。
---

以 repository 的既定角色工作，不自行切換角色。只有目前角色為 study 開發者且使用者要求開發 Study 時使用。讀取根目錄 AGENTS.md 與 `workflows/strategy-forward-replication-research--v002/reference/operations.md`；不要開啟正式 `historical-evaluation-artifacts/` 或管理者專屬目錄。

先確認 workflow version。v002 必須已有核准者建立的有效 release，正式研究不得使用 `--allow-draft`。保留 v001 舊 skill 與既有 Study；不要替換版本字串後直接套用舊命令。

## 研究與輸入

先把假說、候選 family、baseline、門檻、研究目標與停止條件寫清楚，再協助準備研究 bundle。新 `research/<id>/` 用不可覆寫建立方式；遇到已有目錄先辨識是否為同一工作，不覆蓋後重來。多 Trial 全部預先登記，各自的 inputs 必須被 prepare 或 Source Bundle 綁定。

請使用者補齊實際缺少的研究決策、核准或 provenance 事實；不得代填「已核准」、「verified-clean」或「未看過結果」。將已經提供的核准綁定目前 Study、preregistration 與 source 指紋，不重複索取相同核准。

## 正常操作

使用 repository 明確環境的 Python，命令固定為：

```text
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> prepare <id> --report <report.yml>
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> create-authorize --plan <create.yml> --report <report.yml>
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> development <id> --plan <trial.yml>
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> freeze <id> --plan <freeze.yml>
```

新 Study 預設使用 `<repo>/.authority/`；既有 Study 使用建立報告已綁定的位置，需指定時傳 `--authority-root`，不搬移或猜其他目錄。CLI 已包含必要驗證，正常流程不另外串 `studyctl all` 或 authority checker。

每個預先登記的 Trial 各呼叫一次 `development`。CLI 會保存 candidate 與 baseline、產生 publication manifest、登錄 Trial；不要手工拆 YAML、計算結果欄位或拼接 writer 事件。CLI exit code 0 只表示操作成功；另讀取 `assessment` 的正式 gates、research targets、evidence validity 與 candidate freeze eligibility。

`freeze` 已先做完整唯讀 readiness，接著依序發布 registry／provenance／freeze。只有診斷時才另用 `freeze-readiness <id> --plan <freeze.yml>`，不用人工先發布前兩事件。

## 中斷與交接

先讀 CLI 的 error code、progress 與 next_action；用 `status <id>` 查看 Development 範圍，用 `resume <id>` 接續同一 operation。不要刪鎖檔、換 plan、刪 Study 或重新跑 runner 來修復中斷。已有 started 記錄但缺輸出時，先確認實際 exposure 與可恢復性；缺 evidence 不代表沒看過真實資料。

合法的無交易、gate fail 或 target fail 不應以改參數／重跑同一 Trial 消除。保留完整 family，依預先登記規則使用 `terminate <id> --plan <terminal.yml>`，或將缺少的決策交回使用者。

到 candidate-frozen 即停止。交接 Study ID、workflow version、authority root、head、候選與待核准項目；不得自動呼叫 `historical-evaluation`。status 若顯示後續階段未檢視，不宣稱完整語意驗證或 blind review 已合格。
