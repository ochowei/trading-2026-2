# TSM：Development 摘要與索引

本檔整理 52 個 Study 的研究階段（Development）記錄，不包含正式歷史評估或交易結果。2026-09-26 僅精簡文件，未重新核對底層證據、執行試驗或改判策略。每份摘要列目前採用內容；原卡、完整來源、指紋及歷次更正均逐字保存在歷史檔，文末附精確行連結。

閱讀時分開看「證據是否有效、正式門檻、研究目標、凍結資格、實際凍結狀態」。舊卡的 complete 或通過不必然代表目標全過或已凍結；未登記、不適用、尚不能判斷也不是同一件事。缺少證據只表示無法判定，除原卡另有明確記錄，不代表未曾執行。各卡未記載的判定維持未記載，不由其他欄位推論。

下列下一步沿用各卡當時建議，並非本次執行授權；不同版本的來源與結果各自保留，不把同數字當作獨立驗證。盲檢討的個案例外在該卡明列，不能由共同聲明覆蓋。

## 名詞與讀法

| 用語 | 白話說明 |
| --- | --- |
| candidate／baseline | 候選策略／比較基準；基準不自動取得候選的研究目標或凍結資格。 |
| base／stress | 基準成本／較不利成本情境。每份數字依原卡保留；比例與百分比依表頭區分。 |
| PF／MDD | 獲利因子：總獲利除以總虧損；最大回撤：績效自高點往後下跌的最大幅度。PF 為 inf 或 ∞ 不代表小樣本穩健。 |
| valid／證據有效性 | 證據格式、必要欄位及來源檢核通過；不等於假說成立，也不保證登記文字與程式一致。 |
| formal gates／research targets | 必須逐項通過的正式門檻／事前另登記的研究目標；兩種判定分開列。 |
| freeze eligibility／status | 是否具備固定候選供後續評估的資格／實際是否完成凍結；資格不足與狀態未知分開保留。 |
| readiness／qualification-failed／trial-recorded | 凍結前檢查／因不具資格停止／研究試驗已記錄；不能單憑其中一項改寫其他狀態。 |
| provenance／binding／digest | 來源可信狀態／結果與固定版本的綁定／檔案內容指紋。verified-clean 為原卡已核實來源標記，unknown 或未確認不補猜。 |
| publication／Source Bundle | 已發布證據與指紋的索引／本次綁定的程式來源包；完整值見各卡歷史連結。 |
| preregistration／contract／runner | 看結果前的研究登記／程式輸入輸出約定／把策略套用到資料並產生試驗結果的工具。 |
| bootstrap／leave-one-year-out | 保留相鄰交易的區塊重抽樣／每次剔除一年後檢查結果；用來觀察樣本變動影響，並非新增真實交易。 |
| session／XNYS／cooldown | 交易日／紐約證交所交易日曆／退場後暫停進場的冷卻期；stop、target 指停損與停利。 |
| SMA／RSI／ATR／bps | 簡單移動平均／相對強弱指標／平均真實波幅／基點（0.01%）；risk budget 是部位風險預算。 |
| OHLCV／消融／fixture | 每日開高低收與成交量／移除或單獨改一項條件來比較／用人工資料檢查程式的測試情境。 |
| blind eligibility／allowlist | 是否符合受限盲檢討的讀取條件／指定可讀清單；未看正式結果不等於整個盲檢討程序合格。 |

## Study 索引

