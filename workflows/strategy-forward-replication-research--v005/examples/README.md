# Study 填寫範例

這個目錄只提供容易閱讀的填寫骨架，不是已完成的正式 Study，也不具有任何研究 authority。正式檔案必須由 guarded writer 寫入；不要直接複製範例後手動宣稱 `pass`。

最短順序如下：

1. 準備 `source-bundle.example.yml`，列出會影響研究結果的程式與設定 digest。
2. 建立 Study 後，發布 `preregistration.example.yml`。
3. 依序記錄全部 Trials、凍結 registry、稽核 provenance，再發布候選選取、Data Snapshot 與 Candidate Freeze evidence。
4. 發布 Historical Evaluation 的 raw evidence，重新執行 validator。
5. 產生 Terminal Evidence，最後追加 `study-terminal` event；不再追加 challenge、Replay 或 Independent Review event。

測試中的 `tests/helpers.py` 與 `tests/test_study_end_to_end.py` 是目前最完整、而且會由 CI 實際執行的範例。

## v005 runner 合成案例

`runner-contract.example.yml` 提供完整格式及人工價格數列，僅用來說明兩階段的有交易／無交易案例。每個策略都必須自行證明這些數列實際觸發指定分支；範例不保證能觸發任意策略。請依 [日常操作指南](../reference/operations.md) 使用 prepare 與 create。

多資產 Study 的 Development plan 應使用 `data_assets`，並在 Trial inputs 的 `data_bindings.assets` 保存完全相同的清單。TSM 可標成 `trade`，SOXX 標成 `reference`；兩份檔案各有路徑、日期與 digest。若 runner contract 仍只測單一 CSV，preflight 會拒絕這份多資產 Study。完整欄位、資源上限及凍結規則見[多資產資料契約](../reference/multi-asset-input.md)。
