"""
Tushare数据适配配置
配置Tushare API的各种参数和数据字段映射
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class TushareConfig:
    """Tushare配置类"""
    
    # API配置
    token: Optional[str] = None
    timeout: int = 30
    retry_times: int = 3
    retry_delay: float = 1.0
    
    # 数据频率
    freq: str = 'D'  # D-日线，W-周线，M-月线
    
    # 复权类型
    adj: str = 'qfq'  # qfq-前复权，hfq-后复权，None-不复权
    
    # 数据获取限制
    max_records_per_request: int = 5000
    
    @classmethod
    def from_env(cls) -> 'TushareConfig':
        """从环境变量创建配置"""
        return cls(
            token=os.getenv('TUSHARE_TOKEN'),
            timeout=int(os.getenv('TUSHARE_TIMEOUT', '30')),
            retry_times=int(os.getenv('TUSHARE_RETRY_TIMES', '3')),
            retry_delay=float(os.getenv('TUSHARE_RETRY_DELAY', '1.0'))
        )


class TushareDataType(Enum):
    """Tushare数据类型"""
    DAILY = "daily"           # 日线数据
    WEEKLY = "weekly"         # 周线数据
    MONTHLY = "monthly"       # 月线数据
    BASIC = "stock_basic"     # 股票基础信息
    INDUSTRY = "hs_const"     # 行业分类
    FINANCIAL = "fina_indicator"  # 财务指标
    ADJ_FACTOR = "adj_factor"     # 复权因子


# Tushare字段映射配置
TUSHARE_FIELD_MAPPING = {
    # 基础行情数据字段映射
    'daily': {
        'ts_code': 'stock_code',
        'trade_date': 'date',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'pre_close': 'pre_close',
        'change': 'change',
        'pct_chg': 'pct_change',
        'vol': 'volume',
        'amount': 'amount'
    },
    
    # 股票基础信息字段映射
    'stock_basic': {
        'ts_code': 'stock_code',
        'symbol': 'symbol',
        'name': 'name',
        'area': 'area',
        'industry': 'industry',
        'market': 'market',
        'list_date': 'list_date',
        'list_status': 'list_status',
        'delist_date': 'delist_date',
        'is_hs': 'is_hs'
    },
    
    # 行业分类字段映射
    'hs_const': {
        'ts_code': 'stock_code',
        'hs_type': 'industry_type',
        'in_date': 'in_date',
        'out_date': 'out_date',
        'is_new': 'is_new'
    },
    
    # 复权因子字段映射
    'adj_factor': {
        'ts_code': 'stock_code',
        'trade_date': 'date',
        'adj_factor': 'adj_factor'
    }
}

# A股市场特有的数据配置
A_STOCK_CONFIG = {
    # 交易所代码映射
    'exchange_mapping': {
        'SZ': '深交所',
        'SH': '上交所',
        'BJ': '北交所'
    },
    
    # 行业分类标准
    'industry_standards': {
        'SW2021': '申万2021年行业分类',
        'ZJW': '证监会行业分类',
        'GICS': 'GICS行业分类'
    },
    
    # 股票状态
    'stock_status': {
        'L': '上市',
        'D': '退市',
        'P': '暂停上市'
    },
    
    # 特殊处理股票标识
    'special_treatment': {
        'ST': 'ST股票',
        '*ST': '*ST股票',
        'SST': 'SST股票',
        'S*ST': 'S*ST股票'
    }
}

# Alpha101因子计算所需的基础数据字段
ALPHA101_REQUIRED_FIELDS = [
    'date',           # 交易日期
    'open',           # 开盘价
    'high',           # 最高价
    'low',            # 最低价
    'close',          # 收盘价
    'volume',         # 成交量
    'amount',         # 成交额
    'pre_close',      # 前收盘价
    'pct_change',     # 涨跌幅
    'adj_factor'      # 复权因子（可选）
]

# Tushare API调用配置
TUSHARE_API_CONFIG = {
    # 日线数据接口
    'daily': {
        'api_name': 'daily',
        'required_params': ['ts_code'],
        'optional_params': ['trade_date', 'start_date', 'end_date'],
        'frequency_limit': 200,  # 每分钟调用次数限制
        'fields': 'ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
    },
    
    # 股票基础信息接口
    'stock_basic': {
        'api_name': 'stock_basic',
        'required_params': [],
        'optional_params': ['exchange', 'list_status', 'is_hs'],
        'frequency_limit': 100,
        'fields': 'ts_code,symbol,name,area,industry,market,list_date,list_status'
    },
    
    # 行业分类接口
    'hs_const': {
        'api_name': 'hs_const',
        'required_params': ['hs_type'],
        'optional_params': ['ts_code'],
        'frequency_limit': 100,
        'fields': 'ts_code,hs_type,in_date,out_date,is_new'
    },
    
    # 复权因子接口
    'adj_factor': {
        'api_name': 'adj_factor',
        'required_params': ['ts_code'],
        'optional_params': ['trade_date', 'start_date', 'end_date'],
        'frequency_limit': 200,
        'fields': 'ts_code,trade_date,adj_factor'
    }
}

# 数据质量检查配置
DATA_QUALITY_CONFIG = {
    # 价格数据合理性检查
    'price_checks': {
        'max_daily_change': 0.2,  # 最大日涨跌幅
        'min_price': 0.01,        # 最小价格
        'max_price': 10000,       # 最大价格
    },
    
    # 成交量数据检查
    'volume_checks': {
        'min_volume': 0,          # 最小成交量
        'max_volume_ratio': 10,   # 最大成交量比率（相对历史均值）
    },
    
    # 数据完整性检查
    'completeness_checks': {
        'required_fields': ALPHA101_REQUIRED_FIELDS,
        'min_data_points': 250,   # 最少数据点数（用于因子计算）
    }
}

# 默认配置实例
DEFAULT_TUSHARE_CONFIG = TushareConfig.from_env()


def get_stock_code_format(symbol: str, exchange: str = None) -> str:
    """
    格式化股票代码为Tushare格式
    
    Args:
        symbol: 股票代码（如'000001'）
        exchange: 交易所（如'SZ'、'SH'）
    
    Returns:
        Tushare格式的股票代码（如'000001.SZ'）
    """
    if '.' in symbol:
        return symbol
    
    if exchange:
        return f"{symbol}.{exchange}"
    
    # 根据代码规则自动判断交易所
    if symbol.startswith('0') or symbol.startswith('3'):
        return f"{symbol}.SZ"  # 深交所
    elif symbol.startswith('6'):
        return f"{symbol}.SH"  # 上交所
    elif symbol.startswith('8') or symbol.startswith('4'):
        return f"{symbol}.BJ"  # 北交所
    else:
        raise ValueError(f"无法识别股票代码 {symbol} 的交易所")


def validate_tushare_config(config: TushareConfig) -> bool:
    """
    验证Tushare配置
    
    Args:
        config: Tushare配置
        
    Returns:
        配置是否有效
    """
    if not config.token:
        raise ValueError("Tushare token不能为空")
    
    if config.timeout <= 0:
        raise ValueError("超时时间必须大于0")
    
    if config.retry_times < 0:
        raise ValueError("重试次数不能为负数")
    
    if config.retry_delay < 0:
        raise ValueError("重试延迟不能为负数")
    
    return True


def get_api_config(api_type: str) -> Dict:
    """
    获取指定API类型的配置
    
    Args:
        api_type: API类型
        
    Returns:
        API配置字典
    """
    if api_type not in TUSHARE_API_CONFIG:
        raise ValueError(f"不支持的API类型: {api_type}")
    
    return TUSHARE_API_CONFIG[api_type]