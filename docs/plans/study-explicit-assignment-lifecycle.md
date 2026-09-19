# 以明確派工取代 Study 人工核准

## 決策與適用範圍

2026-09-19，依使用者明確派工，由 workflow 維護者制定本規格。研究目的、資料角色與結果定義延續 v002；取消單一 Study 的人工核准前置條件，讓受派角色在指定範圍內連續執行。這是事件與驗證契約的變更，不是把 approval 自動填成 approved。

v002 已為 Active，受 release manifest 保護。本規格放在 Package 外，交由 workflow 執行者以後繼版本實作及驗證；不得直接改寫 v002 或遷移既有 Study。後繼版本號由建版時確認。本文件不建立 Draft Package、Release Candidate 或 Release，也不執行正式 Study。Workflow 發布核准仍適用，與本次取消的 Study 核准不同。

## 實際問題

目前 `create-authorize` 要求預先登記核准與 Development 授權兩份文件，發布 `preregistration-approved`、`development-authorized`；歷史評估另要求綁定候選指紋的 authorization。即使使用者已清楚指定研究及執行角色，仍要另外製作核准文件，且事件記錄的是核准而非實際登記或開始執行。

新流程只要求派工事實、研究輸入及可重算驗證。不再要求 trusted-approver 對個別 Study、Development 或歷史評估簽核；不新增等價的「確認」、「允許」或「放行」關卡。

## 派工與內容指紋分開

派工紀錄保存既有指令的來源識別、原文或可追查摘錄、指派者、受派者、角色、Study ID、workflow version 及工作範圍。工作範圍只能是 `development-to-freeze` 或 `historical-evaluation-to-terminal`。不得從模糊的「繼續研究」、開發交接或核准移除需求推導出正式歷史評估派工。

紀錄可由代理根據已收到的明確指令保存，不要求使用者另外提供 YAML、簽名、核准人或核准時間；內容不足時只詢問缺少的實際任務範圍。CLI 驗證結構、角色及 Study 一致性，不能宣稱因此驗證了使用者身分或指令真偽。不得填入虛構指派者或不存在的指令。

派工可以早於 source 或候選凍結，不必要求使用者在得知最終內容指紋後再次確認。內容指紋是將固定內容計算成摘要以偵測變動：由工具在登記與啟動時綁定真實檔案，不是派工人的簽章。執行紀錄保存派工紀錄指紋、workflow digest、Study ID、authority root、source bundle、預先登記與操作計畫指紋；歷史評估另綁定 candidate freeze、資料快照及 runner 指紋。

使用者可一次明確派出兩階段工作，但須由各自符合資格的角色執行；開發者不可自行切換成評估者。只有 Development 派工時，到候選凍結即完成派工，不自動開始歷史評估。已存在符合範圍的評估派工時，評估者不再索取一次人工核准。

## 事件及狀態

| 舊事件 | 後繼版事件 | 實際意義與必要證據 |
| --- | --- | --- |
| `study-created` | 保留 | 建立固定研究身分、版本、source 與 authority 綁定；保存派工及 prepare 報告引用。 |
| `preregistration-approved` | `preregistration-recorded` | 在任何正式 Development 前保存完整預先登記及指紋，驗證與 prepare 一致；不包含核准人或決策。 |
| `development-authorized` | `development-started` | 受派開發者開始固定計畫；綁定派工、登記、source 與 operation ID，不表示核准。 |
| 無 | `historical-evaluation-started` | 評估角色取得此 Study 唯一評估操作，綁定 frozen candidate、資料、runner、計畫與派工；必須先於正式資料讀取及 runner 啟動。 |
| `historical-evaluation-completed` | 保留 | 引用專用 store 的結果，依固定門檻重算；移除 authorization 引用，改核對同一 started operation。 |

主要路徑：

```text
study-created → preregistration-recorded → development-started
→ trial-recorded（可重複）→ trial-registry-frozen → provenance-audited
→ candidate-frozen → historical-evaluation-started
→ historical-evaluation-completed → study-terminal
```

完整轉換以 v002 表為基礎，只替換上述兩個舊事件，並把 `candidate-frozen → historical-evaluation-completed` 拆成 started 與 completed。`development-started → trial-registry-frozen` 的零 Trial 路徑保留；registry 與 provenance 的原有早期 terminal 路徑保留，結果仍由證據決定。不得從 created、recorded 或 started 跳過資格驗證直接凍結候選。

原有 `evidence-unavailable → study-terminal`、pause／resume 與 terminal 終點語意保留。新增的評估 started 狀態可轉 completed、evidence-unavailable 或 paused；resume 回到原狀態與同一 operation，不清除已開始記錄、不重新取得評估次數。started 後禁止回到 candidate-frozen 或 Development。

新版本拒絕舊核准事件及舊核准欄位，不設偷偷轉譯的相容入口。舊版 Study 使用原版 validator 驗證原事件，不改名、不重寫事件鏈。

## CLI 契約

| 命令 | 行為 |
| --- | --- |
| `prepare STUDY --report PATH` | 保留固定輸入、規格檢查及隔離 runner 測試；報告不具有派工或核准效力。 |
| `create --plan PATH --report PATH --assignment PATH` | 取代 `create-authorize`；先驗證所有輸入，依序發布 created、recorded、development-started。 |
| `develop-to-freeze STUDY --plan PATH --assignment PATH` | 依固定計畫串接 prepare、create、development、registry、provenance、freeze-readiness、freeze；遇實際缺件或不合格即回報，不停下索取核准。 |
| `development`、`freeze-readiness`、`freeze` | 保留分段入口；與連續入口共用 validator、writer、資格判定，不准另設較寬鬆路徑。 |
| `historical-evaluation STUDY --plan PATH --assignment PATH` | 只允許指定評估角色，驗證既有 freeze 及明確評估派工後，發布 started、執行唯一評估、completed、terminal。 |
| `status`、`validate`、`resume` | 保留角色範圍；resume 接續原 operation，不能換計畫、source、authority root 或角色。 |

