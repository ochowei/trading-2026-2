from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from trading_2026_2.tsm_mean_reversion_divergence_atr_gap_filter_v001 import ATR_GAP_FILTER_SPEC, BASE_COST, CONTROL_SPEC, STRESS_COST, backtest
from validator.artifacts import _recompute_development, empty_development_result
from validator.canonical_yaml import canonical_digest, load_canonical, write_canonical
from validator.metrics import compare

def bars_from_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=['Date'])
    if list(frame.columns) != ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']:
        raise ValueError('Development CSV must have the fixed OHLCV columns')
    return frame.set_index('Date')

def text(value: float) -> str:
    return repr(float(value))

def trade_records(base_trades, stress_trades, prefix: str, initial_cash: float):
    if len(base_trades) != len(stress_trades):
        raise ValueError(f'{prefix} base/stress trade count differs')
    output=[]; equity={'base':initial_cash,'stress':initial_cash}
    for index,(base,stress) in enumerate(zip(base_trades,stress_trades,strict=True),start=1):
        if (base.signal_session,base.entry_session,base.exit_session,base.exit_reason)!=(stress.signal_session,stress.entry_session,stress.exit_session,stress.exit_reason):
            raise ValueError(f'{prefix} base/stress lifecycle differs')
        row={'trade_id':f'{prefix}-{index:04d}','signal_session':base.signal_session.date().isoformat(),'entry_session':base.entry_session.date().isoformat(),'exit_session':base.exit_session.date().isoformat(),'exit_reason':base.exit_reason,'held_sessions':int(base.held_sessions)}
        for label,trade in (('base',base),('stress',stress)):
            pre=equity[label]
            row[label]={'executed_entry_price':text(trade.executed_entry_price),'executed_exit_price':text(trade.executed_exit_price),'fees':text(trade.fees),'pnl':text(trade.pnl),'pnl_fraction_of_pre_entry_equity':text(trade.pnl/pre),'shares':int(trade.shares)}
            equity[label]+=trade.pnl
        output.append(row)
    return output

def run_arm(bars,spec,inputs,prereg,source_bundle,model_id,prefix):
    initial=float(prereg['initial_cash'])
    spec=spec.with_changes(mean_reversion_min=0.015,rsi_max=50.0,volume_spike_ratio=1.05,holding_sessions=10,cooldown_sessions=5,stop_return=-0.04,target_return=0.04,risk_fraction=0.02,initial_cash=initial)
    controls=inputs['date_controls']
    base=backtest(bars,spec=spec,cost=BASE_COST,signal_start=controls['signal_start'],signal_end=controls['signal_end'])
    stress=backtest(bars,spec=spec,cost=STRESS_COST,signal_start=controls['signal_start'],signal_end=controls['signal_end'])
    trades=trade_records(base.trades,stress.trades,prefix,initial)
    evidence={'schema_version':1,'stage':'development','candidate_id':model_id,'bindings':{'preregistration_digest':canonical_digest(prereg),'source_bundle_digest':canonical_digest(source_bundle),'trial_inputs_digest':canonical_digest(inputs)},'trades':trades,'network_access_during_run':False}
    if not trades:
        return {**evidence,**empty_development_result(prereg)}
    evidence['accepted_signal_count']=len(trades)
    metrics,diagnostics,actuals=_recompute_development(evidence,prereg)
    gates=[]
    for name,rule in prereg['eligibility_rules']['development_gates'].items():
        actual=actuals[name]; passed=compare(actual,rule['operator'],rule['value'],metric=name)
        gates.append({'gate':name,'operator':rule['operator'],'required':rule['value'],'actual':actual,'passed':passed})
    failed=[item['gate'] for item in gates if not item['passed']]
    return {**evidence,'metrics':metrics,'diagnostics':diagnostics,'gates':gates,'failed_gates':failed,'disposition':'fail' if failed else 'pass'}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--request',required=True); parser.add_argument('--output',required=True); args=parser.parse_args()
    request=load_canonical(args.request)
    if request['stage']!='development': raise ValueError('Development runner only accepts development requests')
    bars=bars_from_csv(Path(request['data_path'])); inputs=request['trial_inputs']; prereg=request['preregistration']; bundle=request['source_bundle']
    candidate=run_arm(bars,ATR_GAP_FILTER_SPEC,inputs,prereg,bundle,inputs['candidate_id'],'candidate')
    baseline=run_arm(bars,CONTROL_SPEC,inputs,prereg,bundle,prereg['baseline_definition']['baseline_id'],'baseline')
    write_canonical(args.output,{'candidate':candidate,'baseline':baseline})

if __name__=='__main__': main()
