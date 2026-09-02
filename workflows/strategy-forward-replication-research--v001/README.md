# Strategy Forward Replication Research v001

這是一個自包含的美國股票日線回溯研究 Workflow Package。規則、schemas、policies、validator、guarded writer、tests、reference docs 與 Studies 都位於本目錄；大型或敏感 raw artifacts 以 Evidence Manifest 引用外部 content-addressed storage。

目前 v001 已於 2026-09-02 由 trusted approver 核准啟用。正式研究應直接使用正式 writer，不得加上 `--allow-draft`；如果 `release.yml` 缺失、內容損壞，或與 release manifest、測試報告不一致，writer 會拒絕操作。

## 使用方式

在 repository 根目錄執行：

```bash
uv run python workflows/strategy-forward-replication-research--v001/writer/cli.py --help
uv run pytest -q workflows/strategy-forward-replication-research--v001/tests
uv run ruff check workflows/strategy-forward-replication-research--v001
```

Study 會建立在本 package 的 `studies/<study-id>/`。本機 authority root 必須另外指定；它保存每次事件發布後的 head checkpoint，用來發現事件被意外刪除或退回舊版本。它不依賴 Git，也不需要網路或券商連線。

正式 writer 只接受已有 `release-manifest.yml`，且經 trusted approver 建立有效 `release.yml` 的版本。`--allow-draft` 只供尚未發布版本的開發與測試，不能用來建立正式研究。

第一次建立正式 Study 前，還要準備真實 Source Bundle、獨立的 authority root、Study identity 與 preregistration。`examples/` 內的 digest 和內容只是格式範例，不能直接當成正式研究輸入。

## 備份與恢復

請把 Workflow Package 與 authority root 一起備份。若寫入中斷，使用 writer 的 `recover` 指令；恢復只能完成原 journal 內已準備好的相同 bytes，不能換資料後重試。若 Study 與 authority checkpoint 不一致，validator 會停止，不會自行猜測哪一份正確。

這套本機防護的目的，是避免誤覆寫、半完成寫入與意外回退。它信任檔案管理者，不防止擁有完整檔案權限的人同時竄改 Study 和 authority root。

## Review 的意思

Independent Review 是從 frozen inputs 與 raw evidence 重新執行 deterministic validator。研究者、replay operator 和 reviewer 可以是同一個人；流程要求的是獨立重算，不是人員分離。

實作與驗收順序請參考 [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md)，操作與研究語意請參考 [`reference/strategy-forward-replication-research-v001-guide.md`](reference/strategy-forward-replication-research-v001-guide.md)，可填寫的最小骨架請參考 [`examples/README.md`](examples/README.md)。
