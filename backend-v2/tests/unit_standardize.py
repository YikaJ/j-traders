from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.standardize import zscore_df


def test_zscore_basic():
    df = pd.DataFrame({
        'trade_date': ['20210101']*5 + ['20210108']*5,
        'factor': [1,2,3,4,5, 2,4,6,8,10],
    })
    out = zscore_df(df, value_col='factor', by=['trade_date'], winsor=None, fill='median')
    g1 = out[out['trade_date']=='20210101']['factor']
    g2 = out[out['trade_date']=='20210108']['factor']
    assert abs(g1.mean()) < 1e-8
    assert abs(g2.mean()) < 1e-8
    assert abs(g1.std(ddof=0) - 1) < 1e-8
    assert abs(g2.std(ddof=0) - 1) < 1e-8
