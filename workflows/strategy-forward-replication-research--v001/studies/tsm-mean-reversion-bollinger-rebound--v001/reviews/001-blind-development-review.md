# TSM 布林回落策略：Development 封存式檢討

檢討日期：2026-09-08
角色：study 開發者
Workflow：strategy-forward-replication-research--v001
Study：tsm-mean-reversion-bollinger-rebound--v001

本報告是補充性的 review，不是正式階段證據、候選、事件、Terminal evidence 或 outcome；不得加入事件鏈、改寫 digest，或作為下一次盲檢討的證據來源。

## 1. 範圍與結論限制

本次通過技能的範圍檢查，僅使用本 Study 的白名單文件、Development 交易證據，以及 Source Bundle 列出的允許程式與測試。Development 為 2014-01-01 至 2018-12-31，共 1,258 個 XNYS 交易日；warmup-only 為 2013-01-01 至 2013-12-31，共 252 個交易日，只供指標暖機，不計入績效。

**本次沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果，也不推測其表現。以下所有績效與門檻判斷都只指 Development。**

資料清冊指向涵蓋封存期間的共用完整 CSV，未提供本技能允許直接使用的獨立 Development／warmup 價格快照。因此本次沒有開啟該 CSV，沒有從原始價格重跑策略，也沒有核驗逐日價格如何產生每一筆訊號。交易金額與日期可由既有明細重算；訊號與執行邊界則以程式及合成資料核對。

白名單中的 evidence/provenance.yml 與 evidence/selection-evidence.yml 不存在，因此停止這兩項證據核對；不據此推測目前生命週期或 Terminal 狀態，也不宣稱已確認 candidate freeze。核心 Development 證據存在，足以完成下述有限範圍的檢討。

## 2. 實際問題與影響

### 改善目標沒有成立，並不是 Development 整體虧損

策略在開發資料中有正報酬，但沒有同時做到「增加可完成的交易」與「改善高成本下的績效」。從交易明細重算：

| Development 要求 | 預先門檻 | 本次結果 | 判斷 |
| --- | ---: | ---: | --- |
| 完成交易 | 至少 30 筆 | 25 筆 | 少 5 筆 |
| 高成本報酬 | 嚴格高於 26.5904% | 20.9880% | 少 5.6024 個百分點 |
| 高成本獲利因子 | 至少 3.2056 | 3.0878 | 未達 |
| 真正新增交易合計損益 | 基本／高成本都大於零 | +5,013.85／+3,372.59 | 達成，但不足以彌補其他三項 |

獲利因子是「獲利交易的損益總和，除以虧損交易的損失總和」。基本成本與高成本的報酬均為五年總報酬，不是年化報酬。

[預先門檻與停止規則](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/preregistration.yml:79) 已明定只有一個 Trial，任何門檻未達便停止，不在同一 Study 調參或放寬要求。本次重算與 [Development 自身記錄的三項未達門檻](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml:237) 一致。這支持保留本輪結果，不支持把它解讀成已達改善目標。

### 新增交易有賺錢，仍可能讓整體組合變差

依預先指定的「訊號日、進場日、出場日、出場原因」完整配對，候選保留 v009 的 18 筆交易、新增 7 筆，另有 6 筆只存在於 v009。交易總數因此只從 24 增至 25；v010 對照則有 29 筆。

| 相對 v009 的損益分解 | 基本成本 | 高成本 |
| --- | ---: | ---: |
| 7 筆新增交易 | +5,013.85 | +3,372.59 |
| 6 筆只存在於 v009 的交易 | +10,600.95 | +8,519.78 |
| 新增減去上述被替換交易 | -5,587.10 | -5,147.19 |
| 保留交易的金額差異 | -499.59 | -387.97 |
| 候選相對 v009 的整體損益差 | **-6,086.69** | **-5,535.16** |

候選交易的分組、金額與完整配對均可核對。v009 保留交易的合計金額是由同一 Development evidence 的 v009 總損益扣除其獨有交易推得，未讀取其他 Study，也未重新執行 v009。不同資金路徑會改變後續整數股數，因此不能只拿新增交易合計金額當作改善幅度。

「被替換」只代表 v009 有而候選沒有，不代表六筆全由冷卻造成。例如候選於 2014-09-17 至 10-01 持倉，覆蓋 v009 的 09-26 訊號時點，確實存在機會衝突；但缺少可讀價格與完整逐日訊號表，不能把所有缺失交易逐一歸因於持倉、冷卻或布林條件。[配對證據](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml:501)

## 3. 規格與實作檢查

**已檢查的核心訊號、成交、部位與 Development 金額計算，未發現可確認的規格不一致。這不等於完成從原始價格到所有證據的完整重現。**

