"""Dated economic judgements, kept separate from portfolio outcomes.

An assessment can be reused only for explicitly reviewed cutoff years. Original
documents are immutable; overrides retain both the reported and adjusted profit.
"""
import gzip
import hashlib
import json
import math
import statistics
from b00s_variants import INPUT, DATES

DIMENSIONS = ('durability', 'capital_economics', 'earnings_reliability',
              'financial_resilience', 'capital_allocation', 'governance')

def load_reviews():
    path = INPUT/'economic_reviews.json'
    if not path.exists():
        return {}
    records = json.loads(path.read_text())
    # Incremental batches never rewrite the accepted initial assessments.
    for update in sorted(INPUT.glob('economic_reviews_[0-9][0-9][0-9][0-9].json')):
        records.extend(json.loads(update.read_text()))
    manifest = {(r['docid'], r['group']): r for r in
                json.loads((INPUT/'review_original_sources.json').read_text())
                if r['status']=='ARCHIVED'}
    checked = set()
    def validate(ref, cutoff):
        src = manifest[ref['docid'], ref['group']]
        if src['received'] > cutoff:
            raise ValueError(('Future documentary evidence', ref, cutoff))
        if not ref.get('pages') or any(p<1 or p>src['page_count'] for p in ref['pages']):
            raise ValueError(('Invalid original page reference', ref))
        key = src['original']
        if key not in checked:
            raw = gzip.decompress((INPUT/key).read_bytes())
            if hashlib.sha256(raw).hexdigest()!=src['original_sha256']:
                raise ValueError(('Altered original', key))
            checked.add(key)
        return ref | {k:src[k] for k in ['received','url','original','original_sha256']}
    result = {}
    for record in records:
        if record['valuation']['status'] not in ['COMPARABLE','COMPARABLE_BOUNDED','INDETERMINATE']:
            raise ValueError('Unknown documentary valuation status')
        if record['valuation']['status']=='COMPARABLE_BOUNDED':
            bounds=record['valuation'].get('profit_bounds',{})
            expected={str(y) for y in range(min(record['years'])-5,min(record['years']))}
            if set(bounds)!=expected or not all(b.get('reason') for b in bounds.values()):
                raise ValueError('Five justified profit bounds required')
        if set(record['dimensions']) != set(DIMENSIONS):
            raise ValueError('Six documentary judgements required')
        for year in record['years']:
            r = json.loads(json.dumps(record)); cutoff = DATES[year]
            if r['cutoff'] > cutoff:
                raise ValueError('Assessment cannot travel backwards in time')
            if year != min(r['years']) and str(year) not in r.get('continuity', {}):
                raise ValueError(('Missing incremental review', r['ticker'], year))
            r['valuation']['evidence'] = [validate(e,cutoff) for e in r['valuation']['evidence']]
            for extra in ['economic_metrics','capital_block','capital_interval','incremental_review']:
                if extra in r:
                    r[extra]['evidence']=[validate(e,cutoff) for e in r[extra]['evidence']]
            for statement in r.get('economic_metrics',{}).get('statement_sources',[]):
                for fact in statement.get('records',[]):
                    if fact['received']>cutoff or fact['period_end']>cutoff:
                        raise ValueError(('Future economic metric input',fact['docid']))
            for dim in r['dimensions'].values():
                if not dim.get('reason') or not dim.get('contrary_evidence'):
                    raise ValueError('Economic reason and contrary evidence are required')
                if dim['status'] not in ['SATISFACTORY','HIGH','INDETERMINATE','REJECTED_EVIDENCED']:
                    raise ValueError('Unknown quality status')
                dim['evidence'] = [validate(e,cutoff) for e in dim['evidence']]
                if dim['status'] in ['SATISFACTORY','HIGH','REJECTED_EVIDENCED'] and not dim['evidence']:
                    raise ValueError('No material judgement without original evidence')
                if dim['status']=='REJECTED_EVIDENCED' and not dim.get('material_evidence'):
                    raise ValueError('Material failure must be distinguished from uncertainty')
            key = (year,r['cnpj'])
            if key in result:
                raise ValueError(('Overlapping assessments',key))
            result[key] = r
    return result

def adjust_profits(profits, evidence, year, review):
    reported = list(profits)
    if review:
        for fy, adjustment in review['valuation'].get('profit_overrides',{}).items():
            fiscal = int(fy)
            if year-5 <= fiscal < year:
                profits[fiscal-(year-5)] = adjustment['adjusted_profit']
                evidence.append(dict(fiscal_year=fiscal,metric='documentary_adjusted_attributable_ni',
                    value=adjustment['adjusted_profit'],reported_value=reported[fiscal-(year-5)],
                    reason=adjustment['reason'],**review['valuation']['evidence'][adjustment['source_index']]))
    return reported

def profit_interval(profits, factors, year, review):
    """Monotonicity of the same five-year median, not a new estimator.

    Unknown endpoints are unbounded. They must never become a point estimate or
    a reinvestment approval. Documented intervals can also prove that an item
    cannot change the median, avoiding fictitious exact tax/attribution bridges.
    """
    if not review:
        return None
    v=review['valuation']
    bounds=v.get('profit_bounds', {})
    invariant=v.get('median_invariance_bounds', {})
    if not bounds and not invariant:
        return None
    lows=[];highs=[]
    for fy,n,factor in zip(range(year-5,year),profits,factors):
        b=bounds.get(str(fy))
        lo,hi=(b['lower'],b['upper']) if b else invariant.get(str(fy),(n,n))
        lo=-math.inf if lo is None else lo
        hi=math.inf if hi is None else hi
        if lo>hi or not factor>0:raise ValueError('Invalid profit bounds')
        lows.append(lo*factor);highs.append(hi*factor)
    lo,hi=statistics.median(lows),statistics.median(highs)
    if invariant and not bounds and not math.isclose(lo,hi,rel_tol=1e-12):
        raise ValueError(('Claimed invariant median changed',review['ticker'],lo,hi))
    return dict(lower=lo if math.isfinite(lo) else None,
                upper=hi if math.isfinite(hi) else None)
