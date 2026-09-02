# Study 填寫範例

這個目錄只提供容易閱讀的填寫骨架，不是已完成的正式 Study，也不具有任何研究 authority。正式檔案必須由 guarded writer 寫入；不要直接複製範例後手動宣稱 `pass`。

最短順序如下：

1. 準備 `source-bundle.example.yml`，列出會影響研究結果的程式與設定 digest。
2. 建立 Study 後，發布 `preregistration.example.yml`。
3. 依序記錄全部 Trials、凍結 registry、稽核 provenance，再發布候選選取、Data Snapshot 與 Candidate Freeze evidence。
4. 發布 Historical Evaluation、九項 Challenge 與 2025 Replay 的 raw evidence。
5. 重新執行 validator，產生 Terminal Evidence，最後才追加 terminal event。

測試中的 `tests/helpers.py` 與 `tests/test_study_end_to_end.py` 是目前最完整、而且會由 CI 實際執行的範例。
