import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from research.fundamental_multipliers_pilot.round3.scale import Prices,economic_key,replay
from research.fundamental_multipliers_pilot.round3.features import statement,ibov_series
from research.fundamental_multipliers_pilot.round3.validation import closed_form
from research.fundamental_multipliers_pilot.round3.statistics import filter_mask,missing_binary_bounds,cluster_difference,rank_effect
from research.fundamental_multipliers_pilot.round3.publication import validate_schema,suppress_small_cells
from research.fundamental_multipliers_pilot.round3.assessment import assess


def book(prices):
    b=Prices.__new__(Prices);b.calendar=['2020-01-02','2020-01-03','2020-01-06','2020-01-07']
    b.series={i:dict(dates=np.array(b.calendar),prices=np.array(p,dtype=float),
        tickers=np.array([i]*4),adjusted=np.array(p,dtype=float)) for i,p in prices.items()}
    return b


class ReturnMaterialityRegression(unittest.TestCase):
    def test_record_date_is_not_ex_date(self):
        b=book({'X':[10,9,9,9]});self.assertEqual(b.next_session('2020-01-03'),'2020-01-06')
        self.assertEqual(b.session('2020-01-05'),'2020-01-03')

    def test_actual_crash_is_retained_without_price_only_upscaling(self):
        b=book({'X':[10,10,1,1]});r=replay(b,'X','2020-01-02','2020-01-07',[])
        self.assertAlmostEqual(r['wealth_multiple'],.1)

    def test_same_day_bonus_and_two_distinct_cash_tranches(self):
        b=book({'X':[10,5,5,5]})
        e=[dict(id='1',ticker='X',ex_date='2020-01-03',kind='SHARES',factor=2),
           dict(id='2',ticker='X',ex_date='2020-01-03',kind='DISTRIBUTION',amount=1),
           dict(id='3',ticker='X',ex_date='2020-01-03',kind='DISTRIBUTION',amount=.5)]
        r=replay(b,'X','2020-01-02','2020-01-07',e)
        self.assertAlmostEqual(r['wealth_multiple'],1.15)
        self.assertAlmostEqual(closed_form(b,'X','2020-01-02','2020-01-07',e),1.15)

    def test_rounded_group_factors_deduplicate_but_opposites_do_not(self):
        a=dict(ex_date='2020-01-03',kind='SHARES',factor=1/30)
        b=dict(a,factor=.03333333334)
        self.assertEqual(economic_key('X',a),economic_key('X',b))
        self.assertNotEqual(economic_key('X',a),economic_key('X',dict(a,factor=30)))
        self.assertNotEqual(economic_key('X',dict(a,kind='DISTRIBUTION',amount=.1)),
                            economic_key('X',dict(a,kind='DISTRIBUTION',amount=.2)))

    def test_conversion_preserves_child_and_nominal_cash(self):
        b=book({'X':[10,10,10,10],'Y':[20,20,20,40]})
        e=[dict(id='c',ticker='X',ex_date='2020-01-03',kind='CONVERSION',legs=[['Y',.5]],amount=2)]
        r=replay(b,'X','2020-01-02','2020-01-07',e)
        self.assertAlmostEqual(r['wealth_multiple'],2.2)
        intervals=r['holding_intervals'];self.assertEqual(intervals[0]['end'],'2020-01-03')
        self.assertEqual(intervals[1]['start'],'2020-01-03')

    def test_redeemed_security_does_not_need_terminal_quote(self):
        b=book({'X':[10,10,10,10]});b.series['X']['dates']=np.array(['2020-01-02'])
        b.series['X']['prices']=np.array([10.])
        e=[dict(id='r',ticker='X',ex_date='2020-01-03',kind='REDEMPTION',amount=8)]
        r=replay(b,'X','2020-01-02','2020-01-07',e);self.assertAlmostEqual(r['wealth_multiple'],.8)

    def test_missing_quote_is_not_zero_or_unlimited_last_price(self):
        b=book({'X':[10,10,10,10]});b.series['X']['dates']=np.array(['2020-01-02'])
        with self.assertRaisesRegex(ValueError,'SUSPENDED'):
            b.trade('X','2020-01-07',max_age=1)
        with self.assertRaisesRegex(ValueError,'NO_TRADE_BEFORE_TARGET'):
            b.trade('X','2020-01-01')

    def test_documented_61_to_1_changes_units_not_wealth(self):
        b=book({'X':[1,61,61,61]})
        e=[dict(id='s',ticker='X',ex_date='2020-01-03',kind='SHARES',factor=1/61)]
        self.assertAlmostEqual(replay(b,'X','2020-01-02','2020-01-07',e)['wealth_multiple'],1)


