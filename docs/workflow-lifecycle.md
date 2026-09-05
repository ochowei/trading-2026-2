# Workflow Lifecycle：strategy-forward-replication-research--v001

## 文件目的

本文件定義 Workflow Package（流程套件）的生命週期，處理的是研究流程本身如何建立、發布、取代與封存；它與 Study Lifecycle（單一研究個案從建立到終止的流程）不同。

本文件目前適用於 `strategy-forward-replication-research--v001`。它位於 Workflow Package 外部，是專案治理文件，不列入 `v001` 的 release digest。這樣可以記錄 Workflow 的治理狀態，而不會因為在已發布的 Package 內新增文件，意外改變既有 Release Record。

## 目前狀態

截至 2026-09-05：

- Workflow：`strategy-forward-replication-research`
- Version：`v001`
- Status：`Active`
- Release Record：`workflows/strategy-forward-replication-research--v001/release.yml`
- 核准者：`william`
- 核准時間：`2026-09-04T18:54:24.100695000Z`

## Lifecycle 狀態

| 狀態 | 實際意思 | 可以做什麼 | 不可以做什麼 |
| --- | --- | --- | --- |
| `Draft` | Package 正在開發，尚未有有效的 `release.yml`。 | 修改規則、程式、Schema、測試與文件；執行開發測試。 | 建立正式 Study 或宣稱這個版本已獲正式核准。 |
| `Release Candidate` | 已產生 `release-manifest.yml` 與測試報告，並通過必要驗證，等待 Trusted Approver 核准。 | 由核准者檢視測試、規則與完整性證據。 | 正式建立 Study；自行建立 `release.yml` 啟用自己交付的版本。 |
| `Active` | 已有有效的 `release.yml`，且它與 manifest、測試報告及 Workflow digest 完全一致。 | 依這個版本建立新的 Study，並驗證既有 Study。 | 直接修改會影響結果的檔案；不得用「更新 status」方式改寫已發布內容。 |
| `Superseded` | 已有新的 Workflow Version 取代它接受新的 Study。 | 讀取、驗證及完成既有 Study；保留原始 Release Record。 | 再建立新的 Study；修改原 Package 來配合新版本。 |
| `Archived` | 這個 Workflow 已正式停止接受新的 Study，但既有資料仍須可追查與驗證。 | 讀取、驗證、重算及檢視既有 Study；保存完整 Package 與相關 authority/evidence。 | 刪除、搬移、重新命名或重新啟用原 Package。需要重新使用時，建立新的 Version。 |

## 合法的狀態轉換

```text
Draft
  → Release Candidate
  → Active
  → Superseded
  → Archived
```

若沒有新的替代版本，也可以由 `Active` 直接進入 `Archived`：

```text
Active → Archived
```

`Archived` 是封存終點，不重新啟用。若未來需要恢復相同研究能力，應建立新的 Workflow Version，重新驗證並重新發布；不得把舊 Package 改回 `Active`。

## 建立新的 Workflow

### 1. 先判斷是新版本還是新的 Workflow

- 研究目的與整體語意相同，只是修正規則、門檻、政策綁定或實作：建立下一個 Version，例如 `v002`。
- 研究目的、資料語意、研究階段、狀態模型或結果定義不同：建立新的 Workflow ID。

每個 Workflow Version 都必須是自包含 Package，包含自己的 `workflow.yml`、rules、schemas、policies、validator、guarded writer、tests、examples 與說明文件；不得依賴未指名的全域規則或 `latest` 版本。

### 2. 建立 Draft Package

在 `workflows/<workflow-id>--<version>/` 建立完整 Package，先完成：

- Workflow 範圍、資料角色、狀態轉換、門檻、結果與安全限制；
- 所有會影響研究結果的程式、設定、政策與實作綁定；
- 對應的 schemas、validator、writer、tests、examples 與 reference docs；
- Package 內的 Study 儲存規則與 immutable evidence 規則。

此時沒有有效 `release.yml`，只能視為 `Draft`。

### 3. 形成 Release Candidate

完成並通過以下驗證後，才可形成 `Release Candidate`：

