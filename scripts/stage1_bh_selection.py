"""Resolve the existing 2014 candidates without selecting on later returns.

Unquoted ON classes have no observable market price. Their PN proxy and a
2x-ON-price sensitivity are explicit conventions, never claimed as exact values
or mathematical valuation bounds. Leaders have contemporaneous quoted classes.
"""
import csv
from datetime import date
import json
from stage1_pit import OUT,dump


def run():
    rows=list(csv.DictReader((OUT/'market_cap_2014.csv').open()))
    missing={r['cnpj']:r['quote'] for r in json.loads((OUT/'bh_missing_class_quotes_pit.json').read_text())}
    ranking=[]
    for r in rows:
        if not r['block']:continue
        x=r.copy();t=r['ticker'];on=float(r['on_shares'] or 0);pn=float(r['pn_shares'] or 0)
        op=float(r['on_price'] or 0);pp=float(r['pn_price'] or 0)
        method='CONTEMPORANEOUS_ON_PN_QUOTES';quote_date='2014-06-30';sensitivity=None
        if t=='ELPL4':x['block']='Utilidades públicas' # electricity distribution, not equipment
        if t=='SGAS4':x['block']='Utilidades públicas' # gas distribution
        if t=='SANB4':
            cap=float(r['market_cap_upper_bound']);method='DOCUMENTED_POST_55_TO_1_EXCLUSION_BOUND'
        else:
            if on and not op:
                q=missing[r['cnpj']]
                if q:
                    op=q['close'];quote_date=q['date'];method='LAST_OBSERVED_ON_CLOSE_BEFORE_CUTOFF'
                else:
                    op=pp;method='UNLISTED_ON_PN_PRICE_PROXY'
                sensitivity=on*op*2+pn*pp
            cap=on*op+pn*pp
        x.update(ranking_capitalization=cap,class_price_method=method,on_price_used=op or '',
                 on_quote_date=quote_date,on_quote_age_days=(date(2014,6,30)-date.fromisoformat(quote_date)).days,
                 sensitivity_double_missing_on_price=sensitivity,selected=False,block_rank=0,initial_weight=0.)
        ranking.append(x)
    for block in sorted({r['block'] for r in ranking}):
        group=sorted([r for r in ranking if r['block']==block],key=lambda r:r['ranking_capitalization'],reverse=True)
        for rank,r in enumerate(group,1):
            r['block_rank']=rank;r['selected']=rank<=2;r['initial_weight']=.125 if rank<=2 else 0.
        threshold=group[1]['ranking_capitalization']
        assert all(r['sensitivity_double_missing_on_price'] is None or r['sensitivity_double_missing_on_price']<threshold for r in group[2:])
    selected=[r for r in ranking if r['selected']]
    assert {r['ticker'] for r in selected}==set('CCRO3 WEGE3 ITUB4 BBDC4 TBLE3 CMIG4 HYPE3 RADL3'.split())
    assert len({r['cnpj'] for r in ranking})==len(ranking)
    assert all(r['capital_received']<='2014-06-30' and r['sector_received']<='2014-06-30' for r in selected)
    assert all(r['class_price_method']=='CONTEMPORANEOUS_ON_PN_QUOTES' for r in selected)
    ranking.sort(key=lambda r:(r['block'],r['block_rank']))
    dump('bh_ranking_2014.csv',ranking);dump('bh_selection_2014.csv',sorted(selected,key=lambda r:(r['block'],r['block_rank'])))
    print('2014 selected:', ', '.join(r['ticker'] for r in selected))


if __name__=='__main__':run()
