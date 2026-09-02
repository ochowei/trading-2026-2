---
status: accepted
---

# 正式執行綁定 Source Content，而不是 Git

必要的 `exact_git_commit` 改為 `source_bundle_digest`：guarded writer 對所有會影響結果的 Python source、workflow、policy、設定與 dependency lock 建立固定清冊並計算 SHA-256。Git commit 若存在只保存為選用 metadata，不參與資格判定，使沒有 `.git` 的複製環境仍能獨立驗證 exact source identity。
