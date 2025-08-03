#!/usr/bin/env python3
"""
数据库初始化脚本（强制重建表结构，插入标准因子）
"""

import asyncio
import logging
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from app.db.database import engine, Base
# 强制导入所有模型，确保Base注册
from app.db.models import factor, stock, strategy, watchlist

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'quantitative_stock.db'

async def main():
    # 1. 删除旧数据库文件
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info(f"已删除旧数据库文件: {DB_PATH}")

    # 2. 创建新数据库并建表
    Base.metadata.create_all(engine)
    logger.info("数据库表结构创建完成")
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 3. 插入自由现金流因子
        Factor = factor.Factor
        fcf_factor = Factor(
            factor_id="fcf-ratio-factor-001",
            name="FCF_RATIO",
            display_name="自由现金流比率因子",
            description="计算自由现金流与企业价值的比率，返回原始FCF/EV值供策略层面使用",
            formula="""
# 自由现金流比率因子
# 返回原始FCF/EV值，策略层面决定如何使用

def calculate_factor(ts_code, start_date=None, end_date=None):
    \"\"\"
    计算自由现金流比率因子
    
    Args:
        ts_code: 股票代码，如 '000001.SZ'
        start_date: 开始日期，格式 'YYYYMMDD'，默认为一年前
        end_date: 结束日期，格式 'YYYYMMDD'，默认为今天
    
    Returns:
        float: 自由现金流与企业价值比率的原始值
    \"\"\"
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 如果没有指定日期，使用默认值
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    if not start_date:
        # 获取一年前的日期
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=365)
        start_date = start_dt.strftime('%Y%m%d')
    
    try:
        # 获取现金流量表数据（最新年报）
        cash_flow_df = pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if cash_flow_df.empty:
            return 0.0
        
        # 获取最新年度的自由现金流（经营活动现金流量净额）
        latest_cash_flow = cash_flow_df.sort_values('end_date').iloc[-1]
        fcf = latest_cash_flow['n_cashflow_act']  # 经营活动现金流量净额
        
        # 获取企业价值（简化计算：市值）
        basic_df = pro.daily_basic(ts_code=ts_code, start_date=end_date, end_date=end_date)
        if basic_df.empty:
            return 0.0
        
        market_cap = basic_df.iloc[0]['total_mv'] * 10000  # 转换为元
        
        # 计算FCF/EV比率
        if market_cap > 0 and fcf is not None:
            fcf_ratio = fcf / market_cap
            return float(fcf_ratio)
        else:
            return 0.0
        
    except Exception as e:
        print(f"计算FCF比率因子失败: {e}")
        return 0.0

# 调用因子计算函数
result = calculate_factor(ts_code, start_date, end_date)
""",
            normalization_method="z_score",
            normalization_code="""
# Z-score标准化方案
# 将因子值标准化为均值为0，标准差为1的分布

def normalize_factor(factor_values):
    \"\"\"
    对因子值进行Z-score标准化
    
    Args:
        factor_values: 因子值列表或Series
    
    Returns:
        normalized_values: 标准化后的因子值
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # 转换为pandas Series
    if not isinstance(factor_values, pd.Series):
        factor_values = pd.Series(factor_values)
    
    # 移除无效值
    valid_values = factor_values.dropna()
    
    if len(valid_values) == 0:
        return pd.Series([0.0] * len(factor_values), index=factor_values.index)
    
    # 计算均值和标准差
    mean_val = valid_values.mean()
    std_val = valid_values.std()
    
    # 避免除零
    if std_val == 0:
        return pd.Series([0.0] * len(factor_values), index=factor_values.index)
    
    # 进行Z-score标准化
    normalized = (factor_values - mean_val) / std_val
    
    # 处理无效值
    normalized = normalized.fillna(0.0)
    
    return normalized

# 调用标准化函数
normalized_result = normalize_factor(factor_values)
""",
            default_parameters={
                "ts_code": "000001.SZ",
                "start_date": None,
                "end_date": None
            },
            parameter_schema={
                "ts_code": {
                    "type": "string",
                    "description": "股票代码",
                    "required": True,
                    "example": "000001.SZ"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 (YYYYMMDD)",
                    "required": False,
                    "example": "20240101"
                },
                "end_date": {
                    "type": "string", 
                    "description": "结束日期 (YYYYMMDD)",
                    "required": False,
                    "example": "20240131"
                }
            },
            calculation_method="advanced_api",
            is_active=True,
            is_builtin=True,
            usage_count=0,
            last_used_at=None,
            version="1.0.0"
        )
        db.add(fcf_factor)
        
        # 4. 插入股息率因子
        dividend_factor = Factor(
            factor_id="dividend-yield-factor-001", 
            name="DIVIDEND_YIELD",
            display_name="股息率因子",
            description="计算股息率因子，返回原始股息率值供策略层面使用",
            formula="""
# 股息率因子
# 返回原始股息率值，策略层面决定如何使用

def calculate_factor(ts_code, start_date=None, end_date=None):
    \"\"\"
    计算股息率因子
    
    Args:
        ts_code: 股票代码，如 '000001.SZ'
        start_date: 开始日期，格式 'YYYYMMDD'，默认为一年前
        end_date: 结束日期，格式 'YYYYMMDD'，默认为今天
    
    Returns:
        float: 原始股息率值
    \"\"\"
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 如果没有指定日期，使用默认值
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    if not start_date:
        # 获取一年前的日期
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=365)
        start_date = start_dt.strftime('%Y%m%d')
    
    try:
        # 获取分红数据（TTM股息）
        dividend_df = pro.dividend(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if dividend_df.empty:
            return 0.0
        
        # 计算TTM股息（近一年分红总和）
        ttm_dividend = dividend_df['div_proc'].sum()  # 分红金额
        
        # 获取当前市值
        basic_df = pro.daily_basic(ts_code=ts_code, start_date=end_date, end_date=end_date)
        if basic_df.empty:
            return 0.0
        
        market_cap = basic_df.iloc[0]['total_mv'] * 10000  # 转换为元
        
        # 计算股息率
        if market_cap > 0 and ttm_dividend > 0:
            dividend_yield = ttm_dividend / market_cap
            return float(dividend_yield)
        else:
            return 0.0
            
    except Exception as e:
        print(f"计算股息率因子失败: {e}")
        return 0.0

# 调用因子计算函数
result = calculate_factor(ts_code, start_date, end_date)
""",
            normalization_method="z_score",
            normalization_code="""
# Z-score标准化方案
# 将因子值标准化为均值为0，标准差为1的分布

def normalize_factor(factor_values):
    \"\"\"
    对因子值进行Z-score标准化
    
    Args:
        factor_values: 因子值列表或Series
    
    Returns:
        normalized_values: 标准化后的因子值
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # 转换为pandas Series
    if not isinstance(factor_values, pd.Series):
        factor_values = pd.Series(factor_values)
    
    # 移除无效值
    valid_values = factor_values.dropna()
    
    if len(valid_values) == 0:
        return pd.Series([0.0] * len(factor_values), index=factor_values.index)
    
    # 计算均值和标准差
    mean_val = valid_values.mean()
    std_val = valid_values.std()
    
    # 避免除零
    if std_val == 0:
        return pd.Series([0.0] * len(factor_values), index=factor_values.index)
    
    # 进行Z-score标准化
    normalized = (factor_values - mean_val) / std_val
    
    # 处理无效值
    normalized = normalized.fillna(0.0)
    
    return normalized

# 调用标准化函数
normalized_result = normalize_factor(factor_values)
""",
            default_parameters={
                "ts_code": "000001.SZ",
                "start_date": None,
                "end_date": None
            },
            parameter_schema={
                "ts_code": {
                    "type": "string",
                    "description": "股票代码",
                    "required": True,
                    "example": "000001.SZ"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 (YYYYMMDD)",
                    "required": False,
                    "example": "20240101"
                },
                "end_date": {
                    "type": "string", 
                    "description": "结束日期 (YYYYMMDD)",
                    "required": False,
                    "example": "20240131"
                }
            },
            calculation_method="advanced_api",
            is_active=True,
            is_builtin=True,
            usage_count=0,
            last_used_at=None,
            version="1.0.0"
        )
        db.add(dividend_factor)
        
        # 5. 创建价值投资策略模板
        from app.db.models.strategy import Strategy, StrategyTemplate
        
        value_strategy = Strategy(
            strategy_id="value-investment-strategy-001",
            name="价值投资策略",
            description="基于自由现金流和股息率的价值投资策略，筛选具有良好现金流和分红能力的股票",
            factors=[
                {
                    "factor_id": "fcf-ratio-factor-001",
                    "weight": 0.6,
                    "is_enabled": True,
                    "parameters": {}
                },
                {
                    "factor_id": "dividend-yield-factor-001", 
                    "weight": 0.4,
                    "is_enabled": True,
                    "parameters": {}
                }
            ],
            filters={
                "exclude_st": True,
                "exclude_new_stock": True,
                "min_market_cap": 50,  # 最小市值50亿
                "max_market_cap": 5000,  # 最大市值5000亿
                "min_turnover": 0.5  # 最小换手率0.5%
            },
            config={
                "max_results": 20,
                "rebalance_frequency": "monthly",
                "ranking_method": "composite_score"
            },
            is_active=True,
            created_by="system",
            execution_count=0,
            avg_execution_time=None,
            last_result_count=None
        )
        db.add(value_strategy)
        
        # 6. 创建策略模板
        value_template = StrategyTemplate(
            template_id="value-investment-template-001",
            name="价值投资模板",
            description="经典价值投资策略模板，结合自由现金流和股息率指标",
            category="value",
            factors=[
                {
                    "factor_id": "fcf-ratio-factor-001",
                    "weight": 0.6,
                    "is_enabled": True,
                    "parameters": {}
                },
                {
                    "factor_id": "dividend-yield-factor-001",
                    "weight": 0.4, 
                    "is_enabled": True,
                    "parameters": {}
                }
            ],
            filters={
                "exclude_st": True,
                "exclude_new_stock": True,
                "min_market_cap": 50,
                "max_market_cap": 5000,
                "min_turnover": 0.5
            },
            config={
                "max_results": 20,
                "rebalance_frequency": "monthly",
                "ranking_method": "composite_score"
            },
            is_active=True,
            is_builtin=True,
            usage_count=0
        )
        db.add(value_template)
        
        db.commit()
        logger.info("已插入自由现金流比率和股息率标准因子，以及价值投资策略模板")
    except Exception as e:
        logger.error(f"插入因子失败: {e}")
        db.rollback()
    finally:
        db.close()
    logger.info("数据库初始化完成！")

if __name__ == "__main__":
    asyncio.run(main())