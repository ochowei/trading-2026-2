# `tsm-mean-reversion-selling-pressure-rollover--v002` 封存式盲檢討

- Review 版本：`001-first-review`
- Workflow：`strategy-forward-replication-research--v001`
- 角色：study 開發者
- 檢討日期：2026-09-10

## 範圍與結論限制

這是只使用研究設計、策略程式、測試與 Development evidence 的 blind review。Development
signal 期間是 2014-01-01 至 2018-12-31，2013 年只作 warmup；本次沒有開啟原始市場快照。
`check_scope.py` 回報 `blind_review_status: eligible`、`development_evidence_status: available`。

本次沒有讀取或使用正式 Historical Evaluation 結果、帶 outcome 的 Terminal 內容、terminal
payload 或 evaluation payload，因此本報告不能判斷正式 Evaluation 是否通過，也不能解釋正式
Evaluation 的失敗原因。

## 實際問題與影響

最重要的問題不是程式已被證明錯誤，而是新增的 Path B 目前仍是小樣本、可能排擠既有訊號的
設計假說：Development 只有 26 筆完成交易，事前要求的 30 筆少 4 筆；stress return 為
29.5255%，低於事前要求的 30.40%，所以 candidate freeze 不具資格。Path B 只有 5 筆交易，
在 base 與 stress 下全部為正；它們分別貢獻約 10,931 與 9,020 的 PnL，但新增交易及其
五日 cooldown 同時排擠了 3 筆原 v009 交易。換句話說，Path B 看似增加交易，不等於它的
淨增量已被穩健證明。

另一個需要正視的影響是風險衡量方式：官方 Development drawdown gate 只看已完成交易的
realized PnL，stress 為約 2.00%；以持倉期間每日 Low 做保守 mark-to-market 估值時，stress
最大回撤約為 3.42%，已高於研究目標 3.00%。這不是把現有 gate 改寫成失敗，而是表示目前
的 gate 可能看不到持倉內、尤其是 gap 期間的資金壓力。

## 假說與規則對照

目前規則的經濟含義可以清楚拆成兩層：

1. setup 是 `Close` 相對 SMA(20) 至少低 1.5%，且 RSI(2) 不高於 50，代表價格處在候選
   超跌區。
2. Path A 要求前五個已完成 session 曾有成交量領先，且訊號日收盤高於前一日；Path B
   則要求前五個已完成 session 的三日 Signed Volume Balance 曾低於或等於 -0.50，當前三日
   回升至至少 -0.15，但刻意不要求訊號日上漲。

訊號在已完成 session close 判定，下一個 XNYS open 進場；同一訊號日只做一筆，持倉結束
後等待五個完整 session，停損為原始進場 open 下方 4%，停利為上方 4%，最多持有十個完整
session。這個 setup／trigger 分工在設計上是自洽的，但 Path B 的「回升」仍是由收盤方向乘
成交量構成，並不是獨立於價格的資訊。SMA gap、RSI(2)、SVB3 也都部分描述近期價格行為，
因此新增條件可能只是把同一個超跌／反彈狀態用另一種方式重述，而不一定帶來獨立訊息。

## 規格與實作檢查

### 已確認一致的部分

- `indicators()` 只用訊號日及以前的資料；Path A 的成交量均值先 shift 一個 session，
  再取前五個 ratio，沒有把訊號日的量能當成「之前」的量能。
- Path B 的 SVB3 使用 `sign(close_t - close_{t-1}) * volume_t`，前五個 SVB3 先 shift
  排除當日，再取最低值；零成交量分母保留為未就緒值。這與 candidate definition 的
  `t-5-through-t-1` 及 `t-2..t` 定義一致。
- Path A 的測試明確以既有 v009 的 signal series 作直接比對；Path B 的同日去重、收盤後下一個
  session open 進場、gap 以 open 成交、同日同時碰到停損與停利時先算停損，也都在程式中
  有對應邏輯。
- 整數股數同時受現金上限及成本內含的停損風險預算限制；base/stress 費用與滑價也分別
  對應 preregistration。
