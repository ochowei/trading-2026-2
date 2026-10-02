# TASK-038 v006 Release Candidate 驗收紀錄

- 日期：2026-10-01（Asia/Taipei）
- 驗收角色：專案管理者
- 狀態：最終 Release Candidate（RC，等待獨立發布核准的候選版）驗收通過；TASK-037 重開修正與 TASK-038 交付符合驗收條件。
- 執行者：`/root/task_038_v006_executor`，workflow 執行者。
- 修正者：`/root/task_037_v006_maintainer`，workflow 維護者；只調整未發布定義，完整流程由執行者驗證。

## 實際問題與處理

完整發布驗證發現舊測試來源只有佔位契約與自行填入的成功旗標，無法通過新版真正的建 Study 前檢查。已將共用測試來源改成完整契約、同一真實回測引擎與執行器，經 prepare 取得與來源相符的原生報告；資格、事前登記、來源、引擎、程序及 Trial 的指紋一起重新綁定。原生 guard（建立前的拒絕檢查）保留。

另修正 macOS 暫存根目錄別名解析不一致、README 測試依賴舊句及固定段落、原人造價格不能形成實際獲利交易的問題。路徑修正有根外 symlink 拒絕案例；人造價格按真實引擎與原門檻重算，不更改 Policy 或計算公式。

新增 SMA 完整流程測試：同資料候選／公開 v009 Control 實際回測；prepare、兩個隔離 Development consumer、外層 create、Trial 發布與凍結來源副本。測試用正式 baseline 是候選引擎自己的 BASELINE_SPEC，保留 regime 並關閉兩個訊號條件，不代表 TASK-036 的原訂 v009 baseline 管線已完成。原 25 日暖機仍在 runner 與發布前被拒絕。

新測試最初把觀察次數寫少：每個 consumer 有建報告一次及三層建立前驗報，共四次；外層 create 也在三個入口重算。已按實際入口修正精確次數與各 consumer 報告一致性，且每次確認尚無真正的事件檔；沒有降低檢查或刪除觀察。

## 完整失敗與中止歷史

| 階段 | 真實結果 | 後續處理 |
| --- | --- | --- |
| 原 TASK-037 開發驗收 | 原三檔 66 passed，無警告 | 原驗收紀錄保留，不能當成完整發布驗證 |
| TASK-038 首輪完整 Draft | 108 passed／83 failed／15 warnings，169.51 秒，exit 1 | 交原維護者修正，共用來源、綁定、README、路徑問題 |
| 修正後限定開發 | 先 74 passed／1 failed，後 75 passed，15.61 秒、0 warnings | 修正真實引擎人造價格，凍結 122 個定義 |
| 第二輪序列完整 Draft | 60 個通過進度後主動中止，856.975 秒，pytest -15／wrapper 241，無完整 JUnit | 為節省逐案等待改用已安裝的 pytest-xdist 四個獨立進程；不能算全套成功 |
| 第二輪並行完整 Draft | 206 passed／1 failed／211 warnings，635.30 秒，exit 1 | 精確修正新測試的觀察次數，保留三層原生檢查 |
| 再修正限定開發 | 75 passed，15.54 秒、0 warnings；Ruff／122 檔 checker／63 AST 通過 | 新凍結定義交原執行者重新完整驗證 |
| 第三輪 SMA 單案診斷 | 1 passed／3 warnings，17.56 秒，exit 0 | 後半 create、Trial、來源副本及改動拒絕已實際執行；尚需完整 Draft 與 RC 驗證 |
| 第三輪完整 Draft | 207 passed／0 failed／0 errors／0 skipped／212 warnings，629.83 秒，exit 0 | 122 個定義及保護基準再次相符後形成 RC |
| 第三輪完整 RC，workflow 執行者 | 207 passed／0 failed／0 errors／0 skipped／212 warnings，822.51 秒，exit 0 | manifest 與初版 report 存在且內容固定，完整重跑成功 |
| PM 獨立完整 RC | 207 passed／0 failed／0 errors／0 skipped／212 warnings，801.75 秒，exit 0 | 使用另一個外部暫存目錄，對同一份固定 RC 獨立驗收 |

首輪 log SHA-256：`509f593bb5ad19f45940261343f75b689b66d61873ebc249c96c52bfaedfdf40`。

第二輪並行 log SHA-256：`e023704c12b5664c20ef9b4294e5048ff92c2660f166a344d7acb75ac4b5e430`；JUnit SHA-256：`82b2f96ab8a2e90a06db58a4347359d650799842a95af23cdd36485a40c899b0`。

第三輪 SMA 單案 log SHA-256：`d32f03c8bf7a5a928f3294275a21e7f7a28df1c71238423ca0840da73f7dfa71`。

外部合成日誌目錄：`/private/tmp/task038-v006-release-20261001-1ib8gl60/`。真實 warnings 保留，不抑制；第二輪 211 個皆為 NumPy 的 `invalid value encountered in subtract`，完整結果以各階段最後摘要為準。

## 當前定義與保護基準

最新凍結 Workflow 指紋：`e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`，122 個發布定義。