| 規則 | 核對結果與實際意義 |
| --- | --- |
| 布林跌深 | 使用當日及之前共 20 個收盤價、母體標準差、上下各 2 倍標準差。位置 %b ≤ 0.25 等價於收盤不高於均線減 1 個標準差；邊界包含，未暖機或通道寬度為零不產生訊號。 |
| 舊跌幅與 RSI | RSI 是衡量近期漲跌幅比例的指標；本輪與固定 1.5% 跌幅一樣只作診斷，沒有暗中保留入場門檻。 |
| 成交量先行 | 對前五日各自計算「當日量／更早 20 日平均量」，其中任一天至少 1.05 倍即可。訊號當日的量不參與當天判定。 |
| 收盤止跌 | 收盤嚴格高於前收；它確認一天的價格方向，沒有要求重新站回中線、突破某價位或達到最低反彈幅度。 |
| 進出場 | 收盤決策、下一交易日開盤進場。停損跳空按較差開盤價、停利跳空按開盤價改善成交；同日同時碰到停利停損先算停損，再套成本。 |
| 持有與冷卻 | 進場日算第一日，完成第十個交易日後於下一開盤到期退出。平倉後滿五個交易日步距才可再接受訊號；同時最多一個部位。 |
| 日期與重置 | 25 筆交易的訊號、進場、出場均落在 Development。XNYS 日曆核對無隔日進場、持有日數、重疊持倉或冷卻違規，最短冷卻恰為 5 步。程式檢查及合成測試涵蓋暖機、期間尾端完整退出與重置；沒有執行正式評估 runner。 |
| 成本與部位 | 基本成本每邊滑價 0.05%、費用 0.01%；高成本每邊 0.20%、0.02%。部位按包含成本的 -4% 停損估計，把單筆風險預算設為進場前資金的 2%，並同時滿足現金上限、整數股、不借款。25 筆、兩種成本的股數、成交價、費用與損益均核對一致。 |

核對依據：[指標](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py:205)、[部位與成交](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py:267)、[交易時序與截止條件](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py:328)。

Source Bundle 中允許讀取的 8 個程式／測試／依賴檔，SHA-256 均與清冊相符；SHA-256 是用來確認檔案內容是否一致的摘要。Development 綁定的 preregistration、Source Bundle、trial inputs、acquisition manifest 四項檔案摘要也一致。未開啟清冊內不在白名單的 research runner，因此不宣稱完整 Source Bundle 全部驗證。

程式結構比較確認，候選與 v009 的回測、成本、股數、退出及回撤函式相同，主要變更在跌深指標；v010 另有 3 日冷卻等參數差異，不能把與 v010 的績效差全歸因於布林。

直接執行了既有測試中的 7 個安全測試函式與 3 個成交參數案例，並補充檢查冷卻、單一持倉、日期邊界與資料延伸不改寫先前交易。合成回測日期全部設為 2014 年，全部通過。未執行整套 pytest、research runner、正式評估測試或任何市場資料回測。

### 設計風險與量測限制

布林位置是「相對近期價格分散程度偏低」的情境條件，不等於反轉已成立。一天上漲提供方向確認，但幅度可以極小；前五日任一天量比 1.05 也不區分買盤、賣盤或事件衝擊。這些是機制尚未被分開驗證的設計風險，不能寫成已證明的失效原因。

本輪入場改成相對波動判斷，出場仍固定正負 4% 與十日持有。不同波動環境下，這些距離代表的難度可能不同。此處只有待驗證機制，沒有新增參數測試。

2% 是按正常停損成交估計的資金風險預算，不是跳空後損失上限。2018-10-23 的跳空停損在高成本下損失約 2.54% 的進場前資金，仍在本輪 4% 的已實現損失門檻內。

此外，[每日最低價回撤診斷](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py:509) 對開盤已完成的停利／停損跳空，仍會使用該日稍後的最低價。以純合成例子核對：同一筆開盤平倉、同樣賺 2,051.60 的交易，只把平倉日之後的最低價從 104 改成 50，診斷回撤就由 0.65% 變成 22.70%。這符合原先「整日 Low」的近似描述，沒有改變交易損益或正式門檻，但不能當成只涵蓋實際持倉的最大回撤。它也沒有追蹤日內最高資產值，故不宜宣稱為真實日內峰谷回撤的嚴格上界。

## 4. Development 穩健度

下表由 [25 筆交易明細](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml:738) 獨立重算；金額沿用 evidence 的資金單位，初始資金為 100,000。

