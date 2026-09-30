# TASK-037：v006 Draft 專案管理者驗收

- 日期：2026-09-30
- 驗收角色：專案管理者
- 執行者：`/root/task_037_v006_maintainer`，角色為 workflow 維護者
- 結論：指派的 Draft 交付符合驗收條件，TASK-037 移到 Done。v006 仍為 Draft；接受新 Study 的版本仍為 v005 Active。

## 已確認的實際問題

專案管理者獨立重跑 `tools/reproduce_v005_fixture.py`，重現 v005 原生訊號搜尋 8 組、持有／冷卻搜尋 160 組均無有效案例，兩項結果為預期的 `synthetic-fixture-invalid`。在 index=49、57、65，實際 SMA20=99.25、SMA50=99.70，候選原始／接受訊號為 0／0，同一資料的 Control 為 1／1；index=36 的 SMA50 尚未就緒。原生函式正確呼叫公開候選的 `DEFAULT_SPEC`／`BASE_COST`，價格案例不足以形成長期上升環境。

另一個缺口是原暖機推導與公開候選規格只有 25。含當日收盤的 SMA50 需要共 50 列資料，也就是訊號日前已有 49 列、最早 index=49 才能計算。v006 會核對這個最長要求，原 25 日設定仍被完整 precreate 拒絕。此結論使用公開來源與人造重建契約，沒有讀取 TASK-036 的私有準備文件；後續由 study 開發者依新派工重新準備一致的暖機與候選契約。

本次 PM 重現輸出：`/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task037-repro-rebl2t2i/reproduction.json`。這是可重建的開發暫存紀錄，不是正式研究結果。

## 交付內容審閱

- v006 自備規則、Schema（格式與必要欄位）、validator、writer、operations、tests、examples、reference 與診斷工具，共 119 個發布定義檔案。
- 產生器只建立人造 OHLCV（開高低收與成交量）；真實指標／回測函式決定原始與接受訊號。原生檢查另外從原始 Close 重算均線與完整訊號，沒有依任務名稱特判或注入成功答案。
- 覆蓋均線成立、不成立、相等、未就緒與剛就緒；同資料 Control、兩筆完整持有交易、冷卻第 4 步拒絕與第 5 步接受後次日開盤。錯誤均線、訊號、持有、冷卻、無效案例與不支援契約保留拒絕。
- 來源、契約、引擎、Workflow 與報告內容都有格式及數位指紋綁定；保留內嵌契約與相同內容的凍結副本相容性。新增 prepare 原生報告的完整整合驗證明列給 TASK-038。
- 審閱時指出的固定 Draft 斷言已改測隔離 Draft 副本；README 與 guide 使用發布狀態條件，避免建立 RC 後文件與測試失效。
- `IMPLEMENTATION-PLAN.md` 記錄實際開發結果及未執行項；`docs/workflow-lifecycle.md` 制定 v006 適用與啟用條件，未切換 Active／Superseded。

## PM 獨立檢查

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_regime.py \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_binding.py \
  workflows/strategy-forward-replication-research--v006/tests/test_draft_contracts.py -q
.venv/bin/ruff check workflows/strategy-forward-replication-research--v006
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  workflows/strategy-forward-replication-research--v006/operations/release_candidate.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  workflows/strategy-forward-replication-research--v006/tools/reproduce_v005_fixture.py \
  --repository-root .
```

| 檢查 | PM 實際結果 |
| --- | --- |
| 三個限定開發測試檔 | 66 passed、0 failed，10.06 秒，無 warnings，退出碼 0 |
| 整個 v006 Ruff | All checks passed，退出碼 0 |
| 唯讀定義 checker | definitions-passed，119 檔，退出碼 0；未使用 `--candidate` |
| Python 語法解析與定義檔空白／換行 | 60 份 Python 解析成功；定義檔無尾端空白，末尾換行存在 |
| v005 不可變內容 | manifest 的 102 份定義及 manifest／test report／release 三份發布檔案 SHA-256 全相符 |
| 固定 Policy | 四份 Policy 加四份 Policy Release，8／8 與 v005 原始 bytes 相同；Policy conformance 程式指紋相符 |
| 研究規格 | workflow.yml 除版本號外完整相同；資料區間、資格門檻、成本、風控與一次評估等規則保留 |
| 公開候選／Control | 無程式變更，與 v006 人造測試使用的兩份來源副本相同 |
| Draft 邊界 | 根層 manifest、test report、release、studies、runtime、evidence、authority 與 .authority 均不存在 |
| 看板 worker 變更 | PM 驗收前只有 TASK-037 內容變更，40 個任務 ID 與角色權限／格式規則保留 |
| 追蹤檔案空白檢查 | `git diff --check` 通過 |

PM 測試時與 subagent 最終交付的定義指紋相同：`be58a60f4165140fdf27c2a0d34ea1546f58c28897c6cdda6484edb504b3e34a`。這只用於本次 Draft 完整性核對，不能作為發布核准。

## 後續依賴

TASK-038 仍需由 workflow 執行者完成全部測試、prepare／runner preflight／隔離 consumer／create 與來源綁定整合、原有失敗恢復與 terminal 案例，形成 RC 後再重跑全部檢查。TASK-039 必須取得對最終三份數位指紋的獨立新核准才能啟用；TASK-040、TASK-041 的 v006 專屬 skills 仍待另行指派。

TASK-036 維持 Pending，等待 TASK-039 與 TASK-040 驗收 Done，再依原假說明確重新派工；新版本不會自動消除原 25 日暖機不足。此次未執行 Workflow／Study Lifecycle，未建立 RC、Release 或真實 Study，也未 commit。