`create` 計畫保存 creator、identity、完整 preregistration 及開發 actor，刪除 preregistration_actor、preregistration_approval、development_authorization 等核准專用資料。歷史評估計畫保留 actor、data_path、data_digest 等固定輸入，刪除 authorization；候選綁定由 validator 對事件及執行紀錄強制檢查。

所有寫入命令要求明示 `--role`，不以預設角色執行。CLI 角色字串不等於作業系統身分驗證；仍受 AGENTS.md 角色規範限制。低階 writer 的公開寫入介面也必須接收並驗證 actor／role／assignment context，與事件重建共用相同檢查，不能只在高階 CLI 擋住。

JSON 回應移除 `required_approval`，以 `missing_inputs`、`scope_boundary`、`operation_id`、已發布事件及待恢復 journals 說明狀況。區分 `assignment-missing`、`role-mismatch`、`binding-mismatch`、`qualification-failed`、`evaluation-already-started` 與 `recovery-required`；不得把合法的研究 fail 當作程式崩潰。通過檢查不需要互動式確認。

## 不可放寬的限制與恢復

1. 預先登記必須早於正式 Development；prepare 使用合成資料，不能偷偷先跑正式 Trial。登記後 source、門檻及計畫不得因結果而改寫；變動須另建 Study 並保存原紀錄。
2. 保留 prepare 新鮮度、canonical bytes、artifact digest、事件鏈、authority checkpoint、journal 與跨 Study 綁定驗證。缺失、刪除或改寫證據均須拒絕；歷史驗證不依賴目前 Python 環境與當年完全相同。
3. 保留完整 Trial registry、candidate／baseline 比較、provenance、候選選擇次序、最低門檻及 freeze-readiness。派工不能使不合格候選取得 freeze 資格，也不能自動填寫 verified-clean 或未接觸結果。
4. 開發角色在存取檔案前檢查路徑及符號連結解析結果，禁止讀取評估 store 或透過 status、validate、resume、例外訊息洩漏結果。評估結果仍只寫入 `historical-evaluation-artifacts/`，append-only；一般 Study 事件只保存必要引用與既有允許的控制資訊。不可掃描管理者專屬資料夾。
5. 多事件 create 或連續 Development 不宣稱跨事件原子性；每一事件有自己的 journal／checkpoint。部分成功後只按相同 plan、report、assignment 與 operation 恢復，不重複執行已完成 runner。
6. 歷史評估在 Study lock 內持久保存唯一 operation reservation，再發布 started 事件；任一步中斷只能恢復同一 reservation。started 事件及 checkpoint 完整落盤前，不得讀正式評估資料。啟動 runner 前另保存不可覆寫的 launch marker；完成輸出可重驗並發布，已有 marker 而輸出缺失或不完整時禁止自動重跑，走 evidence-unavailable／indeterminate 路徑。不能用不同 plan、operation ID、resume 或刪除局部輸出取得第二次執行。
7. reservation 已保存但 started 未完成時，只能修復原事件發布；started 已完成但 launch marker 尚不存在時，可接續尚未啟動的 runner。並行程序只准一個取得 reservation。保守處理 marker 落盤後、實際啟動前的崩潰，不把無法證明未執行當作可重跑。

## 實作交付與驗收

workflow 執行者應在後繼 Draft Package 同步調整 `workflow.yml`、state-machine、evidence requirements、event／plan／assignment schemas、projection、validator、writer、operations、preflight fixtures、範例及 skills。Study approval schema／驗證函式不再是新流程依賴；共用模組中仍有必要的 prepare 報告驗證須拆出保留。Workflow release 的 approved_by／approved_at 不在移除範圍。

下列案例是發布前必要驗收，全部使用暫存目錄與合成資料，不碰正式 Study 或正式評估 store：

- 無任何 approval 文件、approved 決策或 trusted-approver 身分時，明確派工可由 CLI 完整執行至 candidate freeze；獨立評估角色可由明確評估派工完成唯一評估及 terminal。
- 舊 `create-authorize`、approval 欄位與核准事件皆明確拒絕；測試 fixture 不得自動產生 approved 來讓新路徑通過。
- 缺少派工、跨 Study 派工、錯誤受派者／角色、只有開發派工卻要求評估、開發者直呼評估及 writer 旁路皆拒絕，且不得先讀受限資料或啟動 runner。
- 登記前執行、prepare 過期、source／preregistration／assignment 被改寫、跨 Study 引用及 authority root 改變皆拒絕；缺失佐證不可只靠快取 state 通過。
- 不合格 candidate、缺 baseline、registry 不全、provenance 不足、選擇次序偽造、門檻漂移皆無法 freeze；合法早期終止仍正常。
- 在 create 每一事件及評估 reservation、started、launch marker、輸出與 completed／terminal 之間逐點硬中斷，驗證恢復不重複事件、不重跑已啟動評估；並行及不同 plan 的第二次評估皆拒絕。
- 開發角色的 status／validate／resume／錯誤輸出不讀取或洩漏正式結果；測試以禁止讀取的假 store 驗證，而非只比較回應欄位。
- v002 Package、release 及既有 Study bytes 完全不變；原版驗證仍可獨立使用。執行新版本全部必要測試與 Ruff，保存實際命令與結果後再依 Workflow Lifecycle 形成 Release Candidate。

本次維護者交付為治理與介面規格，尚未讓現有 v002 CLI 取消核准。後續實作、測試、建版與發布依角色分工接續；不得將本文件或使用者本次改制要求視為任何正式 Study 的評估派工。
