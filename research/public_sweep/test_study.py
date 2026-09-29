"""Accounting/causality contracts, executed before any network data collection."""
import unittest
import numpy as np
import pandas as pd
from run_study import (french_csv, complete_panel, simulate, self_finance,
    target_at, moving_average, parameter_grid, block_diagnostic, metrics, ETFS)

class Contracts(unittest.TestCase):
    def params(self, **kw):
        return dict(family="momentum",lookback=2,skip=0,top_k=1,every=1,trend=0)|kw

    def test_first_french_table_and_missing_sentinel(self):
        text="Source header\n,A,B\n20000103,1.0,-99.99\n20000104,-2.0,3.0\n\n,A,B\n20000103,99,99\n"
        frame=french_csv(text,2)
        self.assertEqual(frame.shape,(2,2))
        self.assertEqual(frame.iloc[0,0],.01)
        self.assertTrue(np.isnan(frame.iloc[0,1]))
        self.assertAlmostEqual(frame.iloc[1,0],-.02)
        with self.assertRaises(ValueError):
            french_csv(",A,B\n20000103,1,2\n20000103,1,2\n",2)

    def test_missing_session_fails_instead_of_compressing_time(self):
        dates=pd.bdate_range("1994-01-01","2001-01-01")
        frame=pd.DataFrame(100.,index=dates,columns=["A"])
        frame=frame.drop(dates[200])
        with self.assertRaisesRegex(ValueError,"Missing"):
            complete_panel(frame,dates,"2000-01-01","1994-01-01")

    def test_full_session_delay_and_future_mutation(self):
        levels=np.full((25,2),100.)
        levels[1:,0]=110.
        # At i=4, feature 2 sees A's gain. The jump in B at day3 is not yet usable.
        levels[3:,1]=200.
        levels[4:,0]=121.
        p=self.params()
        r,_,_=simulate(levels,np.zeros(25),4,p,costs=np.array([0.]))
        self.assertAlmostEqual(r[0,0],.1)
        changed=levels.copy();changed[15:]=changed[15:]*np.array([2.,.5])
        altered=simulate(changed,np.zeros(25),4,p,costs=np.array([0.]))[0]
        np.testing.assert_array_equal(r[:11],altered[:11])

    def test_skip_window_changes_ranking(self):
        levels=np.full((12,2),100.)
        levels[1:,0]=110.
        levels[3:,1]=200.
        average={}
        target=target_at(levels,3,self.params(skip=1),average)
        np.testing.assert_array_equal(target,[1.,0.])

    def test_exact_cost_solver_against_bisection(self):
        rng=np.random.default_rng(72)
        for _ in range(40):
            old=rng.dirichlet(np.ones(6))[:5]
            target=rng.dirichlet(np.ones(6))[:5]
            g,trade=self_finance(target,old,np.array([0.,.0005,.001,.0025]))
            for j,c in enumerate([0.,.0005,.001,.0025]):
                lo,hi=0.,1.
                for k in range(60):
                    mid=(lo+hi)/2
                    if mid+c*np.abs(mid*target-old).sum()>1:hi=mid
                    else:lo=mid
                self.assertAlmostEqual(g[j],(lo+hi)/2,places=12)
                self.assertAlmostEqual(g[j]+c*trade[j],1.,places=12)

    def test_entry_and_terminal_liquidation_from_cash(self):
        levels=np.full((20,1),100.)
        result,_,_=simulate(levels,np.zeros(20),4,self.params(every=100),costs=np.array([.001]))
        # Buy notional solves amount + fee = initial cash; sell all at final close.
        self.assertAlmostEqual(np.prod(1+result[:,0]),(1-.001)/(1+.001),places=12)

    def test_all_cash_filter_earns_rf_without_trading(self):
        levels=np.arange(300.,0.,-1)[:,None]
        r,t,e=simulate(levels,np.full(300,.0001),220,self.params(trend=100))
        np.testing.assert_allclose(r,.0001,atol=1e-14)
        np.testing.assert_array_equal(t,0)
        np.testing.assert_array_equal(e,0)

    def test_drift_and_equal_universe_holdings(self):
        levels=np.ones((12,2))*100
        levels[5:,0]=120
        r,t,e=simulate(levels,np.zeros(12),4,dict(family="equal",every=100),costs=np.array([0.]))
        self.assertAlmostEqual(np.prod(1+r[:,0]),1.1)
        self.assertAlmostEqual(r[1,0],.1)
        self.assertEqual(t[1,0],0.)
        self.assertAlmostEqual(e[-1],1.)

    def test_no_filling_unavailable_slots(self):
        levels=np.ones((300,3))*100
        levels[:,0]=np.arange(100,400)
        levels[:,1]=np.arange(400,100,-1)
        levels[:,2]=np.arange(400,100,-1)
        av={100:moving_average(levels,100)}
        target=target_at(levels,250,self.params(trend=100,top_k=3),av)
        self.assertAlmostEqual(target.sum(),1/3)

    def test_cost_monotonicity_and_wealth_lineage(self):
        rng=np.random.default_rng(19)
        levels=100*np.cumprod(1+rng.normal(.0002,.01,(400,5)),axis=0)
        r,_,_=simulate(levels,np.zeros(400),280,self.params(top_k=3,every=5))
        wealth=np.prod(1+r,axis=0)
        self.assertTrue(np.all(np.diff(wealth)<=0))

    def test_input_unchanged_and_bad_levels_fail(self):
        levels=np.ones((300,2))*100;prior=levels.copy()
        simulate(levels,np.zeros(300),280,self.params())
        np.testing.assert_array_equal(levels,prior)
        levels[290,0]=np.nan
        with self.assertRaises(ValueError):
            simulate(levels,np.zeros(300),280,self.params())

    def test_bootstrap_zero_null_and_determinism(self):
        x=np.zeros((252,4))
        a=block_diagnostic(x,0,21,reps=29)
        self.assertEqual(a["centered_max_mean_p"],1.)
        self.assertEqual(a["selected_annual_mean_interval"],[0.,0.])
        self.assertEqual(a,block_diagnostic(x,0,21,reps=29))

    def test_metrics_drawdown_from_initial_capital(self):
        r=np.array([-.2,.25,0.,0.])
        m=metrics(r,np.zeros(4),np.zeros(4),np.ones(4))
        self.assertAlmostEqual(m["total_return"],0)
        self.assertAlmostEqual(m["max_drawdown"],-.2)

    def test_grid_counts_and_no_duplicate_etfs(self):
        grid=parameter_grid()
        self.assertEqual(len(grid),459)
        self.assertEqual(sum(v["family"]=="momentum" for v in grid),324)
        self.assertEqual(len({tuple(v.items()) for v in grid}),459)
        self.assertEqual(len(ETFS),36)

if __name__=="__main__":
    unittest.main()
