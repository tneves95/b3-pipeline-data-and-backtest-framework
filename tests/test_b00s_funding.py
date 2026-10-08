import math
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from b00s_funding import reference_entries,renew_reference_entries

def meta(**sectors):return {t:dict(cnpj=t,sector=s) for t,s in sectors.items()}

def test_single_new_does_not_request_all_nav():
    h={'old':.7,'nd':.3};s={'old':'PASS','nd':'INDETERMINATE','new':'PASS'}
    m=meta(old='Bancos',nd='Energia',new='Bancos')
    e=reference_entries(h,s,['new'],m)
    assert e=={'new':.1}
    after,_=renew_reference_entries(h,s,e)
    assert after==pytest.approx({'old':.63,'nd':.27,'new':.1})

def test_new_sector_gets_only_its_reference_share():
    h={'old':1};s={'new':'PASS'};m=meta(old='Bancos',new='Telecom')
    e=reference_entries(h,s,['new'],m)
    assert e=={'new':.2}
    assert renew_reference_entries(h,s,e)[0]==pytest.approx({'old':.8,'new':.2})

def test_several_qualifications_count_incumbents_once():
    h={'old':.6,'other':.4};s={t:'PASS' for t in ['old','other','new1','new2','new3']}
    m=meta(old='Bancos',other='Energia',new1='Bancos',new2='Bancos',new3='Energia')
    e=reference_entries(h,s,list(s),m)
    assert e==pytest.approx({'new1':.2/3,'new2':.2/3,'new3':.1})
    after,_=renew_reference_entries(h,s,e)
    assert after['old']/after['other']==pytest.approx(1.5)
    assert math.fsum(after.values())==pytest.approx(1)

def test_right_and_successor_keep_one_economic_slot_and_all_nav():
    h={'old':.4,'right':.1,'successor':.2,'other':.3};s={'new':'PASS'}
    m=meta(old='Bancos',right='Bancos',successor='Bancos',other='Energia',new='Bancos')
    for t in ['right','successor']:m[t]['cnpj']='old'
    e=reference_entries(h,s,['new','successor'],m)
    assert e=={'new':.1}
    after,_=renew_reference_entries(h,s,e)
    assert after==pytest.approx({'old':.36,'right':.09,'successor':.18,'other':.27,'new':.1})

@pytest.mark.parametrize('released',[.05,.6])
def test_fail_proceeds_first_surplus_is_not_capped(released):
    h={'exit':released,'keep':1-released};s={'exit':'FAIL','keep':'INDETERMINATE','new':'PASS'}
    after,_=renew_reference_entries(h,s,{'new':.2})
    assert after['new']==pytest.approx(max(released,.2))
    assert after['keep']==pytest.approx(1-max(released,.2))
    assert 'exit' not in after

def test_no_entry_means_no_equalization_and_fail_proceeds_redistribute():
    h={'a':.6,'b':.3,'c':.1}
    assert renew_reference_entries(h,{}, {})[0]==h
    a,_=renew_reference_entries(h,{'c':'FAIL'}, {})
    assert a==pytest.approx({'a':2/3,'b':1/3})
    with pytest.raises(ValueError,match='All holdings FAIL'):renew_reference_entries({'a':1},{'a':'FAIL'}, {})

def test_all_fail_with_destination_and_no_cash_created():
    a,_=renew_reference_entries({'old':1},{'old':'FAIL','new':'PASS'}, {'new':.2})
    assert a=={'new':1}
    with pytest.raises(ValueError,match='exhaust'):renew_reference_entries({'old':1},{'new':'PASS'}, {'new':1})

def test_duplicate_entry_class_and_nonpass_cannot_enter():
    m=meta(old='Energia',new='Bancos',newpn='Bancos');m['newpn']['cnpj']='new'
    with pytest.raises(ValueError,match='Two classes'):reference_entries({'old':1},{'new':'PASS','newpn':'PASS'},['new','newpn'],m)
    with pytest.raises(ValueError,match='base PASS'):reference_entries({'old':1},{},['new'],m)

def test_fail_cannot_reenter_via_another_ticker_of_same_lineage():
    m=meta(old='Bancos',new='Bancos');m['new']['cnpj']='old'
    with pytest.raises(ValueError,match='Conflicting FAIL and PASS'):
        reference_entries({'old':1},{'old':'FAIL','new':'PASS'},['new'],m)