| 指標 | 基本成本 | 高成本 |
| --- | ---: | ---: |
| 完成交易／交易年份 | 25／5 | 25／5 |
| 五年總報酬 | 27.5895% | 20.9880% |
| 期末資金 | 127,589.46 | 120,988.01 |
| 獲利因子 | 3.7664 | 3.0878 |
| 已實現最大回撤 | 2.5784% | 2.5365% |
| 勝率 | 76%（19 勝、6 負） | 68%（17 勝、8 負） |
| 平均獲利交易損益 | +1,976.97 | +1,825.92 |
| 平均虧損交易損益 | -1,662.15 | -1,256.59 |
| 平均每筆損益 | +1,103.58 | +839.52 |
| 最長連敗 | 2 筆 | 2 筆 |

高成本會同時縮小符合風險預算的股數，不能把兩欄的差全解讀成相同部位多扣的費用。

年度依訊號年份分組，沒有逐年重置資金；例如 2014 年訊號、2015 年退出的交易仍算在 2014 年。逐年移除是刪去該訊號年份的交易，再用其餘交易原有的「損益／進場前資金」比例重建資金路徑，不是重新產生訊號或重新計算整數股。

| 訊號年 | 筆數 | 基本損益 | 高成本損益 | 移除此年後高成本總報酬 | 移除此年後高成本獲利因子 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2014 | 6 | +5,421.37 | +4,124.61 | 16.1954% | 2.9044 |
| 2015 | 7 | +12,787.05 | +10,534.96 | 9.8716% | 2.3764 |
| 2016 | 4 | -688.14 | -1,275.64 | 22.3492% | 3.9557 |
| 2017 | 2 | +1,342.90 | +873.86 | 20.0627% | 3.2080 |
| 2018 | 6 | +8,726.27 | +6,730.21 | 14.2578% | 3.0503 |

五年中四年為正；2017 年只有兩筆，分段樣本稀少。2015 年貢獻高成本淨利的 50.20%，若分母只算正損益年份，則為 47.32%；最大單筆獲利貢獻淨利約 20%。這是集中度警訊，但移除任何一年後仍有正報酬、獲利因子大於 1，不能說策略只靠一個年份才獲利。上述比例也不是正式 Evaluation 的 fold 指標。

| 出場原因 | 筆數 | 高成本合計損益 |
| --- | ---: | ---: |
| 正常停利 | 6 | +10,584.91 |
| 開盤跳空停利 | 8 | +17,984.42 |
| 正常停損 | 2 | -4,588.18 |
| 開盤跳空停損 | 1 | -3,098.85 |
| 到期退出 | 8 | +105.71 |

到期退出占 32%，高成本合計只略高於零；跳空停利交易貢獻較大。但「跳空停利交易的全部損益」不等於「跳空價差本身的額外損益」，不能混為一談。

### 保留相鄰交易的重抽樣

依預先登記的區塊長度 3、5，各抽樣 50,000 次，各自重新使用亂數種子 20260902。方法是從按時間排序的 25 筆交易抽取連續區塊，末端可接回首筆，拼接後截成 25 筆，再按原有單筆損益比例連乘重建資金。這種 block bootstrap 讓相鄰交易一起被抽到，比把每筆完全打散更能保留局部群聚。

| 高成本、每區塊筆數 | 正報酬比例 | 總報酬第 5／50／95 百分位 | 回撤第 95 百分位 | 回撤超過 10% 的抽樣比例 |
| --- | ---: | --- | ---: | ---: |
| 3 | 99.886% | 8.3547%／20.8959%／35.7383% | 4.6843% | 0% |
| 5 | 99.976% | 10.1773%／21.0367%／32.7566% | 4.3400% | 0% |

基本與高成本兩組都重算；與既有 evidence 的統計差距小於 4×10⁻¹⁴，屬浮點運算差異。另以不首尾相接的連續區塊核對邊界處理，高成本正報酬比例為 99.816%／99.950%，回撤超過 10% 比例為 0.006%／0%，整體描述沒有反轉。

這些比例只是在既有 25 筆交易下的重抽樣結果，不是未來成功機率。抽樣 50,000 次沒有增加原始資訊量；以「交易筆數」分塊也沒有保留所有空手等待時間。Study 已明示同一 Development 被先前研究反覆使用，單一候選與這些重抽樣都不能消除累積研究偏誤。

既有 evidence 另記錄 63／126 交易日的日曆區塊診斷，以及高成本每日 Low 回撤 3.6026%。這些數字本次只核閱，未重算，也未用來證明真正持倉風險；本節的獨立驗證以交易明細可重建的指標為限。

重算環境：Python 3.11.15、NumPy 2.4.6、PyYAML 6.0.3；合成檢查另使用 pandas 3.0.5 與 pytest 9.1.1。XNYS 日曆由本機 exchange_calendars 產生，沒有取得外部市場資料。

可重算口徑：每筆淨損益＝股數×（成本後出場價－成本後進場價）－雙邊費用；資金從 100,000 逐筆累加；已實現回撤＝該資金曲線相對先前最高值的最大跌幅；獲利因子以正、負淨損益分別加總後相除。