- 本次對兩個策略模組與允許的 v001 測試做 Python 語法編譯，結果成功。完整 pytest 沒有
  執行成功：目前環境沒有 pytest，離線依賴快取也缺少 `python-dateutil`；這是驗證環境限制，
  不是策略結果。

### 規格缺口與未驗證風險

1. **同日 Path A／Path B 同時成立時的優先順序沒有在規格寫死。** 程式使用 `if Path A`
   再 `elif Path B`，因此歸類為 Path A。因兩條路徑共用執行規則，這目前不改變該筆交易的
   PnL，但會改變 path attribution、消融解讀與「新增了幾筆 Path B」的統計。下一版應明定
   priority，或允許一筆交易保留雙重 origin 標籤。
2. **2% risk fraction 不是 gap 情境下的硬性最大損失。** 部位大小是按停損價估算，但 gap
   stop 會按更差的 open 成交；因此未來遇到較大 gap 時，單筆損失仍可能超過預算。這與目前
   的 gap-fill 規則並不矛盾，卻是需要在新 Study 事前登記並用合成 gap case 驗證的風險。
3. **測試覆蓋仍偏向訊號形狀。** 現有測試驗證了 SVB3、Path A 等價、Path B 不需上漲確認、
   去重、下一個 open 與部分 intrabar fill，但沒有完整鎖定 cooldown 邊界、target 每日重掛、
   fold reset、gap 超過停損的風險上限，或 mark-to-market drawdown。這些是「尚未驗證」，不是
   已確認的程式錯誤。

## Development 穩健度

我從 `evidence/development.yml` 的 26 筆交易明細重算主要數字，與 evidence 摘要一致：

| 指標 | base | stress |
|---|---:|---:|
| 完成交易 | 26 | 26 |
| Profit factor | 5.3912 | 4.4983 |
| Return | 37.5167% | 29.5255% |
| realized 最大回撤 | 2.000% | 2.000% |
| 最大單筆 realized loss fraction | 2.000% | 2.000% |

正式 Development gates 全部通過；但 research targets 有兩項未通過：`26 < 30` 的完成交易
數，以及 `29.5255% < 30.40%` 的 stress return。minimum stress profit factor 4.4983
高於 4.0，使用 realized 定義的 maximum stress drawdown 約 2.00% 低於 3.00%。這就是為什麼
evidence 的 formal disposition 是 pass，但 candidate selection 與 candidate freeze 仍是
ineligible。

穩健度訊號如下：

- 五年都有交易，但 2017 只有 2 筆；2015 與 2018 合計約佔 base PnL 的 64%，獲利仍有明顯
  年度集中。Leave-one-signal-year-out 後，stress 最低 Profit factor 為 3.8203，最低 return
  為 17.8038%，仍為正，但剩餘交易數只有 19 至 24 筆。
- 預先指定的 trade-block bootstrap（每種 block length 10,000 次）在 stress 下正報酬比例為
  1.0；5% 分位 Profit factor 約為 2.53 至 2.67，95% 分位 realized drawdown 約 3.96%。
 這支持 Development 期間的方向一致性，但不會把 26 筆交易變成更大的獨立樣本。
- Path B 的 5 筆交易在本段 Development 全部獲利；同時 lifecycle breakdown 顯示它排擠了
  3 筆原 v009 交易，整合後相對 v009 的淨增量 PnL 約為 base 3,542、stress 2,837。這是
  需要在下一輪固定驗收規則中處理的 capacity／crowding 問題。
- calendar-block bootstrap 是事前標記為 descriptive-only；其 stress 5% 分位 Profit factor
  約 2.47 至 2.53、5% 分位 return 約 16.2% 至 16.8%，可作補充描述，不能當成額外正式 gate。

## 調整優先順序

