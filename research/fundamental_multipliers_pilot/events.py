"""Reconcile reused evidence; independently extract complete reviewed issuer windows."""
from __future__ import annotations
from bisect import bisect_right
from collections import defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pandas as pd
from .audit import sha256


def verified_gzip(path, manifest_path, key='sha256'):
    raw=gzip.decompress(path.read_bytes())
    meta=json.loads(manifest_path.read_text())
    if hashlib.sha256(raw).hexdigest()!=meta[key]: raise ValueError('Original source hash mismatch')
    return raw


def extract_reviewed_events(root, output, calendar):
    originals=root/'research/returns_2014_2026_selection/originals'
    # Independently parse the issuer's complete historical PN cash and bonus tables.
    raw=verified_gzip(originals/'bradesco_remuneracao.html.gz',originals/'bradesco_remuneracao.json')
    tables=BeautifulSoup(raw,'html.parser').find_all('table');events=[]
    def add(ticker,day,kind,source,**kw):
        events.append(dict(id=f'REVIEWED_{ticker}_{day}_{kind}_{len(events)}',ticker=ticker,
                           ex_date=day,kind=kind,source=source,**kw))
    def next_session(record):
        i=bisect_right(calendar,record)
        if i==len(calendar): return None
        return calendar[i]
    bradesco_source=sha256(originals/'bradesco_remuneracao.html.gz')
    for table in tables:
        for tr in table.find_all('tr'):
            row=[cell.get_text(' ',strip=True) for cell in tr.find_all(['th','td'])]
            if len(row)>=6 and row[5].startswith('R$'):
                record=pd.to_datetime(row[2],dayfirst=True).strftime('%Y-%m-%d')
                day=next_session(record)
                if day and '2017-01-01'<=day<='2026-06-30':
                    amount=float(row[5].replace('R$','').replace('.','').replace(',','.'))
                    add('BBDC4',day,'DISTRIBUTION',bradesco_source,amount=amount,record_date=record,
                        payment_date=row[3],original_type=row[1],scope='FULL_PN_CASH_TABLE')
            elif len(row)>=4 and re.fullmatch(r'\d{2}/\d{2}/\d{4}',row[0]) and row[2].endswith('%'):
                record=pd.to_datetime(row[1],dayfirst=True).strftime('%Y-%m-%d')
                factor=1+float(row[2].rstrip('%').replace(',','.'))/100
                day=next_session(record)
                if day and '2017-01-01'<=day<='2026-06-30':
                    add('BBDC4',day,'SHARES',bradesco_source,factor=factor,record_date=record,scope='FULL_BONUS_TABLE')
    # The PDF explicitly provides ex dates, unadjusted gross amounts and holder factors.
    raw=verified_gzip(originals/'cemig_dividends.pdf.gz',originals/'cemig_dividends.pdf.json')
    text='\n'.join(p.extract_text(extraction_mode='layout') for p in PdfReader(io.BytesIO(raw)).pages)
    pattern=r'(?m)^\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(?:RCA|RD|AGO/E|AGO|AGE)\s+'
    matches=list(re.finditer(pattern,text))
    cemig_source=sha256(originals/'cemig_dividends.pdf.gz')
    for i,m in enumerate(matches):
        # Old PDF rows mix dd/mm and mm/dd before 2014; certified rows are dd/mm.
        if int(m[1][-4:])<2014: continue
        day=pd.to_datetime(m[1],format='%d/%m/%Y').strftime('%Y-%m-%d')
        if not '2014-06-30'<=day<='2022-12-28': continue
        desc=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
        if desc.startswith(('Juros','Dividendos')):
            amount=re.search(r'R\$\s*(\d+(?:[.,]\d+)*)',desc)
            if amount is None: raise ValueError('Unparsed CEMIG cash row')
            value=float(amount[1].replace('.','').replace(',','.'))
            add('CMIG4',day,'DISTRIBUTION',cemig_source,amount=value,scope='FULL_EX_DATED_PN_CASH_TABLE')
        elif desc.startswith('Bonificação'):
            percentage=re.search(r'([\d.,]+)%',desc)
            if percentage is None: raise ValueError('Unparsed CEMIG bonus row')
            add('CMIG4',day,'SHARES',cemig_source,factor=1+float(percentage[1].replace(',','.'))/100)
        else: raise ValueError('Unreviewed CEMIG economic event in certified scope')
    # Reuse the previously audited detached-right entitlement and its first-trade settlement.
    prior=json.loads(gzip.decompress((root/'research/returns_2014_2026_selection/cache/bh_owned_events.json.gz').read_bytes()))
    for e in prior:
        if e['ticker']=='CMIG4' and e['kind']=='RIGHT' or e['ticker']=='CMIG2' and e['kind']=='RIGHT_REINVEST':
            events.append(dict(e,source_evidence_sha256=sha256(root/'research/returns_2014_2026_selection/bh_evidence.json')))
    # IRB cash absence and share mechanics are checked in current primary catalogs.
    sources=output/'sources';source_manifest=json.loads((sources/'manifest.json').read_text())
    raw_sources={}
    for r in source_manifest:
        raw=gzip.decompress((sources/r['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=r['sha256']: raise ValueError('New source hash mismatch')
        raw_sources[r['file']]=raw
    irb_text=BeautifulSoup(raw_sources['irb_capital.html.gz'],'html.parser').get_text(' ',strip=True)
    if not ('25/01/2023' in irb_text or '25 de janeiro de 2023' in irb_text): raise ValueError('IRB reverse-split ex date unverified')
    if '30 (trinta)' not in irb_text: raise ValueError('IRB reverse-split ratio unverified')
    irb_cash=BeautifulSoup(raw_sources['irb_cash.html.gz'],'html.parser')
    cash_rows=[]
    for tr in irb_cash.find_all('tr'):
        r=[c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])]
        if len(r)==6 and r[0] in ['RCA','AGO']: cash_rows.append(r)
    if len(cash_rows)<10 or not any('2020' in r[1] for r in cash_rows):
        raise ValueError('IRB primary cash catalog incomplete or unparsed')
    # Restrict certification to formations after the old entitlement's ex date and endpoints
    # before the new 2026 payouts. A 2021 payment of a 2020 entitlement is not a new dividend.
    if any('2021' in r[1] or '2022' in r[1] or '2023' in r[1] or '2024' in r[1] or '2025' in r[1] for r in cash_rows):
        raise ValueError('IRB cash absence window no longer matches reviewed source')
    offer='\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(raw_sources['irb_offer_2022.pdf.gz'])).pages)
    if 'exclusão do direito de preferência' not in offer: raise ValueError('IRB 2022 issuance mechanism unverified')
    add('IRBR3','2022-09-06','NO_ENTITLEMENT',sha256(sources/'irb_offer_2022.pdf.gz'),
        qualification='Public issuance; priority purchase requires new capital, no detachable preemptive right credited to unchanged holdings')
    add('IRBR3','2023-01-25','SHARES',sha256(sources/'irb_capital.html.gz'),factor=1/30)
    scopes=[
        dict(id='BBDC_PN_RI_FULL_TABLE_2017_2026',ticker='BBDC4',cnpj='60746948000112',isin='BRBBDCACNPR8',start='2017-01-01',end='2026-06-30',certified=True,
             proof='Independent extraction of PN cash and bonus tables; full local originals and verified FRE cross-check; tradable-right episodes checked',
             blocker='BBDC_CASH_BEFORE_2017_NOT_IN_REVIEWED_RI_TABLE'),
        dict(id='CMIG_PN_RI_EX_DATED_2014_2022',ticker='CMIG4',cnpj='17155730000164',isin='BRCMIGACNPR3',start='2014-06-30',end='2022-12-28',certified=True,
             proof='Full ex-dated historical PN cash catalog, simultaneous bonuses, audited 2017 right entitlement and observed settlement',
             blocker='CMIG_CASH_AFTER_2022_NOT_IN_REVIEWED_RI_TABLE'),
        dict(id='IRBR_POST_2020_ENTITLEMENTS_PRE_2026_PAYOUTS',ticker='IRBR3',cnpj='33376989000191',isin='BRIRBRACNOR4',start='2021-06-30',end='2025-12-31',certified=True,
             proof='Primary cash catalog confirms no new entitlements in window; documented 2022 public issuance and exact 1/30 reverse split in 2023',
             blocker='IRBR_CASH_TRANCHES_OUTSIDE_REVIEWED_WINDOW_DIFFER_FROM_B3'),
        dict(id='AMER_PRICE_RECOVERY_EVENT_REVIEW_PENDING',ticker='AMER3',start='2021-07-19',end='2026-06-30',certified=False,
             blocker='AMER_2022_2024_SUBSCRIPTION_RIGHTS_AND_SUCCESSION_NOT_RECONCILED'),
        dict(id='LIGT_CAPITAL_NET_NEUTRAL_CORROBORATED',ticker='LIGT3',start='2014-06-30',end='2026-06-30',certified=False,
             resolved_skipped_dates=['2021-06-25'],blocker='LIGT_FULL_CASH_CATALOG_EX_DATE_CONFLICTS_AND_2026_RIGHT')]
    # Preserve full reused event reconciliation separately; it is not a blanket certificate.
    reused=json.loads(gzip.decompress((root/'research/returns_2014_2026_selection/cache/continuation_events.json.gz').read_bytes()))
    covered={s['ticker'] for s in scopes if s['certified']}
    reused=[e for e in reused if e['ticker'] not in covered and e['ticker']!='CMIG2']
    all_events=reused+events
    fields=sorted(set().union(*(e.keys() for e in all_events)))
    pd.DataFrame(all_events,columns=fields).to_csv(output/'reconciled_economic_events.csv',index=False)
    (output/'certification_scopes.json').write_text(json.dumps(scopes,ensure_ascii=False,indent=2)+'\n')
    return all_events,scopes


def verify_reused_fre(root, source, output):
    """Match existing compact evidence with original local archive rows, without recollection."""
    wanted=[]
    for name in ['owned_capital_events_fre.json','continuation_irb_capital_fre.json','continuation_capital_events_fre.json']:
        wanted.extend(json.loads((root/'research/returns_2014_2026_selection'/name).read_text()))
    selected=[r for r in wanted if re.sub(r'\D','',r['CNPJ_Companhia']) in
              ['60746948000112','17155730000164','33376989000191','03378521000175']]
    groups=defaultdict(list)
    for r in selected: groups[r['source_member']].append(r)
    results=[]
    for member, rows in sorted(groups.items()):
        year=int(member[-8:-4]);archive=source/'data/cvm'/f'fre_cia_aberta_{year}.zip'
        with zipfile.ZipFile(archive) as z:
            values={json.dumps(r,sort_keys=True) for r in csv.DictReader(io.TextIOWrapper(z.open(member),encoding='latin1'),delimiter=';')}
        for r in rows:
            original={k:v for k,v in r.items() if k not in ['source_member','metadata','archive','kind']}
            if json.dumps(original,sort_keys=True) not in values: raise ValueError('Reused FRE row not in original archive')
            results.append(dict(cnpj=re.sub(r'\D','',r['CNPJ_Companhia']),source_member=member,
                docid=r['ID_Documento'],row_sha256=hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
                status='MATCHED_ORIGINAL_LOCAL_FRE'))
    pd.DataFrame(results).to_csv(output/'reused_fre_verification.csv',index=False)
    return results