## 5. 調整優先順序

本次沒有修改策略、門檻或任何既有 Study 證據，也沒有建立新 Study。以下是下一輪才可預先登記、再驗證的方向。

| 優先 | 依據分類 | 要解決的問題與建議 | 可能副作用 | 可否證的驗收方式 |
| --- | --- | --- | --- | --- |
| 1 | Development 警訊 | 本輪維持單一 Trial 的停止規則。下一輪把新增、保留、被替換交易及整體組合差額一起列為主要診斷，避免把「新增有賺」當作「整體改善」。 | 保留舊機會與增加新機會可能競爭同一個部位，交易數未必增加。 | 在新試驗前固定完整配對方式、共同風險與成本口徑及改善門檻；同時檢查整體績效與可完成交易數，不能只通過新增交易損益一項。 |
| 2 | 未驗證設計假說 | 先分清容量受限來自布林候選情境、一天收盤確認，還是持倉／冷卻。只選一個機制問題形成新候選，不同時改入場、停損、停利與冷卻。 | 更強的反轉確認可能進一步減少交易；較寬情境也可能占用原本較好的機會。 | 預先登記每一層條件的訊號數與排除原因，並用同執行規則的固定對照比較；若交易容量或整體高成本效果未達事前要求，即否證。現有簡單 baseline 同時移除量與方向，不能單獨證明哪個條件有效。 |
| 3 | Development 警訊 | 分開報告已實現回撤、實際持倉估值與整日 Low 的壓力近似，並標示跳空損失可超過 2% 預算。不要因已實現回撤約 2.54% 就認定全部風險已涵蓋。 | 更精確的持倉估值需額外資料或明確的日內順序假設；以保守上下界表示可能較不直觀。 | 新量測規格先通過「開盤退出後的價格不得改變實際持倉回撤」合成案例，保留原量測名稱與口徑的差異；不得藉重新定義指標改寫本 Study 的門檻或結果。 |

下一輪仍應揭露已知 Development 資訊與累積嘗試，不能把同一批資料上的再設計稱為獨立驗證。上述建議沒有任何一項能由目前證據保證改善正式結果。

## 6. 不能得出的結論

本報告不能判斷正式 Historical Evaluation 是否執行、是否通過、何年表現如何，或有何失敗原因；也不能推測 Terminal 狀態。不能從 Development 未達改善門檻推論正式結果。

未取得允許讀取的價格快照，因此不能完整重現原始訊號、逐日成交價格或持倉內回撤。provenance 與 selection evidence 的缺失也限制了完整證據鏈核對。這些限制不改變已能由 25 筆 Development 明細確認的算術結果。

## 7. 讀取紀錄與封存聲明

以下列出本次實際讀取的專案與技能檔案；uv.lock 只讀取位元組核對摘要，並未用來執行安裝。v009／v010 僅讀 Source Bundle 授權的共用程式，未開啟其 Study。

- [AGENTS.md](/Users/william/.codex/worktrees/4dc9/trading-2026-2/AGENTS.md)
- [/Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/SKILL.md](/Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/SKILL.md)
- [/Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/references/review-method.md](/Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/references/review-method.md)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/preregistration.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/preregistration.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/candidate-definition.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/candidate-definition.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/qualification-spec.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/qualification-spec.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/development-trial-inputs.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/development-trial-inputs.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/source-bundle.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/source-bundle.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/data-snapshot-acquisition.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/data-snapshot-acquisition.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml)
- [workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development-authorization.yml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/evidence/development-authorization.yml)
- [pyproject.toml](/Users/william/.codex/worktrees/4dc9/trading-2026-2/pyproject.toml)
- [src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py)
- [tests/test_tsm_mean_reversion_bollinger_rebound_v001.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/tests/test_tsm_mean_reversion_bollinger_rebound_v001.py)
- [src/trading_2026_2/__init__.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/__init__.py)
- [src/trading_2026_2/frozen_ohlcv_views_v001.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/frozen_ohlcv_views_v001.py)
- [src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py)
- [src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py](/Users/william/.codex/worktrees/4dc9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py)
- [uv.lock](/Users/william/.codex/worktrees/4dc9/trading-2026-2/uv.lock)

另執行本工作目錄的 .agents/skills/blind-review-strategy-study/scripts/check_scope.py，結果為 eligible。未讀取任何事件、journal、既有 review、Study／research README、study.yml、正式結果檔、完整價格快照、historical-evaluation-artifacts/ 或 .super-admin/；未使用 Git log/show/diff、網路、broker 或 connector。

本次在 /private/tmp/ 產生並使用重算與讀取清冊的暫存檔，僅包含本次由允許證據推得的數字及路徑，不是外部證據。本報告本身另經格式與數字核對，既有輸入檔案摘要保持不變。

**本次沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果。**