| 優先 | 依據 | 下一輪應驗證的調整 | 預期解決的問題與可能副作用 | 可否證的驗收方式 |
|---|---|---|---|---|
| 1 | Development 警訊 | 事前固定 Path A／Path B 的優先順序與 capacity/crowding 報告，分開列出 Path B-only、被排擠的既有訊號與淨增量。 | 判斷 Path B 是增加獨立機會，還是用持倉與 cooldown 交換既有機會；更嚴格的容量限制可能減少交易數與 return。 | 在新 Study 凍結前預先登記淨增量、被排擠數量與 stress 下的最低接受條件；任一未達即否定增量假說。 |
| 2 | Development 警訊 | 把持倉內 mark-to-market drawdown 與 gap loss 作為獨立風險檢查，並加入合成 gap／較差 open 的測試案例。 | 避免 realized PnL 過度低估持倉中的資金壓力；更保守的風險規則可能降低部位與 return。 | 事前定義計算方式與上限，要求 base/stress 以及每筆 gap loss 都通過；不能用事後選擇的估值方式。 |
| 3 | 規格／實作缺陷 | 在新版本的 candidate definition 明寫 tie-break 或雙重 origin，並補 cooldown 邊界、target reissue、fold reset 的測試。 | 讓機制歸因與重算結果不依賴程式內未登記的 `if/elif` 順序；測試增加後可能揭露原本未覆蓋的邊界案例。 | 以固定 synthetic bars 驗收訊號日、exit 日、冷卻第 5 個 session、gap、同日雙路徑與 fold 邊界，要求預期結果逐項相等。 |
| 4 | 未驗證設計假說 | 在不改寫本 Study 的前提下，另立新 Study 比較「Path B 不要求上漲確認」與延遲進場、價格確認等固定變體。 | 驗證 SVB rollover 是否真的提供獨立的反轉時點；加入確認可能降低假訊號，但也可能錯過反彈。 | 所有變體在執行前固定；以交易數、淨增量、stress return、mark-to-market risk 與逐年穩健度共同判定，不按結果挑選變體。 |

目前不建議修改本 Study 的 frozen candidate、preregistration 或既有 evidence 來補救這些問題；本次結果應保留為補充性的 review note。

## 不能得出的結論

- 不能說正式 Historical Evaluation 已通過或失敗。
- 不能把 Development 的兩項 research-target failure、mark-to-market 警訊或 Path B 小樣本，
  寫成正式 Evaluation 的失敗原因。
- 不能保證上述下一輪調整會改善正式結果；它們只是可事前否證的驗證方向。

## 狀態判定

| 狀態 | 本次判定 |
|---|---|
| formal Development gates | `passed`；evidence 的 failed gates 為空 |
| research targets | `failed`：`minimum_completed_trades`、`minimum_stress_return` |
| Development evidence validity | `valid`，evidence 自載 `validated: true`；本次也以交易明細重算主要 metrics 相符 |
| blind review status | `eligible`；依據是目前沒有暴露正式 Evaluation 或帶 outcome 的 Terminal 內容 |
| Historical Evaluation status | `not_inspected`；本次不以此狀態推導盲檢討資格 |
| candidate freeze eligibility | `ineligible`；原因為上述兩項 research-target failure |

## 實際讀取檔案與禁止證據聲明

本次實際讀取：

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `manifests/preregistration.yml`
- `manifests/candidate-definition.yml`
- `manifests/qualification-spec.yml`
- `manifests/development-trial-inputs.yml`
- `manifests/source-bundle.yml`
- `manifests/data-snapshot-acquisition.yml`
- `evidence/development.yml`
- `evidence/development-authorization.yml`
- `src/trading_2026_2/tsm_mean_reversion_selling_pressure_rollover_v001.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `tests/test_tsm_mean_reversion_selling_pressure_rollover_v001.py`
- `tests/test_tsm_mean_reversion_selling_pressure_rollover_v002.py`
- `pyproject.toml`

沒有讀取或使用 `study.yml`、`README.md`、`evidence/historical-evaluation*`、
`evidence/terminal-evidence.yml`、`events/000008-*` 及其後事件、`journals/`、Terminal 或
Evaluation payload、full/quarantine/historical-evaluation 原始價格快照、網路資料或外部
connector。沒有讀取 `evidence/provenance.yml` 或 `evidence/selection-evidence.yml`，因目標
Study 目錄中不存在這兩個檔案；它們也沒有被用來補充結論。

本檔是補充性的盲檢討筆記，不是 stage evidence、candidate、source、event、journal、
terminal evidence 或 outcome，也不應加入事件鏈或改寫任何 digest。
