from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from trading_2026_2.tsm_mean_reversion_divergence_atr_gap_filter_v001 import ATR_GAP_FILTER_SPEC,BASE_COST,STRESS_COST,backtest
from validator.canonical_yaml import load_canonical,write_canonical

def bars_from_csv(path:Path)->pd.DataFrame:
    frame=pd.read_csv(path,parse_dates=['Date'])
    if list(frame.columns)!=['Date','Open','High','Low','Close','Volume']: raise ValueError('Historical input must have the fixed OHLCV columns')
    return frame.set_index('Date')

def text(value:float)->str: return repr(float(value))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--request',required=True); parser.add_argument('--output',required=True); args=parser.parse_args()
    request=load_canonical(args.request)
    if request['stage']!='historical-evaluation': raise ValueError('Historical runner only accepts historical-evaluation requests')
    bars=bars_from_csv(Path(request['data_path'])); prereg=request['preregistration']
    spec=ATR_GAP_FILTER_SPEC.with_changes(initial_cash=float(prereg['initial_cash']),mean_reversion_min=0.015,rsi_max=50.0,volume_spike_ratio=1.05,holding_sessions=10,cooldown_sessions=5,stop_return=-0.04,target_return=0.04,risk_fraction=0.02)
    trades=[]
    for year in range(2020,2025):
        year_bars=bars.loc[(bars.index>=f'{year}-01-01')&(bars.index<=f'{year}-12-31')]
        if year_bars.empty: continue
        base=backtest(year_bars,spec=spec,cost=BASE_COST,reset_at_start=True,signal_start=f'{year}-01-01',signal_end=f'{year}-12-31')
        stress=backtest(year_bars,spec=spec,cost=STRESS_COST,reset_at_start=True,signal_start=f'{year}-01-01',signal_end=f'{year}-12-31')
        if len(base.trades)!=len(stress.trades): raise ValueError('Historical base/stress trade count differs')
        for index,(b,s) in enumerate(zip(base.trades,stress.trades,strict=True),start=1):
            if (b.signal_session,b.entry_session,b.exit_session)!=(s.signal_session,s.entry_session,s.exit_session): raise ValueError('Historical base/stress lifecycle differs')
            trades.append({'trade_id':f'{year}-{index:04d}','fold':year,'signal_date':b.signal_session.date().isoformat(),'exit_date':b.exit_session.date().isoformat(),'order_type':'MARKET','base_pnl':text(b.pnl),'stress_pnl':text(s.pnl)})
    gates=prereg['evaluation_gates']
    write_canonical(args.output,{'schema_version':1,'stage':'historical-evaluation','initial_cash':prereg['initial_cash'],'family_wise_confidence':gates['family_wise_confidence']['value'],'stress_drawdown_limit':gates['stress_max_drawdown']['value'],'trades':trades})

if __name__=='__main__': main()
