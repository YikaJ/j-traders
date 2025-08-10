import os
import pytest
import tushare as ts

token = os.getenv("TUSHARE_TOKEN")
if not token:
    pytest.skip("TUSHARE_TOKEN not set; skipping external TuShare call", allow_module_level=True)

pro = ts.pro_api(token)
df = pro.daily_basic(ts_code='000001.SZ', start_date='20250808')
print(df)