| 摘要 | 原記錄日期 | 目前記錄的重點判定 |
| --- | --- | --- |
| [tsm-mean-reversion-reversal-trigger--v001](#study-01) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-reversal-trigger--v002](#study-02) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v001](#study-03) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v002](#study-04) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v003](#study-05) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v004](#study-06) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v005](#study-07) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v006](#study-08) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v007](#study-09) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v008](#study-10) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v009](#study-11) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v010](#study-12) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v011](#study-13) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-two-stage-volume-reversal--v012](#study-14) | 2026-09-08 | `未通過` |
| [tsm-mean-reversion-volume-lead-setup--v003](#study-15) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-volume-leads--v001](#study-16) | 2026-09-08 | `不可判定` |
| [tsm-mean-reversion-volume-leads--v002](#study-17) | 2026-09-08 | `未通過` |
| [tsm-mean-reversion-volume-leads--v003](#study-18) | 2026-09-08 | `未通過` |
| [tsm-mean-reversion-bollinger-rebound--v001](#study-19) | 2026-09-08 | `未通過` |
| [tsm-mean-reversion-bollinger-rebound--v002](#study-20) | 2026-09-08 | `未通過` |
| [tsm-mean-reversion-supplemental-divergence--v001](#study-21) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-supplemental-divergence--v002](#study-22) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-supplemental-divergence--v003](#study-23) | 2026-09-08 | `未完成` |
| [tsm-mean-reversion-supplemental-divergence--v004](#study-24) | 2026-09-08 | `通過` |
| [tsm-mean-reversion-selling-pressure-rollover--v001](#study-25) | 2026-09-09 | `evidence-unavailable`；門檻`尚不能判斷` |
| [tsm-mean-reversion-selling-pressure-rollover--v002](#study-26) | 2026-09-10 | `complete`；門檻`通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v013](#study-27) | 2026-09-10 | `complete`；門檻`通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v017](#study-28) | 2026-09-11 | `complete`；門檻`通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v014](#study-29) | 2026-09-11 | `evidence-unavailable`；門檻`尚不能判斷` |
| [tsm-mean-reversion-two-stage-volume-reversal--v015](#study-30) | 2026-09-11 | `evidence-unavailable`；門檻`尚不能判斷` |
| [tsm-mean-reversion-two-stage-volume-reversal--v016](#study-31) | 2026-09-11 | `complete`；門檻`通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v018](#study-32) | 2026-09-11 | `complete`；門檻`通過` |
| [tsm-mean-reversion-two-stage-volume-reversal--v024](#study-33) | 2026-09-17 | `complete`；門檻`通過` |
| [tsm-momentum-trend-volume-lead--v001](#study-34) | 2026-09-20 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-ramp--v001](#study-35) | 2026-09-20 | failed（已更正） |
| [tsm-momentum-trend-volume-absorption--v001](#study-36) | 2026-09-20 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-efficiency--v001](#study-37) | 2026-09-20 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-close-acceptance--v001](#study-38) | 2026-09-20 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-return-alignment--v001](#study-39) | 2026-09-20 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-range-compression--v001](#study-40) | 2026-09-21 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-gap-anchoring--v001](#study-41) | 2026-09-21 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-persistence--v001](#study-42) | 2026-09-21 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-peak-lead--v001](#study-43) | 2026-09-21 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-breadth--v001](#study-44) | 2026-09-22 | failed；不具凍結資格 |
| [tsm-momentum-trend-volume-response-lag--v001](#study-45) | 2026-09-22 | 候選 fail；不具凍結資格 |
| [tsm-momentum-trend-volume-body-followthrough--v001](#study-46) | 2026-09-22 | 候選 fail；不具凍結資格 |
| [tsm-momentum-trend-volume-body-sign-consistency--v001](#study-47) | 2026-09-22 | baseline 已更正為 valid；候選不具凍結資格 |
| [tsm-momentum-trend-volume-lagged-neutral-impulse--v001](#study-48) | 2026-09-23 | 盲檢討未通過；候選 0 筆 |
| [tsm-momentum-trend-volume-gap-retention--v001](#study-49) | 2026-09-23 | 盲檢討未通過；不具凍結資格 |
| [tsm-momentum-trend-volume-path-efficiency--v001](#study-50) | 2026-09-23 | 不具凍結資格；登記意圖有歧義 |
| [tsm-momentum-trend-volume-breadth-dispersion--v001](#study-51) | 2026-09-23 | 不具凍結資格；兩組結果相同 |
| [tsm-industry-relative-lag-repair--v001](#study-52) | 原卡未列 | 正式門檻 10/11；資格 false，凍結狀態未知 |

<a id="study-01"></a>
## `tsm-mean-reversion-reversal-trigger--v001`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：TSM 收盤低於 SMA(20) 至少 2%、RSI(2)≤35 時，若前五個 session 有成交量比率≥1.25，且訊號日收盤高於前一日，是否能提升均值回歸的穩健性。 本分支首份候選；加入成交量先行與訊號日反轉確認。 2% risk budget、-4% stop、+4% target、15-session 持有、退場後五-session cooldown 與 SMA＋RSI baseline。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：沒有可核對的結果證據；程式、測試或輸入檔存在，不能代替實際結果，也無法確認停止點。

**下一步**：補做一次固定規格的 Development trial，不修改候選規則。 產出這個已凍結候選的完整 Development evidence 與 bindings。 依 preregistration 的完整 gates 檢查完成交易、年度覆蓋、base/stress 報酬、PF 與 stress 回撤；任何 gate 失敗即否證。

**來源與歷史**：[原卡、完整來源及更正（原第 7–57 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:7)。

<a id="study-02"></a>
## `tsm-mean-reversion-reversal-trigger--v002`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：維持 SMA(20) 偏離 2%、RSI(2)≤35、五日成交量比率≥1.25、收盤高於前收的反轉觸發。 規格可見的主要差異是 candidate family／程序版本更新；沒有看到訊號、成本、持有期或風險規則的語義變更。 15-session 持有、退場後五-session cooldown、-4%／+4% stop-target 與相同 baseline。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：無法判定策略表現或凍結狀態；版本更新不是新策略，也不能以 v001 證據代替 v002。

**下一步**：只執行一次 v002 的完整 Development trial，並保留不可變 evidence。 同一候選的 Development evidence 產出與來源綁定，不再改訊號。 完整 gates 均有 actual、threshold 與 passed 值，且資料、程式、輸入 digest 一致；缺任何一項即未完成。

**來源與歷史**：[原卡、完整來源及更正（原第 58–108 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:58)。

<a id="study-03"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v001`

**判定**：Development `通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：TSM 低於 SMA(20) 1.5%、RSI(2)≤50 時，前五日成交量比率≥1.25 且訊號日收盤高於前收，是否能避免在下跌途中接刀。 本系列首份 Study；建立「量先換手＋價行止跌」兩階段條件。 下一 open 進場、退場後五-session cooldown、15-session 持有、2% risk budget 與 SMA＋RSI baseline。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 20 | 19.76% | 2.760 | 3.96% |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；20 筆交易是完成交易門檻 20 的剛好邊界，其餘交易年度、報酬、PF、回撤與額外穩健性 gates 均通過。

**限制**：交易數剛好達門檻，來源尚無獨立聲明；條件組合尚未逐一拆除比較，不能判定單項條件的效果。

**下一步**：建立有限 follow-up，單獨測試持有時間是否是主要限制。 把未觸發 stop／target 的持有期由 15 個 session 改為 10 個；訊號、成本、風險與 cooldown 不變。 完成交易至少 20 筆、年度至少 3 年，base/stress 報酬大於 0、PF 高於 1.10／1.00，stress 回撤不超過 10%，並保留完整重抽樣與逐年剔除 evidence。

**來源與歷史**：[原卡、完整來源及更正（原第 109–159 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:109)。

<a id="study-04"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v002`

**判定**：Development `通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：測試 TSM 的 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤高於前收的兩階段反轉。 candidate family 與 Study／實作版本更新；preregistration 沒有顯示訊號、執行或成本語義變更。 15-session 持有、退場後五-session cooldown、2% risk budget、-4%／+4% stop-target 與相同 baseline。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 20 | 19.76% | 2.760 | 3.96% |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；全部事前 Development gates 通過。

**限制**：同規則重發，並非新的條件增益或獨立驗證；來源聲明、持有期及成交量條件的因果問題仍未解決。

**下一步**：停止同規則重發，若要繼續只建立一個明確的持有期變更 Study。 將固定持有期由 15 個 session 改為 10 個，其他設定不動。 沿用完整 Development gates，並要求交易數不低於 20、stress 回撤不超過 10%；任一未達即停止。

**來源與歷史**：[原卡、完整來源及更正（原第 160–210 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:160)。

<a id="study-05"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v003`

**判定**：Development `通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：維持 TSM 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤高於前收的兩階段反轉條件。 candidate family 與版本識別更新；未見策略訊號、成本或執行規則變更。 下一 open 進場、15-session 持有、退場後五-session cooldown、2% risk budget 與 -4%／+4% stop-target。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 20 | 19.76% | 2.760 | 3.96% |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；全部事前 Development gates 通過。

**限制**：同規則、同數字不能證明持有期、成交量或價格確認各自有效；交易數仍在下限，來源未有獨立聲明。

**下一步**：停止同規則版本化，改做一個明確的持有期變更測試。 將未觸發 stop／target 的持有期由 15 個 session 改為 10 個。 沿用相同訊號、成本、風險與 cooldown；完成交易至少 20、stress 報酬大於 0、PF>1、回撤≤10%，並完成 bootstrap／leave-one-year-out。

**來源與歷史**：[原卡、完整來源及更正（原第 211–261 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:211)。

<a id="study-06"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v004`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：維持 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤反轉，只把未觸發 stop／target 的持有期縮短至 10 個 session。 持有期 15→10 個 session；成本、部位、cooldown、stop／target 與訊號固定。 同一 SMA＋RSI baseline 也採 10-session 執行規則。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：無法判定縮短持有期的交易數、成本後報酬或風險；不能沿用 15-session 結果推論 10-session 效果。

**下一步**：先完成固定規格的 Development evidence，再決定是否保留 time-decay 假說。 只執行 v004 已凍結的 10-session 持有規則，不再改門檻。 完成交易至少 20、交易年度至少 3 年、base/stress 報酬大於 0、PF 高於 1.10／1.00、stress 回撤≤10%；缺 evidence 或任一 gate 失敗均不通過。

**來源與歷史**：[原卡、完整來源及更正（原第 262–312 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:262)。

<a id="study-07"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v005`

**判定**：Development `未完成`；來源可信狀態：`verified-clean`。

**研究與差異**：測試 10-session 固定持有是否比長持有更能保留均值回歸優勢。 規格中未見訊號、成本、風險或持有語義變更，主要是 Study／candidate 版本與來源登錄更新。 1.5% SMA 偏離、RSI(2)≤50、成交量比率≥1.25、收盤高於前收、10-session 持有、五-session cooldown、2% risk budget。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：已有僅限 Development 的授權、禁止連網及 verified-clean 來源記錄，但這些不等於績效或門檻通過。

**下一步**：完成 v005 的固定規格 Development evidence，或明確封存為未完成，不再用新版本掩蓋缺口。 同一 10-session 候選的 evidence 完整性與 gate 產出。 base/stress 的 actual、threshold、passed、raw-trade bindings 與 provenance 均齊全；完整 gates 全數通過才算完成。

**來源與歷史**：[原卡、完整來源及更正（原第 313–363 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:313)。

<a id="study-08"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v006`

**判定**：Development `未完成`；來源可信狀態：`verified-clean`。

**研究與差異**：確認 10-session 持有規則在成交量先行與訊號日反轉條件下，是否仍能通過穩健性 gates。 未見策略語義變更；主要是版本、source bundle 與程序登錄更新。 1.5% SMA 偏離、RSI(2)≤50、成交量比率≥1.25、收盤高於前收、10-session 持有、五-session cooldown 與 2% risk budget。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：授權限暖機與 Development、禁止連網；缺證據不代表策略失敗，也無法確認與 v005 是否重現。

**下一步**：只補齊 v006 的 Development evidence，完成後再決定是否進行 volume filter 的消融。 固定 10-session 規則下，關閉成交量先行條件；其他訊號與執行規則不變。 先要求 v006 evidence 完整；後續消融版本仍須通過完成交易、年度、報酬、PF、stress 回撤與重抽樣 gates。

**來源與歷史**：[原卡、完整來源及更正（原第 364–414 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:364)。

<a id="study-09"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v007`

**判定**：Development `通過`；來源可信狀態：`verified-clean`。

**研究與差異**：相較 v006，只移除前五個 session 的成交量尖峰條件，保留收盤高於前收的止跌確認，檢查成交量是否提供可重現的額外篩選。 關閉 volume-lead filter；10-session 持有與其他條件固定。 SMA(20) 偏離 1.5%、RSI(2)≤50、五-session cooldown、-4%／+4% stop-target、2% risk budget。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 25 | 30.97% | 3.861 | 2.03% |
| Development / stress | 25 | 23.96% | 3.249 | 2.12% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；25≥20，stress 單筆最大虧損 2.02%、bootstrap 正報酬比例最低 99.996%、逐年剔除 gates 全部通過。

**限制**：同份證據的描述性比較中，volume-only 為 36 筆、stress PF 1.280、報酬 6.95%；這些比較不參與選擇，不能據此挑新門檻或宣稱價格條件具跨期因果優勢。

**下一步**：建立有限 follow-up，重新加入成交量條件但只改一個門檻。 在保留收盤反轉與 10-session 執行的前提下，將成交量比率門檻由 1.25 改為 1.05。 沿用完整 Development gates；完成交易至少 20、stress 報酬與 PF 仍通過、回撤≤10%，並保留同樣的 mechanism ablation。

**來源與歷史**：[原卡、完整來源及更正（原第 415–465 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:415)。

<a id="study-10"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v008`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：在保留收盤反轉的前提下，較寬鬆的 1.05 倍成交量確認能否增加交易樣本並維持風險調整後品質。 重新啟用 volume-lead，且門檻 1.25→1.05；其他訊號與 10-session 執行固定。 SMA(20) 偏離 1.5%、RSI(2)≤50、收盤高於前收、五-session cooldown、2% risk budget、-4%／+4% stop-target。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：已有固定規格與授權，但無法確認實際執行或封存情況；不得用預期交易數或前版結果代填。

**下一步**：先完成 v008 的固定規格 Development evidence。 不再改 1.05 門檻或訊號，補齊實際 run、raw trades、metrics、gates 與 provenance bindings。 完整 Development gates 通過，並能核對 volume-on 與 price-only 的描述性消融；缺任何 evidence 或 gate 失敗都不進 freeze。

**來源與歷史**：[原卡、完整來源及更正（原第 466–516 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:466)。

<a id="study-11"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v009`

**判定**：Development `通過`；來源可信狀態：`verified-clean`。

**研究與差異**：在保留 1.5% SMA 偏離、RSI(2)≤50 與訊號日收盤反轉下，把成交量先行門檻固定為 1.05，檢查適度換手條件是否保留樣本與穩健性。 確認並重發 1.05 倍 volume-lead candidate 的可核對 Development evidence；本輪規格的策略門檻維持 1.05。 10-session 持有、五-session cooldown、-4%／+4% stop-target、2% risk budget 與相同資料邊界。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 24 | 33.68% | 5.036 | 2.00% |
| Development / stress | 24 | 26.52% | 4.204 | 2.12% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；stress block bootstrap 正報酬比例最低 99.998%、stress 回撤超過 10% 比例為 0，逐年剔除後最低 stress 報酬 18.36%、PF 3.409。

**限制**：樣本有限；描述性消融中的 price-only 為 24 筆、calibrated two-stage 為 25 筆，均有正 stress 結果，但不代表 1.05 已被證明最佳。

**下一步**：若要增加容量，只允許一次單參數變更，並保留本 Study 作固定基準。 只把退場後 cooldown 由 5 個 session 改為 3 個，維持 1.5%／RSI 50／volume 1.05 與 10-session 持有。 完成交易增加但不少於 20，base/stress 報酬與 PF 通過，stress 回撤≤10%，bootstrap 與 leave-one-year-out gates 不得退化失敗。

**來源與歷史**：[原卡、完整來源及更正（原第 517–567 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:517)。

<a id="study-12"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v010`

**判定**：Development `通過`；來源可信狀態：`verified-clean`。

**研究與差異**：把 SMA 偏離門檻由 1.5% 放寬至 1.2%、RSI 上限由 50 放寬至 55，並把退場後 cooldown 由 5 縮短至 3，檢查交易容量能否增加而不破壞成本後品質。 一個「容量擴張組合」同時改三項設定；這不是可完全歸因於單一 knob 的變更。 volume 1.05、收盤高於前收、10-session 持有、2% risk budget、-4%／+4% stop-target 與相同資料。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 29 | 34.79% | 3.837 | 2.55% |
| Development / stress | 29 | 26.59% | 3.206 | 2.58% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；stress PF 為 3.206、stress 報酬 26.59%，且 bootstrap、逐年剔除、單筆損失與回撤 gates 均通過。

**限制**：三項設定同時變更，無法分辨 SMA、RSI 或冷卻期各自貢獻，不能將通過歸功於任何單項。

**下一步**：建立單參數隔離 follow-up，不再複製三項同時放寬。 固定 1.2% SMA、RSI 55、volume 1.05 與 10-session 持有，只把 cooldown 由 3 恢復為 5 個 session。 完整 gates 通過，並比較交易數、stress 報酬、PF 與回撤；任何 gate 失敗即否證該單一 cooldown 變更。

**來源與歷史**：[原卡、完整來源及更正（原第 568–618 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:568)。

<a id="study-13"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v011`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：以 1.5% SMA 偏離、RSI(2)≤50、volume 1.05 建立資格，保留 v009 同日確認，並允許三日內延後確認。 改回 v009 的嚴格資格門檻，加入三日有效期的 delayed confirmation 與明確等待狀態；這是機制變更，不是單純參數調整。 10-session 持有、2% risk budget、-4%／+4% stop-target、資料邊界與 base／stress 成本固定。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：無法判定延後確認是否增加有效交易；事前研究目標也沒有實際結果，不能事後放寬三日有效期。

**下一步**：只完成 v011 的固定規格 Development trial，再依事前 targets 決定停止或 freeze。 產出延後確認版本的完整 raw trades、v009／v010 controls 與新增交易比較；不調整三日有效期。 交易數嚴格高於 29、stress 報酬嚴格高於 v009、延後新增交易的 base 與 stress 合計損益都大於 0，且 formal gates 全數通過。

**來源與歷史**：[原卡、完整來源及更正（原第 619–669 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:619)。

<a id="study-14"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v012`

**判定**：Development `未通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：保留 v009 的超跌、RSI 與成交量資格；若當日收盤高於開盤、日內 high>low，且收盤位於當日區間上方三分之一，即使未高於前收也提早確認反轉。 移除三日 delayed confirmation，改為同日盤中反轉條件；同時使用較嚴格的交易數、stress PF 與 stress 報酬選擇門檻。 下一日 open 進場、10-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target 與相同資料。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 28 | 21.80% | 2.166 | 5.88% |
| Development / stress | 28 | 15.38% | 1.849 | 5.88% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：`completed_trades` 28≥30 失敗；`stress_profit_factor` 1.84883≥3.20558 失敗；`stress_return` 0.15380>0.26590 失敗。

**限制**：正報酬不能抵銷事前門檻失敗；無法區分盤中確認、交易替換與較高選擇門檻的影響，不得降低既定門檻。

**下一步**：停止本次 intraday-reversal 假說，不放寬 failed gates。 若仍需 follow-up，只恢復 v009 的收盤高於前收確認，其他 1.5%／RSI 50／volume 1.05／10-session 設定固定。 必須重新通過本輪的交易數、stress PF、stress 報酬與原有穩健性 gates；任一失敗即停止，不再加入第三種確認規則。

**來源與歷史**：[原卡、完整來源及更正（原第 670–720 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:670)。

<a id="study-15"></a>
## `tsm-mean-reversion-volume-lead-setup--v003`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：TSM 低於 SMA(20) 至少 2%、RSI(2)≤35 且前五日成交量比率≥1.25 時，即使訊號日未收紅，是否仍保留有參與度的回落 setup。 移除 `close_above_prior_close` 方向確認；成交量先行與其他執行規則固定。 15-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target、base／stress 成本與 SMA＋RSI baseline。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：沒有實際結果可判斷移除方向確認後的交易數或品質；不得以同系列有方向條件的結果代替。

**下一步**：先完成 v003 固定規格 Development evidence，再決定是否停止或保留 setup 假說。 只執行「volume lead、無訊號日方向確認」版本，不再改 RSI、SMA 偏離或持有期。 完整 Development gates、交易年度、兩套成本報酬與 PF、stress 回撤及重抽樣均需有 actual 並通過。

**來源與歷史**：[原卡、完整來源及更正（原第 721–771 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:721)。

<a id="study-16"></a>
## `tsm-mean-reversion-volume-leads--v001`

**判定**：Development `不可判定`；來源可信狀態：`provenance-unknown`。

**研究與差異**：SMA(20) 偏離至少 2%、RSI(2)≤35 時，若前五日成交量比率≥1.25，能否在價格偏離擴大前辨識換手並提高均值回歸穩健性。 本分支首份候選；加入 volume-lead 條件。 15-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target 與 base／stress 成本。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：原卡記載 evidence-unavailable payload 明示沒有產出結果試驗；來源驗證未通過，但 snapshot 或 binding 的具體原因未確認。不得以修正版結果回填。

**下一步**：建立 corrected Study，只修正 source validation／snapshot integrity，不修改 volume-lead 策略。 讓同一候選產出可核對的 warmup、Development raw trades、metrics 與 bindings。 source validation、network control、資料 digest 與完整 Development gates 全數有證據；若仍無 outcome-bearing evidence，維持未完成。

**來源與歷史**：[原卡、完整來源及更正（原第 772–822 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:772)。

<a id="study-17"></a>
## `tsm-mean-reversion-volume-leads--v002`

**判定**：Development `未通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：修正 v001 的來源驗證問題後，測試不含訊號日方向確認的 volume-lead candidate 是否能在五年中維持穩健均值回歸。 修正 source／程序版本以產出正式 Development evidence；訊號仍是 volume-lead 1.25，沒有加入方向確認。 2% risk budget、-4%／+4% stop-target、15-session 持有、五-session cooldown、base／stress 成本與相同 baseline。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 29 | 6.86% | 1.294 | 6.40% |
| Development / stress | 29 | 2.03% | 1.088 | 6.77% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：stress block bootstrap 回撤超標比例 0.25024／0.20438>0.10；正報酬比例 0.60006／0.61252<0.80；leave-one-year-out 最低 PF 0.96755≤1；最低報酬 -0.00459≤0。

**限制**：整體正報酬掩蓋部分抽樣及剔除年度後的負結果；無法歸因於成交量門檻、缺方向確認或 setup 本身，來源亦無獨立聲明。

**下一步**：建立有限 follow-up，只加入訊號日收盤低於前收的方向確認，不改 volume threshold。 在 1.25 volume-lead 與其他設定固定下，新增 `close_below_prior_close`。 完整原有 gates 全數通過，尤其 stress bootstrap 正報酬比例≥80%、回撤超標比例≤10%，以及 leave-one-year-out 的最低 PF>1、報酬>0。

**來源與歷史**：[原卡、完整來源及更正（原第 823–873 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:823)。

<a id="study-18"></a>
## `tsm-mean-reversion-volume-leads--v003`

**判定**：Development `未通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：成交量先行若再加上訊號日收盤低於前收，是否能把較有方向的回落 setup 與無方向成交量異常分開。 新增 `close_below_prior_close`；SMA 偏離 2%、RSI(2)≤35、volume 1.25、成本、風險、持有期與 cooldown 固定。 15-session 持有、2% risk budget、-4%／+4% stop-target、base／stress 成本與相同 SMA＋RSI baseline。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 28 | 4.42% | 1.191 | 6.40% |
| Development / stress | 28 | 0.01% | 1.000 | 8.09% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：stress bootstrap 回撤超標比例 0.34794／0.27364>0.10；正報酬比例 0.50224／0.50444<0.80；leave-one-year-out 最低 PF 0.82576≤1、最低報酬 -0.02431≤0。

**限制**：加入收跌條件後，stress 報酬接近零；2015、2017、2018 的逐年剔除結果存在報酬或 PF 未達標，不能將接近不虧當成穩健成功。

**下一步**：停止本方向確認版本，不再疊加第三個 filter。 若流程必須 follow-up，只移除 `close_below_prior_close`，其餘 volume-lead 設定固定；不得同時改 threshold。 必須重新通過原有 bootstrap 與 leave-one-year-out gates，且 stress 報酬、PF、回撤與交易數都達到事前門檻；否則終止此分支。

**來源與歷史**：[原卡、完整來源及更正（原第 874–924 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:874)。

<a id="study-19"></a>
## `tsm-mean-reversion-bollinger-rebound--v001`

**判定**：Development `未通過`；來源可信狀態：`verified-clean`。

**研究與差異**：將均值回歸的超跌條件由固定均線偏離改為動態布林通道下軌（%b ≤ 0.25），並搭配前五日成交量比率 ≥ 1.05 與訊號日收盤反轉，檢驗能否改善極端行情下的進場品質。 本系列首份 Study；引進動態布林通道下軌作為超跌資格，同時保留成交量先行與收盤確認。 20 日、±2 倍標準差通道的布林 baseline；10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 25 | 27.59% | 3.766 | 2.58% |
| Development / stress | 25 | 20.99% | 3.088 | 2.54% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：`completed_trades` 25 < 30 失敗；`stress_profit_factor` 3.0878 < 3.20558 失敗；`stress_return` 0.20988 < 0.26590 失敗。

**限制**：重抽樣正報酬比例雖達 99.88% 以上，仍未達容量與超越基準目標；動態布林的單獨貢獻尚不明。

**下一步**：建立有限 follow-up，嘗試引入事件觀察期以捕捉延後確認的反彈機會。 將同日布林條件拆分為事件觸發與 5 個 session 內的延後確認，其他風險與執行規則固定。 完成交易至少 30 筆，且 stress 報酬、PF 與回撤符合事前 gate；任一失敗即否證。

**來源與歷史**：[原卡、完整來源及更正（原第 925–975 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:925)。

<a id="study-20"></a>
## `tsm-mean-reversion-bollinger-rebound--v002`

**判定**：Development `未通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：布林下軌跌深與爆量觸發後，若在後續 5 個 session 內守住事件日低點且出現收盤反轉，是否能捕捉更多延後止跌的反彈交易並維持品質。 將同日條件改為「事件記憶（5 個 session 觀察期）」與「縮量守低後反轉確認」兩階段架構。 10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target、base（1/5 bps）與 stress（2/20 bps）成本。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 16 | 10.89% | 2.868 | 2.58% |
| Development / stress | 16 | 7.57% | 2.240 | 2.54% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018，但 2017 僅 1 筆） 失敗 gate：`completed_trades` 16 < 20（Workflow 最低門檻）與 16 < 30 失敗；`more_completed_trades_than_v009`、`base_return_not_below_v009`、`stress_return_not_below_v009` 等事前目標均失敗。

**限制**：60 個事件中 34 個（56.7%）因跌破低點失效，8 筆因持有到期退出；2018 少數交易貢獻近半獲利。事件到期邊界與成交量參數未對齊也是限制，不宜沿用未修正設計。

**下一步**：停止本事件記憶與縮量守低假說，不在此 Study 放寬門檻。 若需繼續布林研究，應簡化觸發條件或改進持有期配對，不再疊加事件觀察與守低狀態機。 完成交易至少 20 筆（優先滿足流程底線），stress PF > 1.10、報酬 > 0 且通過各年度穩健性檢查。

**來源與歷史**：[原卡、完整來源及更正（原第 976–1026 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:976)。

<a id="study-21"></a>
## `tsm-mean-reversion-supplemental-divergence--v001`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：TSM 在既有跌深反彈條件之外，若在低檔出現價格破底但成交量未創高的量價背離現象，補充進場能否增加有效交易機會。 本系列首份候選；新增量價背離補充觸發路徑（ATR 距離、近 3 日低點比對與成交量分數）。 10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：規格、授權、runner、程式與測試存在，但不能代替結果；實際停止原因未確認。

**下一步**：補齊固定規格的 Development trial 證據，不修改候選規則。 產出已登記候選的完整 Development evidence 與 bindings。 依 preregistration 的完整 gates 檢查完成交易（至少 20 筆）、年度覆蓋、base/stress 報酬與 PF；任一 gate 失敗即否證。

**來源與歷史**：[原卡、完整來源及更正（原第 1027–1077 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1027)。

<a id="study-22"></a>
## `tsm-mean-reversion-supplemental-divergence--v002`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：維持 TSM 均線偏離 1.5%、RSI(2)≤50、成交量先行 1.05 與量價背離補充路徑的雙重觸發設計。 規格中僅見 candidate family 與版本識別更新；未見策略進出場、成本或風控語義變更。 10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：版本識別更新不能代替結果；目前無法判定績效、容量或任何門檻。

**下一步**：只執行一次固定規格的 Development trial 並封存 evidence，不再改動訊號。 同一量價背離候選的 Development evidence 產出。 完整 gates 均有 actual 且通過門檻；缺漏任何一項即未完成。

**來源與歷史**：[原卡、完整來源及更正（原第 1078–1128 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1078)。

<a id="study-23"></a>
## `tsm-mean-reversion-supplemental-divergence--v003`

**判定**：Development `未完成`；來源可信狀態：`provenance-unknown`。

**研究與差異**：確認量價背離補充路徑在 TSM 均值回歸中的表現。 Study 及 candidate 版本識別更新；未見訊號、成本或執行規則變更。 10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：同規則持續重發仍缺結果；不能宣稱量價背離補充路徑具重現性。

**下一步**：專注產出完整的 Development evidence，避免持續同規則重發。 產出本策略的完整 evidence 與資料綁定。 完成交易至少 20 筆、stress 報酬大於 0、PF > 1.0、最大回撤在限度內且重抽樣 gate 全數通過。

**來源與歷史**：[原卡、完整來源及更正（原第 1129–1179 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1129)。

<a id="study-24"></a>
## `tsm-mean-reversion-supplemental-divergence--v004`

**判定**：Development `通過`；來源可信狀態：`provenance-unknown`。

**研究與差異**：TSM 低於 SMA(20) 1.5%、RSI(2)≤50 且成交量比率≥1.05 時，加入量價背離補充路徑是否能捕捉更優質的反彈時機。 完成並封存可核對之正式 Development evidence；策略進出場與風控規則維持同一設定。 10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target、base／stress 成本。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 27 | 38.73% | 5.967 | 2.00% |
| Development / stress | 27 | 30.40% | 4.831 | 2.00% |

**門檻與覆蓋**：交易年度覆蓋：5（2014–2018） 失敗 gate：無；所有事前 Development gates（包含報酬、獲利因子、回撤、交易數與逐年剔除）全數通過。

**限制**：逐年剔除後最低 stress 報酬 19.73%、PF 3.792；但無獨立來源聲明，也無法排除參數過度配合本樣本。未做單一機制消融，不能將改善全歸因於背離條件。

**下一步**：建立有限 follow-up Study，對量價背離補充路徑進行單一參數敏感度測試或消融驗證。 單獨關閉或調整量價背離補充路徑中的觀察窗口（例如由 5 個 session 改為 3 個），其他參數不變。 完成交易至少 20 筆，base/stress 報酬與 PF 維持通過，stress 回撤不超過 5%；任何 gate 失敗即否證該參數變更。

**來源與歷史**：[原卡、完整來源及更正（原第 1180–1230 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1180)。

<a id="study-25"></a>
## `tsm-mean-reversion-selling-pressure-rollover--v001`

**判定**：成果卡狀態：`evidence-unavailable`；Development gate：`尚不能判斷`；來源可信狀態：`verified-clean`；實際凍結狀態：`已完成`。

**研究與差異**：TSM 超跌時，價格尚未反轉，但賣方成交量可能已先衰退。若三個 session 的 Signed Volume Balance（依漲跌方向加總成交量的賣壓指標）由前五個 session 的極負值回升，可能增加可接受的均值回歸交易。 保留 v009 的 Path A，新增不要求訊號日收盤上漲的 Path B；Path B 要求目前 SVB3 ≥ -0.15，且前五個 session 的最低值 ≤ -0.50。 SMA(20) 超跌 1.5%、RSI(2)≤50、下一個開盤進場、持有 10 個完整 session、5-session cooldown、2% risk budget、-4% stop／+4% target，以及簡單超跌 baseline。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：來源聲明記載已完成凍結，與目前缺少 Development 結果證據是兩回事；不能由 verified-clean 或凍結記錄反推績效通過。

**下一步**：修正 Development evidence 的產製與 validator 綁定流程，不調整策略參數。 以相同凍結候選補齊可驗證的 base／stress Development evidence。 validator 接受合法 evidence，且兩種成本情境都含實際交易數、報酬、PF、回撤、年度與必要 diagnostics；否則仍為 `evidence-unavailable`。

**來源與歷史**：[原卡、完整來源及更正（原第 1231–1285 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1231)。

<a id="study-26"></a>
## `tsm-mean-reversion-selling-pressure-rollover--v002`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`provenance-unknown`；實際凍結狀態：`未完成`。

**研究與差異**：在 SMA(20) 超跌 1.5%、RSI(2)≤50 時，若前三日 SVB3 從前五日的極負值回升，是否能在不等待收盤上漲確認下增加有效交易。 保留既有 v009 Path A，新增不要求訊號日上漲的 Path B。 下一個 session open 進場、10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本模型。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 26 | 37.52% | 5.391 | 2.00% |
| Development / stress | 26 | 29.53% | 4.498 | 2.00% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）。 Research targets 失敗：完成交易 26 少於 30；stress return 29.53% 低於 30.40%。

**限制**：Path B 的 5 筆皆獲利，但排擠 3 筆 v009 交易，淨增量仍待驗證。來源無獨立聲明；已實現回撤約 2.00%，保守逐日估值的 stress 回撤約 3.42%。

**下一步**：建立一個只測 Path B capacity／crowding 的 follow-up Study。 固定 Path A／Path B 優先順序，並扣除被排擠的既有交易後重新評估淨增量。 完成交易至少 30 筆、stress return >30.40%，且 Path B 扣除被排擠交易後的淨增量仍為正。

**來源與歷史**：[原卡、完整來源及更正（原第 1286–1340 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1286)。

<a id="study-27"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v013`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`verified-clean`；實際凍結狀態：`未完成`。

**研究與差異**：退場後放量事件若在三個 session 內獲得原有反轉條件確認，能否提前恢復交易。 加入提前冷卻重設；其餘訊號、執行、成本、風控與持有期沿用 v009。 固定 v009 two-stage candidate。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 25 | 24.399% | 3.353 | 2.362% |
| Development / stress | 25 | 18.167% | 2.742 | 2.596% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）；formal gates 無失敗，research targets 失敗 10 項，故 freeze 未完成。

**限制**：新增 3 筆提前交易（2015–2016）的 base／stress 損益為 -210.07／-677.31，並取代兩筆 v009 獲利交易；總交易僅增 1 筆，不能把正式門檻通過當成可凍結。

**下一步**：停止本 Study freeze，建立有限 follow-up Study。 只禁止上一筆交易以 stop、stop-gap 或 stop-same-session 結束後啟動提前重設。 formal gates 全通過，新增減被取代的 base／stress PnL >0，且 stress 報酬／PF／回撤不劣於 v009；任一失敗即停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1341–1395 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1341)。

<a id="study-28"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v017`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`provenance-unknown`；實際凍結狀態：`未完成`。 原卡記錄 Development 證據已由 validator（證據檢查工具）接受。

**研究與差異**：訊號日前第 2–5 個交易日若先有成交量至少為前 20 日均量 1.25 倍、收盤守住區間上半部的放量事件，之後出現不破事件低點的縮量收跌回測，是否能讓原本只需低於 SMA(20) 1.0%（含）至未滿 1.5% 的淺超跌訊號形成有效均值回歸機會。 保留 v009 原有量先與收盤上漲路徑，新增一次性、最新事件優先的「放量→縮量回測→收盤反轉」補充路徑。 下一個 XNYS session open 進場、10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與成本模型。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 24 | 33.676% | 5.036 | 2.000% |
| Development / stress | 24 | 26.523% | 4.204 | 2.119% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）。 失敗 gate：無 formal Development gate 失敗；但 research targets 有 7 項失敗，包括完成交易 24<30、相對 v009 未增加交易（24 不大於 24）、新增交易數 0<1、新增交易年度 0<3、兩套成本下淨新增減被排擠損益均為 0，以及 stress 報酬 26.523%<30.40%。

**限制**：建立 164 個放量事件，補充確認及交易均為 0；與 v009 完全相同的結果不支持新增機制。無獨立來源聲明，無法分辨事件窗口、低點或消耗規則何者造成稀疏。

**下一步**：停止 v017 candidate freeze，不在原 Study 內調參或重跑。 若仍要延伸，只把補充事件的有效觀察窗口（含 expiry）由 5 個 session 延長至 7 個 session；其餘訊號、成本、執行與風控固定。 formal Development gates 全部通過，且補充路徑至少產生 1 筆交易、分布於至少 3 個 signal years、總交易至少 30 筆、stress 報酬至少 30.40%，兩套成本下淨新增減被排擠損益都嚴格大於 0；任一條件失敗即停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1396–1451 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1396)。

<a id="study-29"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v014`

**判定**：成果卡狀態：`evidence-unavailable`；Development gate：`尚不能判斷`；來源可信狀態：`未確認`；實際凍結狀態：`尚不能判斷`。

**研究與差異**：訊號日前第 2–5 個交易日若先有成交量至少為前 20 日均量 1.25 倍的放量事件，之後出現收跌、量縮至事件量 80% 以下且不跌破事件低點的淺回測，是否能在原本 1.5% 超跌門檻之外，形成扣除成本後有優勢的均值回歸機會。 移除 v013 的退場冷卻提前重設，改加入獨立的「放量事件→縮量回測→訊號日收盤上漲」補充路徑；它與 v009 原有路徑並存，原路徑優先。 v009 的資料、進場與退場、2% 風險預算、10 個完整持有 session、停損停利、冷卻與成本口徑。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：缺 evidence/development.yml，績效、門檻、研究目標與凍結資格皆無法判斷；不得以程式或輸入重建數值。

**下一步**：修正 Development evidence 的產製、驗證與封存流程；不要在 v014 內補跑或調整策略參數。 只驗證同一候選能否產出一份被 validator 接受、同時包含 base／stress 與 status table 的 `evidence/development.yml`。 檔案存在、validator 接受、base／stress 結果完整且 status 與 gates／research targets 一致即成功；缺檔、無法驗證或任一情境缺資料即失敗。

**來源與歷史**：[原卡、完整來源及更正（原第 1452–1506 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1452)。

<a id="study-30"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v015`

**判定**：成果卡狀態：`evidence-unavailable`；Development gate：`尚不能判斷`；來源可信狀態：`未確認`；實際凍結狀態：`尚不能判斷`。

**研究與差異**：延續 v014 的放量後縮量淺回測補充路徑，檢驗訊號日只需低於 SMA(20) 1.0%（含）但未達 1.5% 時，是否能形成成本後有優勢的均值回歸交易。 明確綁定 v009 Study-local comparison control，並將同一套候選與 Development runner／證據路徑版本化；v014 與 v015 的策略 source diff 為空，因此沒有可確認的策略規則變更。 補充路徑條件、v009 原有路徑、資料期間、成本、2% 風險預算、10-session 持有、停損停利與冷卻規則。

**結果**：允許範圍沒有可核對的 Development 結果證據；base／stress 績效、交易年度及門檻不可判定，不填零、不借用前版結果。

**限制**：策略與 v014 相同，但兩處 evidence 目錄都缺 development.yml；無法確認 base／stress 是否實際執行，不得借用 v014 或 v009 結果。

**下一步**：修正 Development evidence 產製、validator 驗證與封存鏈；保持策略規則不變，不在 v015 內重跑或調參。 只驗證候選結果能否產出並封存一份與 v009 control 綁定、可被 validator 接受的 `evidence/development.yml`。 evidence 存在且合法、base／stress 完整、status table 與 gates／research targets 一致即成功；任一缺失或不一致即失敗。

**來源與歷史**：[原卡、完整來源及更正（原第 1507–1561 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1507)。

<a id="study-31"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v016`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`provenance-unknown`；實際凍結狀態：`未完成`。 原卡記錄 Development 證據已由 validator（證據檢查工具）接受。

**研究與差異**：放量事件後的縮量、不破低點淺回測，是否能在原 v009 路徑外增加扣除成本後有優勢的均值回歸機會；補充路徑只在訊號日前 2–5 個交易日有效，且與原路徑並存但不增加持倉。 策略 source 與 v015 相同；v016 主要是同一候選的版本化 Study／runner 與獨立 Development evidence，沒有新的策略參數變更。 v009 原有路徑、資料與 2014–2018 期間、base／stress 成本、2% 風險預算、10-session 持有、5-session 冷卻、停損停利與進出場口徑。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 24 | 33.676% | 5.036 | 2.000% |
| Development / stress | 24 | 26.523% | 4.204 | 2.119% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）。 失敗 gate：無 formal Development gate 失敗；research targets 失敗包括完成交易至少 30、交易數多於 v009、新增交易至少 1 筆且分布至少 3 年、base／stress 淨新增減被排擠損益嚴格大於 0，以及 stress 報酬至少 30.40%。實際新增交易為 0、兩套成本下淨新增損益為 0。

**限制**：164 個事件未形成任何補充確認或交易；24 筆全來自原路徑，新增及淨新增損益均為 0。來源無獨立聲明，不能估計補充機制效果；研究目標失敗阻止凍結。

**下一步**：停止 v016 candidate freeze；若要延伸，建立有限 follow-up Study，不在原 Study 內調參或重跑。 只把補充事件的有效觀察窗口／expiry 從 5 個 session 延長到 7 個 session，其餘訊號、成本、執行與風控固定。 formal Development gates 全通過，補充路徑至少新增 1 筆交易且分布於至少 3 個 signal years，總交易至少 30 筆，stress 報酬至少 30.40%，兩套成本下淨新增減被排擠損益都嚴格大於 0；任一條件失敗即停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1562–1617 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1562)。

<a id="study-32"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v018`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`verified-clean`；實際凍結狀態：`未完成`。 原卡記錄 Development 證據已由 validator（證據檢查工具）接受。

**研究與差異**：連續兩日放量、跌幅收斂、低點守住，若訊號日只比 SMA(20) 低 1.0% 至未滿 1.5% 且收盤轉強，是否能增加成本後有優勢的均值回歸交易。 在 v009 原有訊號路徑上加入事前固定的淺回落補充路徑；原路徑、成本、風險、停損停利、持有期與冷卻規則維持不變。 v009 comparison control、2013 warmup／2014–2018 Development、下一個 XNYS open 進場與單一部位執行口徑。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 24 | 33.676% | 5.036 | 2.000% |
| Development / stress | 24 | 26.523% | 4.204 | 2.119% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）。 失敗 gate：無 formal Development gate 失敗；research targets 失敗包括交易至少 30 筆、交易數多於 v009、新增交易至少 1 筆且分布至少 3 年，以及 base／stress 淨新增減被排擠損益大於 0。實際新增交易與淨新增損益均為 0。

**限制**：補充路徑的原始訊號、接受訊號及完成交易皆為 0；24 筆全來自 v009。多條件交集或持倉限制的影響尚不能區分，不能估計增量效果。

**下一步**：停止 v018 candidate freeze，不在原 Study 內調參或重跑。 另建一個 follow-up，只放寬一項事前有機制理由的補充條件；原 v009 路徑、成本、執行、風控與比較控制全部固定。 formal Development gates 全部通過，補充路徑至少有 1 筆新增交易且分布於至少 3 個 signal years，總交易至少 30 筆，base／stress 淨新增減被排擠損益均嚴格大於 0；任一條件失敗即停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1618–1673 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1618)。

<a id="study-33"></a>
## `tsm-mean-reversion-two-stage-volume-reversal--v024`

**判定**：成果卡狀態：`complete`；Development gate：`通過`；來源可信狀態：`verified-clean`；實際凍結狀態：`未完成`。 證據狀態表為 valid／validated。

**研究與差異**：上升趨勢中的放量蓄勢，若在事件後五個交易日內突破固定價位，能否補足 v009 均值回歸的交易空窗，同時增加交易並維持 stress 表現。 在 v009 原有路徑上加入完整補充路徑：收盤高於 SMA(20) 且均線上行、成交量至少為前 20 日均量 1.25 倍、事件收盤不高於前五日高點，之後五日內首次嚴格突破固定價；事件失效、單事件追蹤與原路徑優先順序均事前固定。 v009 原路徑、2014–2018 資料範圍、下一個 XNYS open 進場、base／stress 成本、2% 風險、4% 停損／停利、10-session 持有與 5-session 冷卻。

| 條件 | 完成交易 | 報酬 | PF | 最大回撤 |
| --- | ---: | ---: | ---: | ---: |
| Development / base | 35 | 33.874% | 2.806 | 5.880% |
| Development / stress | 35 | 24.715% | 2.348 | 5.880% |

**門檻與覆蓋**：交易年度覆蓋：5 年（2014–2018）。 失敗 gate：無 formal Development gate 失敗。研究目標失敗為：base 最大回撤 5.8799% > v009 的 1.9998%；stress 報酬 24.7146% < v009 的 26.5232%；stress 最大回撤 5.8797% > v009 的 2.1193%；淨新增 stress PnL 為 -1,598.34，未大於 0。

**限制**：新增 11 筆補充交易提高交易量，卻惡化 stress 結果及回撤；無證據缺口，但研究目標失敗使候選不具凍結資格，不能歸因至單一補充條件。

**下一步**：停止 v024 candidate freeze，不在原 Study 內調參或重跑，並停止這組「上升趨勢放量突破」增量假說。 無；不建立 v024 同機制的參數 follow-up。若另起研究，必須另行事前登記全新假說，不得用本輪失敗結果反向放寬門檻。 本輪停止處置的成功條件是保留合法 evidence、凍結失敗結論且不事後調參；若未來另立 Study，須事前要求 formal gates 全通過、stress 報酬不低於 v009、stress 回撤不高於 v009，且淨新增 stress PnL 嚴格大於 0。

**來源與歷史**：[原卡、完整來源及更正（原第 1674–1730 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1674)。

<a id="study-34"></a>
## `tsm-momentum-trend-volume-lead--v001`

**研究與差異**：五日分散量能壓力先於當日價格加速；baseline 只關閉量能壓力，量能欄位只取先前交易日。

**判定**：成果卡 failed；兩組證據 valid。候選失敗：交易數、交易年度及 stress 逐年剔除報酬；baseline 失敗：base／stress 報酬與 PF、交易數及 stress 穩健性門檻。研究目標未登記；候選不具凍結資格，實際凍結狀態尚不能判斷。

| Trial／模型 | 情境 | 證據狀態／原因 | 交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `tsm-momentum-trend-volume-lead-v001`／candidate | Development/base | valid；只有 1 筆合法完成交易 | 1／1（2015） | 1.904% | ∞ | 0.000% |
| `tsm-momentum-trend-volume-lead-v001`／candidate | Development/stress | valid；同一筆交易的壓力成本結果 | 1／1（2015） | 1.622% | ∞ | 0.000% |
| `tsm-momentum-trend-volume-lead-v001`／baseline | Development/base | valid；控制組完整產出 | 16／5（2014–2018） | -0.573% | 0.956 | 4.548% |
| `tsm-momentum-trend-volume-lead-v001`／baseline | Development/stress | valid；控制組完整產出 | 16／5（2014–2018） | -2.793% | 0.780 | 4.832% |

**限制與更正**：單筆正報酬與 PF 無限大不代表穩健；未找到獨立來源聲明，未驗證完整事件鏈或凍結事件。

**下一步**：另立 Study，事前固定一項改善交易覆蓋的機制，其餘條件不變；證據須有效，至少 20 筆／3 年且全部正式門檻通過，否則停止凍結。

**來源與歷史**：[原卡、完整來源及更正（原第 1731–1758 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1731)。

<a id="study-35"></a>
## `tsm-momentum-trend-volume-ramp--v001`

**研究與差異**：前三個交易日至少一次量能達此前二十日均量 1.05 倍；baseline 只關閉量能脈衝。

**判定**：依更正，目前成果卡採 failed（原 complete 已更正）；證據仍 valid、研究目標未登記、候選不具凍結資格，流程停在凍結前。候選失敗：報酬、PF、交易數及 stress 重抽樣／逐年剔除門檻；baseline 核心及壓力門檻亦失敗。

| 模型 | 交易數／年 | base 報酬／PF | stress 報酬／PF |
| --- | --- | --- | --- |
| candidate | 11／4 | -1.865%／0.828 | -3.271%／0.695 |
| baseline | 16／5 | -0.573%／0.956 | -2.793%／0.780 |

**限制與更正**：單筆損失 2.601%、stress 回撤 4.797% 及年度門檻通過，不能抵銷失敗項目。

**下一步**：不得在本 Study 調參或重跑；若續研，另立 Study 重新事前登記。

**來源與歷史**：[原卡、完整來源及更正（原第 1759–1774 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1759)。
更正定位：[更正（2026-09-20）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1769)。

<a id="study-36"></a>
## `tsm-momentum-trend-volume-absorption--v001`

**研究與差異**：前五日先出現成交量至少為二十日均量 1.20 倍、收盤絕對變化不超過 0.5% 的吸收狀態，再由當日漲幅至少 2% 確認；baseline 只關閉吸收條件。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選失敗：交易數、stress 重抽樣正報酬比例、逐年剔除 PF／報酬；baseline 另失敗 base／stress 報酬、PF 及多項穩健性門檻。候選不具凍結資格，實際凍結狀態尚不能判斷；未完成 registry、來源及凍結事件。

| Trial／模型 | 情境 | 證據狀態／原因 | 交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `tsm-momentum-trend-volume-absorption-v001`／candidate | Development/base | valid；完整 evidence | 5／3（2015、2016、2018） | 3.9698% | 2.9487 | 1.9991% |
| `tsm-momentum-trend-volume-absorption-v001`／candidate | Development/stress | valid；完整 evidence | 5／3（2015、2016、2018） | 2.9420% | 2.4477 | 1.9997% |
| `tsm-momentum-trend-volume-absorption-v001`／baseline | Development/base | valid；控制組完整產出 | 16／5（2014–2018） | -0.5729% | 0.9556 | 4.5483% |
| `tsm-momentum-trend-volume-absorption-v001`／baseline | Development/stress | valid；控制組完整產出 | 16／5（2014–2018） | -2.7935% | 0.7800 | 4.8322% |

**限制與更正**：候選重抽樣正報酬比例 0.7969<0.80；剔除 2018 後 stress PF 0.7983、報酬 -0.4100%，結果對年度敏感。

**下一步**：另立 Study，保留 1.20 倍及 0.5% 定義，僅改吸收觀察窗口或另立明確替代機制；至少 20 筆／3 年，全部正式門檻通過，重抽樣正報酬比≥0.80、各逐年剔除 stress PF>1.00 且報酬>0。

**來源與歷史**：[原卡、完整來源及更正（原第 1775–1800 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1775)。

<a id="study-37"></a>
## `tsm-momentum-trend-volume-efficiency--v001`

**研究與差異**：前五日成交量加權日內區間／未加權日內區間≥1.15，檢驗高量伴隨較大區間是否先於價格加速；baseline 只關閉這項條件。

**判定**：成果卡 failed；證據 valid；研究目標未登記。候選只失敗交易數（6<20），其餘門檻通過；baseline 失敗報酬、PF、交易數及 stress 穩健性。候選不具凍結資格，readiness／freeze 未完成，實際凍結狀態尚不能判斷。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | ---: | ---: | ---: | ---: |
| candidate | Development/base | valid／6／3（2015、2016、2018） | 5.208% | 3.427 | 1.999% |
| candidate | Development/stress | valid／6／3 | 3.930% | 2.853 | 2.000% |
| baseline | Development/base | valid／16／5（2014–2018） | -0.573% | 0.956 | 4.548% |
| baseline | Development/stress | valid／16／5 | -2.793% | 0.780 | 4.832% |

**限制與更正**：只有三年六筆，不能將正報酬視為穩健優勢；來源綁定已核對，但未形成凍結來源事件。

**下一步**：停止原 Study；另立且事前固定一項新的量價效率機制，其餘不變，要求有效證據、至少 20 筆／3 年及全部正式門檻通過。

**來源與歷史**：[原卡、完整來源及更正（原第 1801–1818 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1801)。

<a id="study-38"></a>
## `tsm-momentum-trend-volume-close-acceptance--v001`

**研究與差異**：前五日量能加權收盤位置≥0.48、加權減未加權位置差≥0.01，另要求平均量比≥1.05；baseline 只關閉收盤承接條件。這是實際執行的規則。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選只失敗交易數（4<20）；baseline 失敗 base／stress 報酬與 PF、交易數及 stress 重抽樣／逐年剔除。候選不具凍結資格，baseline 資格不適用；實際凍結狀態尚不能判斷。

| Trial／模型 | 情境 | 證據狀態／原因 | 交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `tsm-momentum-trend-volume-close-acceptance-v001`／candidate | Development/base | valid；完整 evidence | 4／4（2014、2015、2016、2018） | 2.7972% | 2.3142 | 2.1284% |
| `tsm-momentum-trend-volume-close-acceptance-v001`／candidate | Development/stress | valid；同一 Trial 的壓力成本 evidence | 4／4 | 2.0084% | 1.9478 | 2.1191% |
| `tsm-momentum-trend-volume-close-acceptance-v001`／baseline | Development/base | valid；控制組完整產出 | 16／5（2014–2018） | -0.5729% | 0.9556 | 4.5483% |
| `tsm-momentum-trend-volume-close-acceptance-v001`／baseline | Development/stress | valid；控制組壓力 evidence | 16／5 | -2.7935% | 0.7800 | 4.8322% |

**限制與更正**：已發布登記文字仍寫 0.65／0.10，實際結構化規格、contract、程式及證據綁定為 0.48／0.01；不得把本結果當作 0.65／0.10 假說的試驗。缺陷不可回寫或重跑修正。

**下一步**：另立 Study，只改收盤承接門檻家族，先對齊登記文字與結構化規格；有效證據、至少 20 筆／3 年及全部正式門檻通過，否則停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1819–1848 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1819)。
更正定位：[Parent review 回修更正（2026-09-20）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1844)。

<a id="study-39"></a>
## `tsm-momentum-trend-volume-return-alignment--v001`

**研究與差異**：前五日量能加權收盤報酬≥-0.02，且加權減未加權≥0.0005；baseline 只關閉此條件，ready index 固定 25。

**判定**：成果卡 failed；證據 valid；研究目標未登記。候選失敗交易數、stress 報酬／PF、重抽樣正報酬比例及逐年剔除 PF／報酬；baseline 另失敗 base 報酬／PF。候選不具凍結資格，兩次凍結相關嘗試失敗，實際凍結狀態尚不能判斷。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | ---: | ---: | ---: | ---: |
| `tsm-momentum-trend-volume-return-alignment-v001`／candidate | Development/base | valid／5／4（2014、2015、2016、2018） | 0.7410% | 1.1797 | 2.2588% |
| 同上／candidate | Development/stress | valid／5／4 | -0.0308% | 0.9925 | 2.5202% |
| 同上／baseline | Development/base | valid／16／5（2014–2018） | -0.5729% | 0.9556 | 4.5483% |
| 同上／baseline | Development/stress | valid／16／5 | -2.7935% | 0.7800 | 4.8322% |

**限制與更正**：目前採用更正：直接測試為 3 passed／1 failed，舊測試夾具仍要求 False，而實際為 True；runner 的 Ruff I001 未修復，只有忽略該項才通過。登記文字寫 0.20%（0.002），實測下限為 -0.02，不得宣稱測了 0.20% 假說或完整測試通過。證據仍 valid，綁定檔案未改。

**下一步**：停止原 Study，不回寫或重跑；另立並事前固定一項量能與報酬對齊替代機制，其餘不變，任一正式門檻失敗即停止凍結。

**來源與歷史**：[原卡、完整來源及更正（原第 1849–1882 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1849)。
更正定位：[驗證補充（2026-09-20）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1870)；[Parent review correction（2026-09-20；TASK-008）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1874)。

<a id="study-40"></a>
## `tsm-momentum-trend-volume-range-compression--v001`

**研究與差異**：前五日原始量加權日內區間／未加權平均區間≤1.05，且平均量比≥1.05，再由趨勢及至少 2% 漲幅確認；baseline 只關閉壓縮條件。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選失敗 base／stress 報酬及 PF、交易數、stress 重抽樣正報酬比例、逐年剔除 PF／報酬及年度（2<3）；baseline 亦失敗核心及壓力門檻。候選不具資格，readiness／freeze 回 qualification-failed，實際凍結狀態為未完成／尚不能判斷。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬 | PF | 最大回撤 |
| --- | --- | ---: | ---: | ---: | ---: |
| candidate | Development/base | valid／5／2（2016、2018） | -2.4766% | 0.4663 | 2.4766% |
| candidate | Development/stress | valid／5／2 | -3.0025% | 0.3645 | 3.0025% |
| baseline | Development/base | valid／16／5（2014–2018） | -0.5729% | 0.9556 | 4.5483% |
| baseline | Development/stress | valid／16／5 | -2.7935% | 0.7800 | 4.8322% |

**限制與更正**：與 efficiency 共用區間比值家族；差異為相反方向的≤1.05 壓縮條件及五日量比，不能宣稱公式全新或完全獨立。樣本僅兩年，無法把弱結果歸因單一門檻。

**下一步**：另立 Study，事前固定新機制或相反方向的市場狀態定義；有效證據、至少 20 筆／3 年且全部正式門檻通過，否則停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1883–1910 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1883)。
更正定位：[Parent review 澄清（2026-09-21）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1903)。

<a id="study-41"></a>
## `tsm-momentum-trend-volume-gap-anchoring--v001`

**研究與差異**：前五日量能加權隔夜缺口≤-0.20%、負缺口量能占比≥10%、平均量比≥1.05，再由趨勢及至少 2% 漲幅確認；比較條件採相同價格與執行。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選失敗交易數、stress 逐年剔除報酬及年度；baseline 失敗 base／stress 報酬與 PF、交易數及 stress 穩健性。候選不具資格，readiness／freeze 回 qualification-failed，實際凍結狀態尚不能判斷。

| 模型／情境 | evidence／交易數／年 | 報酬 | PF／最大回撤 |
| --- | ---: | ---: | ---: |
| candidate／base | valid／3／1（2018） | 0.8092% | 1.3936／1.9988% |
| candidate／stress | valid／3／1 | 0.3189% | 1.1558／1.9995% |
| baseline／base | valid／16／5（2014–2018） | -0.5729% | 0.9556／4.5483% |
| baseline／stress | valid／16／5 | -2.7935% | 0.7800／4.8322% |

**限制與更正**：三筆集中 2018 年，正結果不能證明策略有效；仍共用日線量價資料及五日窗口。preflight 的人工歷史分支不是正式評估結果。

**下一步**：另立 Study，只改成五日中至少三日負隔夜缺口，其餘不變；有效證據、至少 20 筆／3 年及全部正式門檻通過，否則停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1911–1929 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1911)。

<a id="study-42"></a>
## `tsm-momentum-trend-volume-persistence--v001`

**研究與差異**：Study 名稱為 persistence，唯一 Trial 名為 tsm-momentum-trend-volume-fade-v001；前五日平均量比≥1.05，最新／最早量 V[t-1]／V[t-5]≤1.00，baseline 只關閉量能衰減條件。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選只失敗交易數（3<20）及年度（2<3）；baseline 失敗交易數、stress 重抽樣正報酬比例及逐年剔除 PF／報酬。候選不具資格，readiness／freeze 回 qualification-failed，未產生 candidate-frozen，原卡凍結狀態記為尚不能判斷。

| 模型／情境 | evidence／交易數／年度 | 報酬 | PF／最大回撤 |
| --- | ---: | ---: | ---: |
| candidate／base | valid／3／2（2015、2018） | 4.8247% | inf／0% |
| candidate／stress | valid／3／2 | 4.0260% | inf／0% |
| baseline／base | valid／10／4（2014–2018 中四年） | 2.1411% | 1.3059／2.128% |
| baseline／stress | valid／10／4 | 0.5312% | 1.0756／2.275% |

**限制與更正**：三筆集中 2015、2018；baseline 重抽樣正報酬比 0.5991、逐年剔除 PF 0.8456／報酬 -1.0733% 亦未達標。無法將小樣本正結果歸因於衰減機制。

**下一步**：另立 Study，事前固定唯一替代量先價機制；有效證據、至少 20 筆／3 年及全部正式門檻通過，不在原 Study 調參或重跑。

**來源與歷史**：[原卡、完整來源及更正（原第 1930–1951 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1930)。
更正定位：[Parent review 欄位補充（同一張成果卡）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1945)。

<a id="study-43"></a>
## `tsm-momentum-trend-volume-peak-lead--v001`

**研究與差異**：五日視窗內量比峰值至少早於收盤報酬峰值一日，再由當日趨勢及加速確認；核心差異是峰值先後，仍共用日線量價資料限制。

**判定**：成果卡 failed；兩組證據 valid；研究目標未登記。候選失敗 base／stress 報酬及 PF、交易數、stress 重抽樣正報酬比例、逐年剔除報酬及年度；baseline 失敗交易數及三項 stress 穩健性。候選不具資格，readiness／freeze 回 qualification-failed，未產生 candidate-frozen；凍結來源仍非 verified-clean。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬／PF／最大回撤 |
| --- | --- | ---: | ---: |
| candidate `tsm-momentum-trend-volume-peak-lead-v001` | base | valid／1／1（2018） | -1.9986%／0／1.9986% |
| 同上 | stress | valid／1／1（2018） | -2.0000%／0／2.0000% |
| baseline `tsm-momentum-trend-volume-peak-lead-v001-baseline` | base | valid／10／4（2014、2015、2016、2018） | 2.1411%／1.3059／2.1279% |
| 同上 | stress | valid／10／4 | 0.5312%／1.0756／2.2747% |

**限制與更正**：只有一筆、一年，不能由虧損或 baseline 較好判斷跨期效果；日線資料也不能辨識盤中主動買賣。

**下一步**：另立且事前固定一個不同量先價機制，保留資料、成本、風控及 baseline；有效證據、至少 20 筆／3 年及全部正式門檻通過，否則停止。

**來源與歷史**：[原卡、完整來源及更正（原第 1952–1970 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1952)。

<a id="study-44"></a>
## `tsm-momentum-trend-volume-breadth--v001`

**研究與差異**：前五日平均單日量比≥1.05，其中至少三日的五日滾動平均量／此前二十日均量≥1.05，再由趨勢、收盤方向及至少 2% 加速確認；baseline 只關閉多日覆蓋。

**判定**：成果卡 failed；兩組證據 valid；受限盲檢討合格。候選只失敗交易數正式門檻；研究目標交易數失敗，stress 報酬及年度通過。Baseline 失敗交易數與三項 stress 穩健性門檻，候選研究目標不適用於 baseline。候選不具資格，readiness／freeze 回 qualification-failed，未產生 candidate-frozen；原記錄階段 trial-recorded。

| Trial／情境 | evidence／交易數／交易年數 | 報酬／PF／最大回撤 |
| --- | --- | --- |
| candidate／base | valid／7／3 | 0.0718974225／4.2883682633／0.0199898809 |
| candidate／stress | valid／7／3 | 0.0559591924／3.5981105326／0.0199892960 |
| baseline／base | valid／10／4 | 0.0214113763／1.3058563599／0.0212790741 |
| baseline／stress | valid／10／4 | 0.0053120034／1.0755804379／0.0227468297 |

**限制與更正**：七筆集中 2015（1）、2016（1）、2018（5）；重抽樣正報酬比最低 0.94038 也不能抵銷小樣本。baseline 不穩健，不能證明候選的因果優勢。表中報酬及回撤沿用原文小數比例，未換算百分比。

**下一步**：另立並事前固定一項變更；兩組證據有效，候選至少 20 筆／3 年、全部正式門檻及已登記目標通過，否則停止，不在原 Study 重跑。

**來源與歷史**：[原卡、完整來源及更正（原第 1971–1988 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1971)。

<a id="study-45"></a>
## `tsm-momentum-trend-volume-response-lag--v001`

**研究與差異**：以 d 日成交量配對 d→d+1 收盤報酬，五個已完成配對的加權報酬≥-0.02，且高於未加權平均至少 0.0005；baseline 只關閉跨日量與次日報酬傳導。

**判定**：候選 disposition=fail；兩組證據 valid；受限盲檢討完成。候選失敗 base／stress 報酬及 PF、交易數、stress 重抽樣正報酬比、逐年剔除報酬及年度；交易數、stress 報酬、年度三項研究目標全失敗。Baseline 失敗交易數及三項 stress 穩健性正式門檻；原表 target 診斷僅屬控制組比較。候選不具資格，readiness／freeze 回 qualification-failed，未凍結、階段 trial-recorded。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬／PF／最大回撤 |
| --- | --- | ---: | ---: |
| candidate | Development/base | valid／1／1（2018） | -1.9986088%／0／1.9986088% |
| candidate | Development/stress | valid／1／1（2018） | -1.9999960%／0／1.9999960% |
| baseline（控制組） | Development/base | valid／10／4（2014、2015、2016、2018） | 2.1411376%／1.3058564／2.1279074% |
| baseline（控制組） | Development/stress | valid／10／4 | 0.5312003%／1.0755804／2.2746830% |

**限制與更正**：唯一候選交易在 2018 停損；無法估計跨日承接的獨立效果。證據綁定一致，沒有缺件；已達唯一 Trial 上限，不能回原 Study 重跑。

**下一步**：另立並事前固定新 Study，資料、成本、風控、baseline 相同；候選須同時達至少 20 筆／3 年及 stress 報酬>0，任一未達即否證並停止凍結。

**來源與歷史**：[原卡、完整來源及更正（原第 1989–2005 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:1989)。

<a id="study-46"></a>
## `tsm-momentum-trend-volume-body-followthrough--v001`

**研究與差異**：前五日同日 Close/Open−1 的成交量加權平均≥0，且不低於同窗未加權平均；baseline 只關閉日內實體條件。

**判定**：候選 disposition=fail；兩組證據 valid；盲檢討 exposure check 通過。候選只失敗交易數正式門檻及同項研究目標，stress 報酬及年度目標通過；baseline 失敗交易數及三項 stress 穩健性，candidate targets 不適用。候選不具資格，readiness／freeze 回 qualification-failed，未產生 candidate-frozen。

| Trial／模型 | 情境 | evidence／交易數／年度 | 報酬／PF／最大回撤 |
| --- | --- | ---: | ---: |
| candidate | Development/base | valid／3／3（2015、2016、2018） | 5.0316%／inf／0% |
| candidate | Development/stress | valid／3／3 | 4.2172%／inf／0% |
| baseline（控制組） | Development/base | valid／10／4（2014、2015、2016、2018） | 2.1411%／1.3059／2.1279% |
| baseline（控制組） | Development/stress | valid／10／4 | 0.5312%／1.0756／2.2747% |

**限制與更正**：三筆全正、PF 無限大及零回撤不能取代足量樣本。assignment 仍寫高 0.05 個百分點，實測差值下限是 0，不得宣稱測了 0.05% 假說。v012 已用過單日未加權 Close>Open；本次差異限五日窗口、量權重及動能情境，非概念首創。

**下一步**：另立 Study，只改成事前固定的正實體成交量占比，其餘不變；至少 20 筆／3 年且全部正式門檻通過，否則停止。

**來源與歷史**：[原卡、完整來源及更正（原第 2006–2025 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2006)。
更正定位：[Parent review clarification（2026-09-22）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2022)。

<a id="study-47"></a>
## `tsm-momentum-trend-volume-body-sign-consistency--v001`

**研究與差異**：前五日 Close≥Open 的成交量占比≥0.60，另保留五日量比≥1.05；平盤歸入非負類。與前卡加權平均不同，也不是首次使用 Open→Close 概念。

**判定**：採更正後內容：baseline 證據可取得且 valid，原 unavailable 已更正；candidate 亦 valid。候選失敗交易數、stress 逐年剔除 PF／報酬；研究目標交易數失敗。Baseline disposition=fail，失敗交易數、stress 重抽樣正報酬比例及逐年剔除 PF／報酬，候選研究目標及凍結資格不適用。候選資格 false，readiness／freeze 回 qualification-failed，trial-recorded／未凍結；盲檢討 exposure check 通過。

| 模型／情境 | 交易數 | 報酬（比例） | PF | 最大回撤（比例） |
| --- | ---: | ---: | ---: | ---: |
| candidate／base | 3 | 0.006977421424769781 | 1.3278289105815337 | 原更正未列 |
| candidate／stress | 3 | 0.0021563831144390576 | 1.10176033923166 | 原更正未列 |
| baseline／base | 10 | 0.021411376349155745 | 1.305856359872508 | 0.021279074115623766 |
| baseline／stress | 10 | 0.0053120033963509694 | 1.0755804379115148 | 0.022746829677724723 |

**限制與更正**：候選只有三筆，baseline 亦未通過穩健性，不能歸因單一門檻或年度。更正只補固定 baseline／publication／inputs；未重跑或修改綁定，event head/count 仍 unavailable。表中報酬及回撤採更正段的小數比例。

**下一步**：另立 Study，只改為前五日至少三日 Close≥Open，其餘不變；任一正式門檻或研究目標失敗即停止凍結。

Baseline 有交易年度為 4 年；候選年度與未列指標不由其他卡補入。

**來源與歷史**：[原卡、完整來源及更正（原第 2026–2037 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2026)。
更正定位：[Parent review correction（2026-09-22）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2032)。

<a id="study-48"></a>
## `tsm-momentum-trend-volume-lagged-neutral-impulse--v001`

**研究與差異**：恰好 t−5 的中性日量比≥1.50，Close/Open 與 Close/前收絕對變化皆≤0.5%；後四日量≤事件量一半且無單日上漲達 2%，再以訊號日加速確認。baseline 只關閉該事件序列。

**判定**：兩組證據 valid；候選 disposition=fail，0 筆／0 年，報酬與 PF 不可估計，13 項正式門檻及三項研究目標全失敗。Baseline 失敗 8 項正式門檻：base／stress 報酬及 PF、交易數、stress 重抽樣正報酬比例及逐年剔除 PF／報酬；baseline 研究目標不適用。候選資格 false，readiness／freeze 回 qualification-failed，沒有凍結及 freeze operation ID；盲檢討程序未通過。

| 模型 | Development 結果 |
| --- | --- |
| candidate | valid；0 筆／0 年；base、stress 報酬及 PF 均不可估計 |
| baseline | valid；16 筆／5 年。base 報酬 `-0.5729%`、PF `0.9556`、最大回撤 `4.5483%`；stress `-2.7935%`、PF `0.7800`、最大回撤 `4.8322%` |

**限制與更正**：搜尋 checker 時越界輸出四個鄰近 Study 的 assignment 設計片段；未讀那些結果，但仍超出單 Study 範圍，已停止且未重試，不可補稱 passed。規格同時留舊 volume_lagged_neutral_impulse／retest_* 及新 lagged_neutral_volume_impulse；engine 只使用新 key，登記歧義未回改。

**下一步**：另立 Study 前先清除未用舊欄位，固定候選及 baseline；有效證據、至少 20 筆／3 年、stress 報酬>0 及全部正式門檻、研究目標通過，否則停止，不授權原 Study 重跑。

**來源與歷史**：[原卡、完整來源及更正（原第 2038–2063 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2038)。
更正定位：[成果卡補充（同一張卡，2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2052)；[Parent review correction（同一成果卡，2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2058)。

<a id="study-49"></a>
## `tsm-momentum-trend-volume-gap-retention--v001`

**研究與差異**：前五日平均量比≥1.05，訊號日正向開盤缺口≥0.50% 且收盤不低於開盤；baseline 只關閉缺口接受條件，其餘趨勢與至少 2% 加速固定。

**判定**：兩組證據 valid。候選失敗 base PF、交易數、stress 重抽樣正報酬比、逐年剔除 PF／報酬及 stress PF／報酬；研究目標交易數與 stress 報酬失敗、年度通過。Baseline 失敗交易數及三項 stress 穩健性。候選資格 false、未凍結；盲檢討未通過且未重試。

| 模型 | 交易數／年 | base 報酬／PF | stress 報酬／PF |
| --- | --- | --- | --- |
| candidate | 9／3 | 0.2327%／1.0337 | -1.0725%／0.8457 |
| baseline | 10／4 | 2.1411%／1.3059 | 0.5312%／1.0756 |

**限制與更正**：採最新更正：遞迴搜尋掃過整個 v004 workflow，輸出含範圍外 events／study.yml 路徑與事件摘要；不能保證沒有附帶掃描。輸出僅用來識別越界並停止，未用於策略分析或研究結論，未引用正式結果；不能沿用原卡全面未讀聲明。九筆不足以判定因果。

**下一步**：另立 Study，事前固定一項缺口接受變更，重新驗證樣本與 stress 門檻；不在本 Study 調參或重跑。

**來源與歷史**：[原卡、完整來源及更正（原第 2064–2084 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2064)。
更正定位：[成果卡補充／Parent review correction（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2072)；[成果卡補充／Parent review correction 2（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2081)。

<a id="study-50"></a>
## `tsm-momentum-trend-volume-path-efficiency--v001`

**研究與差異**：量比加權五日收盤淨位移絕對值／缺口加日內區間總路徑≥0.20。登記仍留 3/5 breadth 文字，因此此條件究竟取代或追加 breadth，尚不能判定，不選其中一種當成已登記意圖。

**判定**：兩組證據 valid。候選失敗交易數（6<20）、stress 重抽樣正報酬比（0.7193<0.80）；研究目標交易數失敗、stress 報酬及年度通過。Baseline 失敗交易數、stress 重抽樣正報酬比、逐年剔除 PF／報酬；候選目標及凍結資格不適用。候選資格 false，trial-recorded／未凍結，未嘗試 readiness／freeze。

| Trial／情境 | 交易數 | 報酬 | PF | MDD（最大回撤） | Evidence validity |
| --- | ---: | ---: | ---: | ---: | --- |
| Candidate／base | 6 | +3.318876% | 2.186381 | 2.324947% | valid |
| Candidate／stress | 6 | +2.194951% | 1.764773 | 2.582898% | valid |
| Baseline／base | 10 | +2.141138% | 1.305856 | 2.127907% | valid |
| Baseline／stress | 10 | +0.531200% | 1.075580 | 2.274683% | valid |

**限制與更正**：盲檢討 eligible／完成不等於設計無缺陷：登記留舊假說、contract 綁 volume_coverage_ratio 但 engine 輸出 prior_volume_ratio、docstring 稱方向效率而公式取絕對值，三項均未改。證據 valid 不證明規格與程式一致。來源指紋採 2026-09-23 最後一次逐字更正的完整值，保留 63／64 位差異紀錄。

**下一步**：另立 Study，在建立前釐清取代或追加、修正登記／contract／docstring 綁定；候選至少 20 筆並通過全部正式門檻及事前目標，否則否證，不在本 Study 補跑。

**目前採用的 baseline 證據指紋**：`db4ee9bfb36b0d9e11b5d1f5e7586b33ae1f4edd551c1268e190cfcf3fe2f868`（64 位；完整更正見歷史紀錄）。

**來源與歷史**：[原卡、完整來源及更正（原第 2085–2123 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2085)。
更正定位：[Parent review correction（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2092)；[Parent review digest correction（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2115)；[Parent review exact digest correction（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2119)。

<a id="study-51"></a>
## `tsm-momentum-trend-volume-breadth-dispersion--v001`

**研究與差異**：保留原 3/5 breadth，再加訊號日前五日最大單日原始量／五日總量≤60%；baseline 不加。既有卡未見同一上限，不代表組件首創或具獨立因果效果。

**判定**：兩組證據 valid；各 13 項正式門檻，唯一失敗均為交易數（7<20），其餘 12 項通過。候選研究目標：交易數失敗、stress 報酬>0 及年度≥3 通過；baseline 無候選目標。候選資格 false，trial-recorded／未凍結，未嘗試 readiness／freeze；盲檢討 eligible／完成。

| 臂別／情境 | 完成交易 | 有交易年份 | 報酬 | PF | 最大回撤 MDD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Candidate／base | 7 | 3 | 7.189742% | 4.288368 | 1.998988% |
| Candidate／stress | 7 | 3 | 5.595919% | 3.598111 | 1.998930% |
| Baseline／base | 7 | 3 | 7.189742% | 4.288368 | 1.998988% |
| Baseline／stress | 7 | 3 | 5.595919% | 3.598111 | 1.998930% |

**限制與更正**：兩組交易及指標完全相同，60% 上限沒有排除已接受訊號，不能支持改善。初稿 35% 因人工測試資料 5/9=55.6% 而在建立 Study 前改為 60%；當時未建立 Study、未跑 Development，最終僅建立一次、執行一個 Trial。

**下一步**：另立 Study，事前選足夠原 breadth 訊號的資料範圍，候選至少 20 筆／3 年，且 60% 規則須排除至少一筆事前定義的 baseline 訊號；任一條件、正式門檻或研究目標未達即停止，不依結果調整上限。

**來源與歷史**：[原卡、完整來源及更正（原第 2124–2166 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2124)。
更正定位：[Parent review correction／同一成果卡補充：`tsm-momentum-trend-volume-breadth-dispersion--v001`（2026-09-23）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2131)。

<a id="study-52"></a>
## `tsm-industry-relative-lag-repair--v001`

**研究與差異**：在 v009 加入 SOXX 五個 XNYS 交易日漲幅>0、TSM 落後≥3 個百分點的條件，次日買進；對照為 v009。

| 模型 | base 報酬／PF／MDD | stress 報酬／PF／MDD |
| --- | --- | --- |
| candidate | 28.783%／2.005／6.955% | 18.245%／1.646／7.674% |
| v009 | 33.676%／5.036／1.9998% | 26.523%／4.204／2.119% |

**判定**：兩份證據有效、publication 指紋綁定。候選正式門檻通過 10/11，唯一失敗為壓力重抽樣 MDD>10% 比率 19.848%>10%；v009 全過。研究目標至少 20 筆／3 年，候選 47 筆／5 年通過。凍結資格 false；實際凍結狀態尚不能判斷，未執行 freeze／readiness。

**自訂目標與限制**：TASK-023 的自訂目標不是 v005 門檻：不重疊新增 26 筆≥5 通過；扣除排擠後壓力淨增益 -$8,278.22<0，MDD 7.674%>v009 2.119%。SOXX 僅一檔參考資產，訊號期僅 2014–2018，因果及跨期效果未知。盲檢討完成，未讀正式結果或 Study 狀態資料。

**資料**：SOXX 作參考、TSM 作交易資產；均為 Yahoo 日線調整價，America/New_York 時區、按 XNYS 對齊，收盤後可用；資料期 2013-01-02–2018-12-31，訊號期 2014-01-01–2018-12-31、暖機標示 2013-01-01–2013-12-31。逐檔 SHA-256 與 publication 資產清單指紋是不同項目，完整值見歷史來源。

**下一步**：另立並事前登記；正式門檻全過、壓力淨增益>0、MDD≤v009 須同時成立，否則否證。

**來源與歷史**：[原卡、完整來源及更正（原第 2167–2181 行）](/Users/william/.codex/worktrees/3256/trading-2026-2/.study-developer/development-note/TSM-history-before-condensation-2026-09-26.md:2167)。
