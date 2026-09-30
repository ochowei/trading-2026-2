# TASK-036 prepare-before checkpoint

**目前狀態：等待 PM 審核。** 本 checkpoint 已完成設計落檔、source/config 綁定、靜態與 schema 檢查，以及隔離 synthetic runner-preflight。Native `precreate` 僅因兩個 synthetic fixture 無法滿足 Candidate 訊號條件而失敗，細節見下文。未呼叫 `prepare`、`create` 或正式 Development；沒有建立正式 Study、event 或 lifecycle operation。請 PM 審核此限制並決定是否授權下一步。

## 研究設定與授權身分

- Study ID：`tsm-divergence-sma20-sma50-regime--v001`
- Candidate：`tsm-mr-v009-sma20-over-sma50-regime-v001`
- 固定 Control：`tsm-mr-v009-two-stage-volume-reversal-control-task036-v001`
- 唯一策略差異：Control 使用 v009 原始完整 `DEFAULT_SPEC`；Candidate 只在同一組原始訊號上增加訊號日 SMA(20) 嚴格高於 SMA(50) 的條件。沒有增加 SMA(50) 斜率、動能或其他 filter，也沒有依 TASK-035 表現調整規則。
- SMA 使用 Yahoo auto-adjusted Close 與 XNYS 已完成交易 session 的簡單移動平均，兩者都納入訊號日收盤；SMA(50) 未就緒或兩者相等時拒絕 Candidate 訊號，不讀取訊號日後資料。其餘超跌、RSI、量能、收盤方向、進出場、持有、停損／停利、冷卻、風險、成本及執行規則照完整 v009 `DEFAULT_SPEC`。
- 身分精確值：`research_owner=ochowei@gmail.com`、`historical_evaluation_operator=operator A`。
- 派工：`.study-developer/assignments/TASK-036-v005.yml`；已 canonicalize，SHA-256 `308a2b80aa35521c16cd4b50173f5c274d276c0e0fbddf512aa81ec2f3ce3f8b`。角色 `study 開發者`、workflow v005、scope `development-to-freeze`。
- Study 唯一性：先前設計檢查未找到相同 Study 或相同 SMA20/SMA50 設計；本次再確認正式目錄 `workflows/strategy-forward-replication-research--v005/studies/tsm-divergence-sma20-sma50-regime--v001` 不存在。

## 資料與 workflow 綁定

- 唯一允許的價格檔：`research/market-data/yahoo/TSM-warmup-development--sha256-a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7.csv`，SHA-256 `a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`。範圍固定為 warmup 2013-01-01–2013-12-31 與 Development 2014-01-01–2018-12-31；設定為 Yahoo、TSM、America/New_York、after-close、warmup-development，未使用正式 provider 存取。此 checkpoint 的合成 runner-preflight 使用記憶體／暫存 synthetic rows，不讀其他市場資料。
- Active workflow：`strategy-forward-replication-research` v005，package `workflows/strategy-forward-replication-research--v005`；workflow digest `2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`；release manifest `workflows/strategy-forward-replication-research--v005/release-manifest.yml` digest `6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`；Policy set digest `c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`；workflow-reference digest `40396c0c742a653a589c5bfb738358149ae7c4302e55dc732362975902af3b90`。Runner report 的綁定欄位亦記錄相同的 v005、workflow、release、Policy 與 reference digest。

## Gates 與設定 digest

Development qualification 仍是原定 13 gates，沒有新增或調整；`research_targets: {}`。門檻為：`base_profit_factor > 1.10`、`base_return > 0`、`completed_trades >= 20`、`maximum_realized_trade_loss_fraction <= 0.04`、`maximum_stress_block_bootstrap_drawdown_above_10pct_ratio <= 0.10`、`maximum_stress_leave_one_year_out_drawdown <= 0.10`、`minimum_stress_block_bootstrap_positive_return_ratio >= 0.80`、`minimum_stress_leave_one_year_out_profit_factor > 1.00`、`minimum_stress_leave_one_year_out_return > 0`、`stress_maximum_drawdown <= 0.10`、`stress_profit_factor > 1.00`、`stress_return > 0`、`traded_years >= 3`。