PM 已獨立重算兩輪凍結指紋並核對 Draft 路徑狀態；已逐項核對 v005 的 102 個 manifest 指名檔案、三份發布檔案、八份 Policy／Policy Release、兩個公開引擎與初始基準一致。只讀指定公開定義，不遍歷舊 Study、authority 或正式結果庫。

v005 Workflow 指紋：`2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`；manifest：`6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`；test report：`3120c4edf745f3b2ae8701a7d37ac54737180a15b204bfcea46bb6619b3872dc`；release：`92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`。

## 最終完整證據

Draft 通過後才建立 manifest 與初版 test report。執行者與 PM 使用不同外部暫存目錄，對相同的固定候選檔案完整驗證；測試當時 manifest 指紋為下表最終值，初版 report 指紋為 `800fd8eeaa172b65dee37871dc887662e25fe6bf6caedd82c70dceb34d069518`。兩套 RC 結果收齊後，才補入實際結果並定稿報告；發布定義與 manifest 沒有變動。初版 report 指紋只記錄測試時的內容，發布核准須使用下表的最終 report 指紋。

PM 逐案比較三份完整 JUnit（機器可讀的測試結果）：Draft、執行者 RC、PM RC 均為相同 13 個測試檔、207 個唯一案例，全部成功。涵蓋 SMA 真正 prepare／consumer／create／Trial、報告缺失／替換／造假拒絕、凍結來源副本與漂移拒絕、原 25 日暖機不足拒絕、單一 CSV、26 個故障恢復案例，以及 1／2／3／16 資產 Development、2／3／16 資產到 terminal 和超額拒絕；沒有宣稱逐一執行 4 至 15 資產的完整流程。

每份完整 suite 均有 212 個 NumPy `invalid value encountered in subtract` 數值運算警告，已如實保存，沒有抑制警告或修改計算公式與門檻。正式研究仍須另依自身資料驗證證據有效性；這些測試只使用專案外的人造資料。

| 完整階段 | 日誌 SHA-256 | JUnit SHA-256 |
| --- | --- | --- |
| 第三輪 Draft | `07731c00f357c4d38992d5cf2db49ac0472c800f62d3154aa5dd6d8d93824d1a` | `f978f42e82b99ccb61bb66e408531edfaf42e04f1095f900f1e13570f0ce1123` |
| 執行者 RC | `5e93d2aed74c537d0aa1e3079ce9b281bb4a664882c24c0fbff503b96286c817` | `9bc8211db76e7abc0a49bc5736c8f0b9c6c55305375cc689ead3f9029523e747` |
| PM RC | `5519f2cc676f3150a1a7208920537f16ac3a32cce5fe3d34bfcc29676058552a` | `2d172df808fa7dd87590fe509beacee3c396f0f8938d39b9ce6a52f4f09c4b50` |

PM 完整 suite 的實際命令如下，wrapper 記錄退出碼 0、801.916 秒；pytest 自身記錄 801.75 秒。執行者命令與各階段結果保存於最終 test report。

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  workflows/strategy-forward-replication-research--v006/tests -n 4 -q --tb=long \
  --basetemp=/private/tmp/task038-v006-pm-acceptance-20261001-VjNLIvJU/pytest-tmp \
  --junitxml=/private/tmp/task038-v006-pm-acceptance-20261001-VjNLIvJU/pm-rc-pytest-junit.xml \
  -o cache_dir=/private/tmp/task038-v006-pm-acceptance-20261001-VjNLIvJU/pytest-cache
```

PM 日誌目錄：`/private/tmp/task038-v006-pm-acceptance-20261001-VjNLIvJU/`。`pm-three-suite-crosscheck.json` 記錄三套逐案比較；`pm-final-report-log-audit.json` 記錄最終報告十項檢查的日誌指紋與退出碼逐一相符。

## 最終驗收與後續

| 最終核准必須使用的內容 | SHA-256 數位指紋 |
| --- | --- |
| Workflow，122 個發布定義 | `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9` |
| Release manifest | `e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882` |
| 最終 test report，10 項檢查 | `e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe` |

PM 對定稿內容重新獨立驗證 manifest、Schema（格式與必填內容）、canonical bytes（固定格式的檔案內容）、122 個定義、v005 的 102 份定義與三份發布檔案、八份 Policy、固定 Policy conformance 程式、兩份公開引擎及根層無 Release／Study／runtime／evidence／authority；全部通過。最終 `release_candidate.py --candidate` 與 Ruff 也均為退出碼 0。報告十項檢查的日誌指紋與實際退出碼已逐項相符，PM 結果在報告中另外列出。

驗收交付為 [release-manifest.yml](../../workflows/strategy-forward-replication-research--v006/release-manifest.yml) 與 [release-test-report.yml](../../workflows/strategy-forward-replication-research--v006/release-test-report.yml)。PM 接受 TASK-037 的重開修正與 TASK-038 完整交付，將兩項移到 Done。v006 維持 RC，`release_record_created=false`；v005 仍 Active。

TASK-039 尚待對最終三個指紋取得獨立的新核准，再由 workflow 執行者啟用。TASK-040／041 的 v006 專屬 skills 尚未建立；TASK-036 仍 Pending，等待既定啟用與開發指引依賴，再由 PM 明確重新分派。此次沒有建立正式 Release、真實 Study 或 commit。
