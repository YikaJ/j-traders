import tushare as ts

pro = ts.pro_api('TUSHARE_TOKEN')
df = pro.daily_basic(ts_code='000001.SZ', start_date='20250808')
print(df)