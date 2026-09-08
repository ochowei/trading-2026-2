# TSM 賣壓退潮補充路徑研究

本 Study 只在 `v009` 的既有高品質 Path A 之外，增加一條以 3-session Signed Volume Balance（SVB3）判斷賣方主動性是否退潮的 Path B。Development 只使用 2013 warmup-only 與 2014–2018 Development view；quarantine 與 Historical Evaluation 僅保存固定資料角色的 metadata，不在本階段讀取或執行。

Path A 維持既有語意：收盤低於 20 日均線至少 1.5%、RSI(2) 不高於 50、訊號日前五個 session 內曾有量能比至少 1.05，且訊號日收盤高於前一日。Path B 使用同一個 base oversold 條件，加上訊號日前五個已完成 session 的 SVB3 最低值不高於 -0.50，以及今日 SVB3 不低於 -0.15；Path B 不等待價格上漲確認，訊號日收盤確認後於下一個 XNYS session open 進場。

所有正式 artifact 由 workflow guarded writer 發布。這個 bundle 只做到 candidate freeze 前，沒有正式 Historical Evaluation 結果。

