# Authority Checkpoints

這個目錄是 repository-local 的 authority root，位置固定為：

```text
<repository-root>/.authority/
```

它位於 Workflow Package 與各個 Study 之外，但刻意納入 Git。每個 Study 的
checkpoint 會保存於：

```text
.authority/<study-id>/checkpoints/
```

checkpoint 會以 Git 追蹤，和 `workflows/strategy-forward-replication-research--v001/`
底下的 Event 一起備份。新的 Study 不得改用 `.study-authority/`、暫存目錄或其他
未確認的 authority root。

authority root 不是簽章，也不能防止同一個人同時修改 Event 與 checkpoint；它主要用來
偵測 Study Event 的誤刪、誤回退、換序與半完成寫入。