class HistoricalSelectionRegression(unittest.TestCase):
    def test_known_false_and_missing_preserves_loss_companies(self):
        f=pd.DataFrame(dict(income_positive=[0,1,1,np.nan],ocf_to_positive_income=[np.nan,1.2,np.nan,.5]))
        k,s=filter_mask(f,['positive_income','cash_conversion'])
        self.assertEqual(k.tolist(),[True,True,False,True]);self.assertEqual(s.tolist(),[False,True,False,False])

    def test_later_revision_and_same_day_receipt_are_unavailable(self):
        meta=pd.DataFrame(dict(period_end=['2019-12-31']*3,received=['2020-03-01','2020-06-30','2021-01-01'],version=[1,2,3],docid=[1,2,3]))
        values={'X_DFP_2019-12-31_1':dict(net_income=10,filing_date='2020-03-01'),
                'X_DFP_2019-12-31_2':dict(net_income=999,filing_date='2020-06-30')}
        r,_=statement(meta,values,'X','2019-12-31','2020-06-30');self.assertEqual(r['net_income'],10)
        r,cause=statement(meta,values,'X','2019-12-31','2020-07-01');self.assertEqual(r['net_income'],999)
        r,cause=statement(meta,{},'X','2019-12-31','2020-07-01');self.assertFalse(r);self.assertIn('VERSION_VALUES_MISSING',cause)

    def test_metadata_receipt_disagreement_blocks_history(self):
        meta=pd.DataFrame(dict(period_end=['2019-12-31'],received=['2020-03-01'],version=[1],docid=[1]))
        r,c=statement(meta,{'X_DFP_2019-12-31_1':dict(filing_date='2020-04-30')},'X','2019-12-31','2020-06-30')
        self.assertEqual(c,'RECEIPT_DISAGREEMENT')

    def test_ibov_uses_actual_endpoint_not_later_semester_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'research/returns_2014_2026_inputs/b3';p.mkdir(parents=True)
            (p/'ibov_2020.json').write_text(json.dumps(dict(results=[dict(day=28,rateValue6='100,00'),dict(day=30,rateValue6='999,00')])))
            series=ibov_series(Path(tmp));self.assertEqual(series('2020-06-29'),100)


class ConditionalStatisticsRegression(unittest.TestCase):
    def test_boundary_ambiguity_is_preserved_instead_of_convenient_classification(self):
        frame=pd.DataFrame(dict(cnpj=list('abcd'),horizon_years=[3]*4,year=[2020]*4,calendar_complete=[True]*4,
            grade=['A','B','B','B'],wealth_multiple=[.5,.52,3.,4.5],wealth_low=[.5,.45,2.6,4.],
            wealth_high=[.5,.60,3.5,5.],ibov_wealth=[1.5]*4))
        coverage=pd.DataFrame(dict(horizon=[3]*6,dimension=['COHORT','SECTOR','SIZE_ASSETS']+['ECONOMIC_STATE']*3,
            value=['2020','SECTOR','SMALL_ASSETS','OTHER','DISTRESS_BDI','EXIT_OR_SUSPENSION'],mature_n=[4]*6,usable_fraction=[1.]*6))
        protocol=json.loads(Path('research/fundamental_multipliers_pilot/protocol_round3.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            assess(frame,coverage,protocol,Path(tmp));r=pd.read_csv(Path(tmp)/'threshold_uncertainty.csv').iloc[0]
            self.assertEqual((r.robust_loss,r.possible_loss,r.ambiguous_loss),(1,2,1))
            self.assertEqual((r.robust_3x,r.possible_3x,r.ambiguous_3x),(1,2,1))

    def test_missing_losses_can_reverse_apparent_advantage(self):
        bounds=missing_binary_bounds(1,4,3,2,10,10,10,0)
        self.assertLess(bounds['loss_advantage_low'],0);self.assertGreater(bounds['loss_advantage_high'],0)

    def test_complete_coverage_bounds_collapse_to_actual_rates(self):
        b=missing_binary_bounds(1,4,3,2,10,10,0,0)
        self.assertAlmostEqual(b['loss_advantage_low'],.3);self.assertAlmostEqual(b['loss_advantage_high'],.3)
        self.assertAlmostEqual(b['bombs_avoided_low'],.8);self.assertAlmostEqual(b['bombs_avoided_high'],.8)

    def test_cluster_resampling_does_not_gain_iid_precision_from_duplicates(self):
        f=pd.DataFrame(dict(cnpj=['a','b','c','d'],v=[2.,3.,0.,1.],s=[True,True,False,False]))
        a=cluster_difference(f,f.v,f.s,reps=199)
        duplicated=pd.concat([f]*10,ignore_index=True)
        b=cluster_difference(duplicated,duplicated.v,duplicated.s,reps=199)
        np.testing.assert_allclose(a,b)

    def test_cohort_rank_correlation_is_not_cross_cohort_inflation(self):
        f=pd.DataFrame(dict(cnpj=list('abcabc'),year=[2014]*3+[2020]*3,x=[1,2,3,100,200,300],y=[3,2,1,300,200,100]))
        effect,r=rank_effect(f,'x','y');self.assertTrue(np.isnan(effect))  # insufficient cohort n
        f=pd.concat([f]*4,ignore_index=True);effect,r=rank_effect(f,'x','y');self.assertAlmostEqual(effect,-1)


class AggregatePublicationRegression(unittest.TestCase):
    def test_individual_identifier_is_blocked_even_under_dimension_label(self):
        f=pd.DataFrame(dict(horizon=[3],cohort=[2020],cause=['BRABCDACNOR1'],n=[10]))
        with self.assertRaisesRegex(ValueError,'INDIVIDUAL_IDENTIFIER'):validate_schema(f,'uncertainty_causes.csv')

    def test_price_column_cannot_be_added_to_allowed_aggregate(self):
        f=pd.DataFrame(dict(horizon=[3],cohort=[2020],cause=['MISSING_INPUT'],n=[10],close=[20]))
        with self.assertRaisesRegex(ValueError,'SCHEMA_REJECTED'):validate_schema(f,'uncertainty_causes.csv')

    def test_small_cells_suppress_returns_without_losing_counts(self):
        f=pd.DataFrame(dict(n=[1,20],companies=[1,10],selected_n=[1,10],rejected_n=[0,10],
            selected_companies=[1,5],mean_return=[1.,.2],universe_mean_return=[1.,.1],selected_minus_rejected=[np.nan,.2]))
        s=suppress_small_cells(f);self.assertEqual(s.n.tolist(),[1,20]);self.assertTrue(pd.isna(s.mean_return.iloc[0]))
        self.assertEqual(s.mean_return.iloc[1],.2)


if __name__=='__main__':unittest.main()