- Workflow schema 與 canonical YAML 驗證；
- validator、state transitions、artifact digest 與 failure/recovery 反例；
- policy conformance；
- 端到端 Study fixtures 與各種 terminal dispositions；
- 全部必要 tests 與 Ruff 檢查；
- `release-manifest.yml` 與 `release-test-report.yml`。

Release Candidate 仍不是正式可用的 Workflow，因為此時還沒有 Trusted Approver 建立的 `release.yml`。

### 4. 由 Trusted Approver 啟用

Trusted Approver 必須檢視 Release Candidate 的規則、測試報告、manifest 與 digest，確認後一次性建立 `release.yml`。有效的 Release Record 必須綁定：

- Workflow ID 與 Version；
- Workflow digest；
- release manifest digest；
- test report digest；
- 核准者與核准時間。

只有完成這一步，狀態才是 `Active`。實作者不能自行替自己交付的版本建立正式 Release。

## 已發布 Workflow 的修改規則

`Active`、`Superseded` 或 `Archived` 的 Workflow Package 都不得直接修改已被 Release manifest 保護的內容。任何會影響研究結果或驗證行為的修改，都必須：

1. 建立新的 Version 或新的 Workflow ID；
2. 重新執行完整驗證與測試；
3. 產生新的 manifest 與 test report；
4. 由 Trusted Approver 建立新的 `release.yml`；
5. 讓新的 Study 明確綁定新的 Workflow digest。

既有 Study 從建立到終止都維持原本綁定的 Workflow Version，不因新版本發布而自動搬遷或重跑。

## Workflow Superseded 與 Archived 的處理方式

### Superseded

當新的 Workflow Version 已經成為 `Active`，Workflow 維護者可以將舊版本標記為 `Superseded`，並記錄：

- 取代它的 Workflow ID 與 Version；
- 停止接受新 Study 的時間；
- 取代原因；
- 舊版仍需保留的 Study、evidence 與 authority root。

舊版本的 Package、Release Record、manifest、測試報告與 Studies 必須原地保存。`Superseded` 不代表舊研究結果失效，也不代表可以刪除舊資料。

### Archived

若要正式封存，Workflow 維護者應先確認：

1. 已決定不再接受新的 Study；
2. 已記錄封存原因、日期與必要的替代版本；
3. 既有 Study 與外部 evidence/artifacts 仍可取得；
4. Workflow Package 與 authority root 已完成備份；
5. Validator 仍能驗證既有 Study 的事件鏈與 digest。

封存後只能讀取、驗證、重算與檢視既有 Study，不得刪除 Package，也不得以修改舊檔案的方式重新啟用。

## 目前的工具限制

目前的 release schema、validator 與 writer 已強制 `Draft` 與有效 Release 之間的界線，也會在已發布內容被修改時拒絕操作；但目前沒有 Workflow Registry、`archived` schema 欄位或專用的封存 CLI。因此：

- `Draft`、`Release Candidate`、`Active` 的部分可由現有 release artifacts 判定；
- `Superseded` 與 `Archived` 目前是本文件定義的治理狀態，尚未由工具自動阻擋建立新 Study；
- 在正式加入 Registry 或封存事件前，Workflow 維護者與 Workflow 執行者必須依本文件人工確認舊版本不得再建立新的 Study。

這個限制不影響既有 Study 的事件鏈與 Release Record；它表示未來若要完全自動化 Workflow Lifecycle，仍需另行建立 Workflow Registry、Archive Record schema、狀態驗證與對應測試。

## 相關權威文件

- [Workflow Package 說明](../workflows/README.md)
- [v001 Workflow Package README](../workflows/strategy-forward-replication-research--v001/README.md)
- [Workflow 定義](../workflows/strategy-forward-replication-research--v001/workflow.yml)
- [Release Record 規範](adr/0034-release-workflows-with-an-immutable-release-record.md)
- [自包含 Workflow Package 規範](adr/0031-each-workflow-is-a-self-contained-package.md)
- [Study Lifecycle 指南](../workflows/strategy-forward-replication-research--v001/reference/strategy-forward-replication-research-v001-guide.md)