| 固定檔案 | SHA-256 |
|---|---|
| `preregistration.yml` | `7e837d35bf1e48082ea751ac0d24e8460859e0611221cf9c966993a0dd542154` |
| `candidate-definition.yml` | `a732be072bf435b2f4cfc5842729f56ad2c1ba05d2235bb9d260848d8fdf13f8` |
| `implementation-contract.yml` | `8295f8834920f69fd5f38c800f6e76a78f1160140beb7982a12f1ba867012140` |
| `qualification-spec.yml` | `d95db264fdb5b4bc116c190f4ecac664922695387ef3c1c8d941fe7b35a730db` |
| `runner-contract.yml` | `accbbc6674cb5a52b7aa6e56885cfeb9d95ba2a78e310dfceddfdc785b11f22f` |
| `development-trial-inputs.yml` | `aa5e55b3214f81833525c04ffd36896a7a51df50e66d3415e18cf09026427097` |
| `source-bundle.yml` | `b9b814f9ddbadc0a05db1dc69818e37b89a29fcb43cf75a8d8db3a6d7e3bcb68` |
| `run_development.py` | `dc9245ffce87e41e27ca9e84ffdfb1561c25425bce44e4a3dccaa157942c1b3a` |
| `synthetic_preflight.py` | `e7427ef77581c07a7bcf3e52e781565532c54843311bf33910476e8c4b8608aa` |
| Candidate engine | `4d0f756827e137b673b2975d654696caeeabd0d46a9e1f44dfa2dae8f5d14888` |
| v009 Control engine | `f3163c9b92046d0397ce1daf0cfb320a302c9e994875a4be0e93057a83cef7c4` |

`source-bundle.yml` 列出的 11 個來源檔均已逐一重算 SHA-256，全部與 manifest 相符。其餘 cross-binding 包括：trial inputs 綁定上述 preregistration、SourceBundle、Candidate engine、runner；runner-preflight report 的 settings 也逐項使用相同 digest。digest 索引檔 `prepare-before-digest-summary.yml` SHA-256 為 `c1672ddd2fcdee5f23dc0bfc65cdb5b7d1aef537c23f75a626ee7fca262e55da`。

## 檢查結果

1. **Canonical YAML／schema 與靜態檢查：通過。** preregistration、SourceBundle、runner contract 等 v005 schema 檢查通過；其餘 candidate definition、qualification spec、trial inputs、implementation contract 均可 canonical load。Native precreate 的 contract 檢查通過；SourceBundle 11/11 檔案 digest 驗證成功，身份、研究輸入、參數、持有／冷卻／停損／停利及 gate 綁定檢查通過。
2. **Candidate 專屬 synthetic preflight：通過。** 命令 `./.venv/bin/python research/tsm-divergence-sma20-sma50-regime--v001/synthetic_preflight.py` 輸出：`synthetic_preflight: PASS; above/below/equal/unready and future-perturbation; candidate/control execution parity`。覆蓋趨勢高於、低於、相等、SMA(50) 未就緒、訊號日後資料擾動，以及通過 filter 時 Candidate／Control 的成交執行一致性。
3. **Native precreate：失敗，只有兩筆 fixture-invalid。** 命令 `./.venv/bin/python research/tools/studyctl.py --repository-root . --authority-root .authority precreate tsm-divergence-sma20-sma50-regime--v001` 回傳 `status=failed`、`error_count=2`、`warning_count=0`。唯一兩筆錯誤均為 `synthetic-fixture-invalid`：
   - `signal`：`signal case 失敗：synthetic fixture 無法依 implementation contract 產生可接受的 raw signal；這是 fixture-invalid，不能只用交易數量不符帶過`。
   - `holding-cooldown`：`holding/cooldown case 失敗：holding/cooldown fixture 無法同時形成兩個 raw signal 與兩筆合法交易；請先區分 fixture 無法滿足條件，或策略實作沒有按 contract 接受 signal`。

   precreate 的 `contract` subcheck 通過，`synthetic` subcheck 因上述兩筆失敗。這是既有 native checker fixture 在新增嚴格趨勢條件後無法構造對應合成訊號／交易的限制；保留結果，未修改 `studyctl` 或 workflow code，也未把 precreate 描述為通過。

4. **v005 隔離 runner-preflight：通過。** 使用 `--role 'study 開發者'` 執行 runner-preflight；報告為 [runner-preflight-report.yml](runner-preflight-report.yml)，SHA-256 `d74ccef98382b883fb176c959c099a89c51b053f3c3eb5315c63890d7c4c135a`，頂層 `status=passed`，四個 synthetic case 均完成：Development trades（Candidate/Control 各 1 筆）、Development no-trades（Candidate 0、Control 1）、Historical-runner synthetic trades（Candidate 1）、Historical-runner synthetic no-trades（Candidate 0）。後兩者只驗證隔離 runner 介面，不是正式 Historical Evaluation。報告記錄的少量 gate failure 是刻意極小 synthetic fixture 的預期結果，runner output 與 evidence/schema 驗證通過。

## 邊界與停點

- Native precreate 與 runner-preflight 沒有建立正式 Study、event、operation 或 Study 狀態檔；正式 v005 Study 目錄經檢查不存在。runner-preflight 的 synthetic consumer 在隔離暫存目錄執行。
- 未執行 `prepare`、`create`、正式 Development、freeze、Historical Evaluation、Terminal、challenge 或 replay。未讀取 `historical-evaluation-artifacts/`、`.super-admin/`、quarantine 或正式 Evaluation/Terminal 證據。
- TASK-036 維持 Doing。此文件提交 PM review 後停止；需要 PM 另行明確授權才可進入下一個操作階段。
