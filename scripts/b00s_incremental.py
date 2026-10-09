"""PIT economic calculations from explicitly reviewed, sourced issuer inputs."""
import statistics

def calculate_metrics(proof, ipca):
    result={}
    if 'solidity' in proof:
        assessment=proof['solidity']
        if (type(assessment.get('proven')) is not bool or
                not assessment.get('reason') or not proof.get('evidence')):
            raise ValueError('Solidity needs an explicit sourced economic judgement')
        result['solidity_proven']=assessment['proven']
    if 'real_eps' in proof:
        p=proof['real_eps'];a=p['first'];b=p['last']
        years=b['year']-a['year']
        if years!=4 or min(a['profit'],b['profit'],a['weighted_shares'],b['weighted_shares'])<=0:
            raise ValueError('Five annual observations need four EPS growth intervals')
        growth=(b['profit']/b['weighted_shares'])/(a['profit']/a['weighted_shares'])
        result['real_eps_cagr']=(growth/(ipca[b['year'],12]/ipca[a['year'],12]))**(1/years)-1
    if 'roic' in proof:
        rows=proof['roic']['annual_inputs'];capital={}
        for r in rows:
            capital[r['year']]=r['equity']+r['interest_debt']-r['cash_and_short_investments']
        rates=[];nopat={}
        for r in rows:
            nopat[r['year']]=r['ebit']*(1-r['income_tax_expense']/r['pretax_income'])
            if r['year']-1 in capital:
                avg=(capital[r['year']]+capital[r['year']-1])/2
                if avg<=0:raise ValueError('Nonpositive invested capital')
                rates.append(nopat[r['year']]/avg)
        if len(rates)!=3:raise ValueError('Three annual ROIC observations required')
        result.update(return_on_capital_median=statistics.median(rates),
            return_on_capital_kind='ROIC_NOPAT_AVERAGE_EQUITY_PLUS_INTEREST_DEBT_LESS_CASH',
            economic_roic_annual=rates)
        first,last=rows[0]['year'],rows[-1]['year']
        change=capital[last]-capital[first]
        result['incremental_return']=(nopat[last]-nopat[first])/change if change>0 else None
    return result
