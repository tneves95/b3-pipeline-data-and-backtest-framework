"""Motor multiativo v2: retorno teórico bruto, preços BRL não ajustados.

Continuação do motor herdado; não altera seleções nem pesos Graham/BESST.
Direitos em dinheiro pertencem à posição no FECHAMENTO da data-com (depois
 de eventual rebalanceamento). Reinvestimento na data-ex ao fechamento.
Cisões mantêm a controladora e acrescentam os ativos recebidos; incorporações
consomem a origem; direitos nunca viram ações grátis. Quantidades fracionárias
são conservadas no índice teórico. Nenhum aporte externo é criado.

Os testes de software NÃO certificam documentos ou completude de séries.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Mapping, Sequence
from bisect import bisect_right, bisect_left
from math import isfinite
import json, os

EPS = 1e-12

class AnalysisError(ValueError):
    category = 'FALHA_TECNICA'
class MissingData(AnalysisError):
    category = 'DADO_AUSENTE'
class IncompleteCoverage(MissingData): pass
class UnsupportedOperation(AnalysisError):
    category = 'FUNCIONALIDADE_NAO_IMPLEMENTADA'
class InvalidData(AnalysisError):
    category = 'DADO_INCONSISTENTE'
class InsufficientCash(InvalidData): pass

KINDS = {'CASH','SPLIT','BONUS','CONVERSION','MERGER','SPINOFF',
         'RIGHTS_ISSUE','RIGHTS_SELL','RIGHTS_EXERCISE','RIGHTS_EXPIRE',
         'CASH_OUT','CASH_IN_LIEU'}

@dataclass(frozen=True)
class Event:
    event_id: str
    date: str
    kind: str
    asset: str
    source: str
    record_date: str = ''
    amount: float = 0.0
    factor: float = 1.0
    legs: tuple = ()      # ((ticker, new units per old unit), ...)
    reinvest: str = ''    # CASH: blank=same asset; KEEP_CASH=do not reinvest
    price: float | None = None # only documented cash-out/right sale
    quantity: float | None = None  # rights: None=all; cash-in-lieu=explicit fraction
    order: int = 50
    note: str = ''
    def __post_init__(self):
        if self.kind not in KINDS:
            raise UnsupportedOperation(f'{self.event_id}: tipo {self.kind}')
        if not self.event_id or not self.source or not self.asset:
            raise InvalidData('Evento sem identificação, ativo ou fonte')
        if not isfinite(self.amount) or self.amount < 0 or not isfinite(self.factor) or self.factor <= 0:
            raise InvalidData(f'{self.event_id}: montante/fator inválido')
        if self.record_date and self.record_date >= self.date:
            raise InvalidData(f'{self.event_id}: data-com deve anteceder data-ex')
        if self.price is not None and (not isfinite(self.price) or self.price < 0):
            raise InvalidData(f'{self.event_id}: preço inválido')
        if self.quantity is not None and (not isfinite(self.quantity) or self.quantity < 0):
            raise InvalidData(f'{self.event_id}: quantidade inválida')
        for ticker, ratio in self.legs:
            if not ticker or not isfinite(ratio) or ratio <= 0:
                raise InvalidData(f'{self.event_id}: perna inválida')

@dataclass
class State:
    start: str
    last_date: str
    initial_value: float
    holdings: dict[str,float]
    cash: float = 0.
    snapshots: dict = field(default_factory=dict)
    applied: list = field(default_factory=list)
    ledger: list = field(default_factory=list)
    nav: list = field(default_factory=list)
    exposure_open: dict = field(default_factory=dict)
    exposure_closed: list = field(default_factory=list)
    policy: str = 'GROSS_EX_CLOSE_FRACTIONAL_NO_EXTERNAL_CASH'

@dataclass(frozen=True)
class Coverage:
    asset: str
    start: str
    end: str
    cash_status: str
    structure_status: str
    evidence: str
    scope: str = 'THEORETICAL_GROSS'

class PriceBook:
    def __init__(self, prices: Mapping[str,Mapping[str,float]], calendar: Sequence[str]):
        self.prices={a:dict(v) for a,v in prices.items()}
        self.calendar=sorted(set(calendar))
        if not self.calendar: raise MissingData('Calendário vazio')
        for a, ps in self.prices.items():
            if any(not isfinite(float(v)) or float(v)<=0 for v in ps.values()):
                raise InvalidData(f'{a}: cotação não positiva ou não finita')
    def exact(self, asset:str, date:str)->float:
        try: return float(self.prices[asset][date])
        except KeyError: raise MissingData(f'Cotação exata ausente: {asset}, {date}; sem forward-fill') from None
    def next_session(self, date:str)->str:
        i=bisect_right(self.calendar,date)
        if i==len(self.calendar):raise MissingData(f'Calendário insuficiente após {date}')
        return self.calendar[i]
    def previous_session(self,date:str)->str:
        i=bisect_left(self.calendar,date)-1
        if i<0:raise MissingData(f'Calendário insuficiente antes de {date}')
        return self.calendar[i]
    def first_quote_on_or_after(self,asset:str,date:str)->str:
        # Use somente para execução documentada: não serve para sinais de seleção.
        dates=sorted(d for d in self.prices.get(asset,{}) if d>=date)
        if not dates:raise MissingData(f'Ativo recebido sem cotação: {asset}, após {date}')
        return dates[0]

class Engine:
    def __init__(self, book:PriceBook, events:Sequence[Event], coverage:Sequence[Coverage]=()):
        self.book=book
        self.events=sorted(events,key=lambda e:(e.date,e.order,e.event_id))
        ids=[e.event_id for e in self.events]
        if len(set(ids))!=len(ids):raise InvalidData('Identificador de evento duplicado')
        self.coverage=list(coverage)
        for e in self.events:
            if e.date not in self.book.calendar:
                raise InvalidData(f'{e.event_id}: data efetiva não pertence ao calendário de negociação')
    def initialize(self,start:str,weights:Mapping[str,float],capital:float=10000.)->State:
        self._weights(weights)
        if not isfinite(capital) or capital<=0:raise InvalidData('Capital inicial inválido')
        hs={a:capital*w/self.book.exact(a,start) for a,w in sorted(weights.items()) if w>0 and a!='CASH'}
        st=State(start,start,capital,hs,cash=capital*weights.get('CASH',0.))
        st.snapshots[start]=dict(hs)
        st.exposure_open={a:start for a in hs}
        st.ledger.append({'date':start,'event_id':'INITIAL','kind':'BUY_INITIAL',
                          'before':{},'after':dict(hs),'cash_before':capital,'cash_after':st.cash,
                          'source':'Pesos e datas herdados/entrada explícita','details':{'weights':dict(weights)}})
        st.nav.append({'date':start,'nav':capital,'cash':st.cash,'missing_assets':''})
        return st
    @staticmethod
    def _weights(weights):
        if not weights or any(not isfinite(w) or w<0 for w in weights.values()) or abs(sum(weights.values())-1)>1e-10:
            raise InvalidData('Pesos devem ser finitos, não negativos, e somar 1')
    def _entitlement(self,st:State,e:Event)->float:
        rd=e.record_date or self.book.previous_session(e.date)
        # Data-com pode ser dia não útil; posição de fechamento anterior é a mesma.
        rd=max((d for d in st.snapshots if d<=rd),default='')
        return st.snapshots.get(rd,{}).get(e.asset,0.)
    def _put(self,st:State,a:str,q:float,date:str):
        old=st.holdings.get(a,0.)
        new=old+q
        if new < -EPS:raise InvalidData(f'Posição negativa: {a} em {date}')
        if abs(new)<EPS:
            st.holdings.pop(a,None)
            if a in st.exposure_open:
                st.exposure_closed.append({'asset':a,'start':st.exposure_open.pop(a),'end':date})
        else:
            st.holdings[a]=new
            if a not in st.exposure_open:st.exposure_open[a]=date
    def _apply(self,st:State,e:Event):
        if e.event_id in st.applied:return # reentrega idempotente
        before=dict(st.holdings);cb=st.cash; q=st.holdings.get(e.asset,0.);details={}
        if e.kind in {'CASH','SPINOFF','RIGHTS_ISSUE'}:
            q=self._entitlement(st,e)
        if q<=EPS:
            st.applied.append(e.event_id);return
        if e.kind=='CASH':
            amount=q*e.amount;st.cash+=amount
            target=e.reinvest or e.asset
            details={'entitled_quantity':q,'amount_per_share':e.amount,'cash_credit':amount,'reinvest':target}
            if target!='KEEP_CASH':
                p=self.book.exact(target,e.date)
                if st.holdings.get(target,0)<=EPS and target==e.asset:
                    raise UnsupportedOperation(f'{e.event_id}: origem saiu; indique destino do reinvestimento')
                dq=amount/p; self._put(st,target,dq,e.date);st.cash-=amount
                details.update(reinvest_price=p,shares_bought=dq)
        elif e.kind in {'SPLIT','BONUS'}:
            self._put(st,e.asset,q*(e.factor-1),e.date)
            details={'factor':e.factor}
        elif e.kind in {'CONVERSION','MERGER'}:
            if not e.legs:raise InvalidData(f'{e.event_id}: falta relação de troca')
            self._put(st,e.asset,-q,e.date)
            for a,ratio in e.legs:self._put(st,a,q*ratio,e.date)
            st.cash+=q*e.amount
            details={'consumed':q,'legs':list(e.legs),'cash_credit':q*e.amount}
        elif e.kind in {'SPINOFF','RIGHTS_ISSUE'}:
            if not e.legs:raise InvalidData(f'{e.event_id}: ativo recebido ausente')
            for a,ratio in e.legs:self._put(st,a,q*ratio,e.date)
            details={'entitled_quantity':q,'legs':list(e.legs),'parent_retained':True}
        elif e.kind in {'CASH_OUT','CASH_IN_LIEU','RIGHTS_SELL'}:
            n=q if e.quantity is None else e.quantity
            if n>q+EPS:raise InvalidData(f'{e.event_id}: venda maior que a posição')
            p=e.price if e.price is not None else self.book.exact(e.asset,e.date)
            if e.kind=='CASH_OUT' and e.price is None:
                raise InvalidData(f'{e.event_id}: OPA/resgate requer valor documental explícito')
            self._put(st,e.asset,-n,e.date);st.cash+=n*p
            details={'sold_quantity':n,'execution_price':p,'cash_credit':n*p}
            if e.reinvest and e.reinvest!='KEEP_CASH':
                rp=self.book.exact(e.reinvest,e.date)
                self._put(st,e.reinvest,n*p/rp,e.date);st.cash-=n*p
                details.update(reinvest=e.reinvest,reinvest_price=rp)
        elif e.kind=='RIGHTS_EXERCISE':
            n=q if e.quantity is None else e.quantity
            if n>q+EPS:raise InvalidData(f'{e.event_id}: exercício maior que direitos detidos')
            cost=n*e.amount
            if cost>st.cash+EPS:raise InsufficientCash(f'{e.event_id}: subscrição requer {cost}; caixa {st.cash}; sem aporte implícito')
            if not e.legs:raise InvalidData(f'{e.event_id}: subscrição sem ativo recebido')
            self._put(st,e.asset,-n,e.date);st.cash-=cost
            for a,ratio in e.legs:self._put(st,a,n*ratio,e.date)
            details={'rights_exercised':n,'cash_used':cost,'legs':list(e.legs)}
        elif e.kind=='RIGHTS_EXPIRE':
            self._put(st,e.asset,-q,e.date)
            details={'expired_quantity':q,'documented_expiry':True}
        else:raise UnsupportedOperation(e.kind)
        if st.cash<-EPS:raise InvalidData('Caixa negativo não autorizado')
        if abs(st.cash)<EPS:st.cash=0.
        st.applied.append(e.event_id)
        st.ledger.append({'date':e.date,'event_id':e.event_id,'kind':e.kind,'asset':e.asset,
                          'before':before,'after':dict(st.holdings),'cash_before':cb,'cash_after':st.cash,
                          'source':e.source,'note':e.note,'details':details})
    def value(self,st:State,date:str,strict:bool=True):
        total=st.cash;missing=[]
        for a,q in sorted(st.holdings.items()):
            try:total+=q*self.book.exact(a,date)
            except MissingData:missing.append(a)
        if missing and strict:raise MissingData(f'Patrimônio incompleto em {date}: {", ".join(missing)}')
        return {'date':date,'nav':None if missing else total,'cash':st.cash,'missing_assets':';'.join(missing)}
    def rebalance(self,st:State,date:str,weights:Mapping[str,float]):
        self._weights(weights);key='REBALANCE:'+date
        if key in st.applied:return
        v=self.value(st,date)['nav'];before=dict(st.holdings);cb=st.cash
        target={a:v*w/self.book.exact(a,date) for a,w in sorted(weights.items()) if a!='CASH' and w>0}
        for a in sorted(set(st.holdings)|set(target)):
            self._put(st,a,target.get(a,0)-st.holdings.get(a,0),date)
        st.cash=v*weights.get('CASH',0.)
        st.applied.append(key)
        st.ledger.append({'date':date,'event_id':key,'kind':'REBALANCE','before':before,'after':dict(st.holdings),
                          'cash_before':cb,'cash_after':st.cash,'source':'Seleção e pesos anuais fornecidos',
                          'details':{'nav_before':v,'weights':dict(weights)}})
    def advance(self,st:State,end:str,rebalances:Mapping[str,Mapping[str,float]]|None=None)->State:
        if end<st.last_date or end not in self.book.calendar:raise InvalidData('Fim inválido')
        schedule=rebalances or {}
        event_days={}
        for e in self.events:
            if st.last_date<e.date<=end:event_days.setdefault(e.date,[]).append(e)
        for day in self.book.calendar:
            if not (st.last_date<day<=end):continue
            # Before close: corporate entitlements from prior snapshots; each CASH
            # references the same record-date snapshot, not reinvested quantities.
            # Dia transacional: uma falha não deixa provento creditado pela
            # metade, nem duplica eventos ao retomar após corrigir a entrada.
            backup=(dict(st.holdings),st.cash,dict(st.exposure_open),
                    list(st.exposure_closed),len(st.applied),len(st.ledger),len(st.nav))
            try:
                for e in event_days.get(day,[]):self._apply(st,e)
                if day in schedule:self.rebalance(st,day,schedule[day])
                row=self.value(st,day,strict=False)
            except Exception:
                st.holdings,st.cash,st.exposure_open,st.exposure_closed,na,nl,nn=backup
                del st.applied[na:];del st.ledger[nl:];del st.nav[nn:]
                raise
            st.snapshots[day]=dict(st.holdings)
            st.nav.append(row)
            st.last_date=day
        return st
    def exposure(self,st:State):
        return st.exposure_closed+[{'asset':a,'start':d,'end':st.last_date} for a,d in st.exposure_open.items()]
    def coverage_gaps(self,st:State):
        gaps=[]
        for x in self.exposure(st):
            usable=sorted((c for c in self.coverage if c.asset==x['asset'] and c.cash_status=='RECONCILED'
                         and c.structure_status=='RECONCILED' and c.evidence),key=lambda c:c.start)
            cursor=x['start'];covered=False
            for c in usable:
                if c.start<=cursor and c.end>=cursor:
                    cursor=max(cursor,c.end)
                    if cursor>=x['end']:covered=True;break
            if not covered:gaps.append(x)
        return gaps
    def result(self,st:State,require_complete:bool=True):
        final=self.value(st,st.last_date)
        gaps=self.coverage_gaps(st)
        if gaps and require_complete:raise IncompleteCoverage('Cobertura não conciliada: '+json.dumps(gaps,ensure_ascii=False))
        return {'start':st.start,'end':st.last_date,'initial_value':st.initial_value,
                'final_value':final['nav'],'return':final['nav']/st.initial_value-1,
                'cash':st.cash,'holdings':dict(st.holdings),'coverage_gaps':gaps,
                'status':'RECONCILED_THEORETICAL' if not gaps else 'INDICATIVE_INCOMPLETE_COVERAGE',
                'daily_missing':sum(x['nav'] is None for x in st.nav)}

def save_state(st:State,path:str|Path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(asdict(st),ensure_ascii=False,sort_keys=True,indent=2),encoding='utf8')
    os.replace(tmp,p)
def load_state(path:str|Path)->State:
    return State(**json.loads(Path(path).read_text(encoding='utf8')))
def load_events(path:str|Path):
    rows=json.loads(Path(path).read_text(encoding='utf8'))
    return [Event(**r) for r in rows]
