"""
真实Tushare数据字段服务
基于Tushare实际API接口提供数据字段映射
"""

from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

from app.schemas.data_fields import (
    DataField, DataFieldConfig, DataFieldCategory, DataFieldType,
    FactorInputFieldsRequest, FactorInputFieldsResponse
)

logger = logging.getLogger(__name__)


@dataclass
class TushareApiInfo:
    """Tushare API接口信息"""
    api_name: str
    description: str
    required_params: List[str]
    optional_params: List[str]
    fields: List[str]
    example_call: str
    frequency_limit: int = 200


class RealTushareFieldService:
    """真实Tushare数据字段服务"""
    
    def __init__(self):
        self._api_configs = self._initialize_api_configs()
        self._field_configs = self._initialize_field_configs()
    
    def _initialize_api_configs(self) -> Dict[str, TushareApiInfo]:
        """初始化Tushare API配置"""
        return {
            'daily': TushareApiInfo(
                api_name='daily',
                description='日线行情数据',
                required_params=['ts_code'],
                optional_params=['trade_date', 'start_date', 'end_date'],
                fields=['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount'],
                example_call="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')",
                frequency_limit=200
            ),
            'daily_basic': TushareApiInfo(
                api_name='daily_basic',
                description='每日指标数据',
                required_params=['ts_code'],
                optional_params=['trade_date', 'start_date', 'end_date'],
                fields=['ts_code', 'trade_date', 'turnover_rate', 'turnover_rate_f', 'volume_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm', 'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'],
                example_call="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')",
                frequency_limit=200
            ),
            'adj_factor': TushareApiInfo(
                api_name='adj_factor',
                description='复权因子数据',
                required_params=['ts_code'],
                optional_params=['trade_date', 'start_date', 'end_date'],
                fields=['ts_code', 'trade_date', 'adj_factor'],
                example_call="pro.adj_factor(ts_code='000001.SZ', start_date='20240101', end_date='20240131')",
                frequency_limit=200
            ),
            'stock_basic': TushareApiInfo(
                api_name='stock_basic',
                description='股票基础信息',
                required_params=[],
                optional_params=['exchange', 'list_status', 'is_hs'],
                fields=['ts_code', 'symbol', 'name', 'area', 'industry', 'market', 'list_date', 'list_status'],
                example_call="pro.stock_basic(exchange='', list_status='L')",
                frequency_limit=100
            ),
            'fina_indicator': TushareApiInfo(
                api_name='fina_indicator',
                description='财务指标数据',
                required_params=['ts_code'],
                optional_params=['period', 'start_date', 'end_date'],
                fields=['ts_code', 'end_date', 'eps', 'roe', 'roa', 'grossprofit_margin', 'netprofits_margin', 'debt_to_assets', 'current_ratio', 'quick_ratio'],
                example_call="pro.fina_indicator(ts_code='000001.SZ', period='20231231')",
                frequency_limit=100
            ),
            'income': TushareApiInfo(
                api_name='income',
                description='利润表数据',
                required_params=['ts_code'],
                optional_params=['period', 'start_date', 'end_date'],
                fields=['ts_code', 'end_date', 'revenue', 'operate_profit', 'total_profit', 'n_income', 'n_income_attr_p'],
                example_call="pro.income(ts_code='000001.SZ', period='20231231')",
                frequency_limit=100
            ),
            'balance_sheet': TushareApiInfo(
                api_name='balance_sheet',
                description='资产负债表数据',
                required_params=['ts_code'],
                optional_params=['period', 'start_date', 'end_date'],
                fields=['ts_code', 'end_date', 'total_assets', 'total_liab', 'total_cur_assets', 'total_cur_liab', 'total_equity'],
                example_call="pro.balance_sheet(ts_code='000001.SZ', period='20231231')",
                frequency_limit=100
            ),
            'cashflow': TushareApiInfo(
                api_name='cashflow',
                description='现金流量表数据',
                required_params=['ts_code'],
                optional_params=['period', 'start_date', 'end_date'],
                fields=['ts_code', 'end_date', 'n_cashflow_act', 'n_cashflow_inv_act', 'n_cash_flows_fnc_act', 'free_cashflow'],
                example_call="pro.cashflow(ts_code='000001.SZ', period='20231231')",
                frequency_limit=100
            )
        }
    
    def _initialize_field_configs(self) -> List[DataFieldConfig]:
        """初始化数据字段配置"""
        configs = []
        
        # 价格类数据字段 (来自daily接口)
        price_fields = [
            DataField(
                field_id="close",
                field_name="close",
                display_name="收盘价",
                description="当日收盘价格，用于计算移动平均线等技术指标",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=True,
                is_common=True,
                tushare_field="close",
                tushare_api="daily",
                example_value="12.34",
                validation_rules={"min": 0, "max": 10000},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="open",
                field_name="open",
                display_name="开盘价",
                description="当日开盘价格",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="open",
                tushare_api="daily",
                example_value="12.45",
                validation_rules={"min": 0, "max": 10000},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="high",
                field_name="high",
                display_name="最高价",
                description="当日最高价格",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="high",
                tushare_api="daily",
                example_value="12.89",
                validation_rules={"min": 0, "max": 10000},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="low",
                field_name="low",
                display_name="最低价",
                description="当日最低价格",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="low",
                tushare_api="daily",
                example_value="12.01",
                validation_rules={"min": 0, "max": 10000},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="pre_close",
                field_name="pre_close",
                display_name="前收盘价",
                description="前一日收盘价格，除权价，前复权",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="pre_close",
                tushare_api="daily",
                example_value="12.20",
                validation_rules={"min": 0, "max": 10000},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="volume",
                field_name="volume",
                display_name="成交量",
                description="当日成交量（手）",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="手",
                is_required=False,
                is_common=True,
                tushare_field="vol",
                tushare_api="daily",
                example_value="123456",
                validation_rules={"min": 0},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="amount",
                field_name="amount",
                display_name="成交额",
                description="当日成交额（千元）",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="千元",
                is_required=False,
                is_common=True,
                tushare_field="amount",
                tushare_api="daily",
                example_value="1523456",
                validation_rules={"min": 0},
                api_call_example="pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            )
        ]
        
        # 基本面数据字段 (来自daily_basic接口)
        fundamental_fields = [
            DataField(
                field_id="pe_ttm",
                field_name="pe_ttm",
                display_name="市盈率TTM",
                description="市盈率（滚动12个月）",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="倍",
                is_required=False,
                is_common=True,
                tushare_field="pe_ttm",
                tushare_api="daily_basic",
                example_value="15.5",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="pb",
                field_name="pb",
                display_name="市净率",
                description="市净率",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="倍",
                is_required=False,
                is_common=True,
                tushare_field="pb",
                tushare_api="daily_basic",
                example_value="1.8",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="ps_ttm",
                field_name="ps_ttm",
                display_name="市销率TTM",
                description="市销率（滚动12个月）",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="倍",
                is_required=False,
                is_common=False,
                tushare_field="ps_ttm",
                tushare_api="daily_basic",
                example_value="2.5",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="total_share",
                field_name="total_share",
                display_name="总股本",
                description="总股本数量",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="万股",
                is_required=False,
                is_common=True,
                tushare_field="total_share",
                tushare_api="daily_basic",
                example_value="100000",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="float_share",
                field_name="float_share",
                display_name="流通股本",
                description="流通股本数量",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="万股",
                is_required=False,
                is_common=True,
                tushare_field="float_share",
                tushare_api="daily_basic",
                example_value="80000",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="total_mv",
                field_name="total_mv",
                display_name="总市值",
                description="总市值",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="万元",
                is_required=False,
                is_common=True,
                tushare_field="total_mv",
                tushare_api="daily_basic",
                example_value="1234567",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            ),
            DataField(
                field_id="circ_mv",
                field_name="circ_mv",
                display_name="流通市值",
                description="流通市值",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="万元",
                is_required=False,
                is_common=True,
                tushare_field="circ_mv",
                tushare_api="daily_basic",
                example_value="987654",
                validation_rules={"min": 0},
                api_call_example="pro.daily_basic(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            )
        ]
        
        # 复权因子字段 (来自adj_factor接口)
        adj_factor_fields = [
            DataField(
                field_id="adj_factor",
                field_name="adj_factor",
                display_name="复权因子",
                description="复权因子，用于前复权计算",
                category=DataFieldCategory.DERIVED,
                field_type=DataFieldType.NUMERIC,
                unit="",
                is_required=False,
                is_common=False,
                tushare_field="adj_factor",
                tushare_api="adj_factor",
                example_value="1.0",
                validation_rules={"min": 0},
                api_call_example="pro.adj_factor(ts_code='000001.SZ', start_date='20240101', end_date='20240131')"
            )
        ]
        
        # 财务指标字段 (来自fina_indicator接口)
        financial_fields = [
            DataField(
                field_id="roe",
                field_name="roe",
                display_name="净资产收益率",
                description="净资产收益率",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=False,
                tushare_field="roe",
                tushare_api="fina_indicator",
                example_value="12.5",
                validation_rules={"min": -100, "max": 100},
                api_call_example="pro.fina_indicator(ts_code='000001.SZ', period='20231231')"
            ),
            DataField(
                field_id="roa",
                field_name="roa",
                display_name="总资产收益率",
                description="总资产收益率",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=False,
                tushare_field="roa",
                tushare_api="fina_indicator",
                example_value="8.2",
                validation_rules={"min": -100, "max": 100},
                api_call_example="pro.fina_indicator(ts_code='000001.SZ', period='20231231')"
            ),
            DataField(
                field_id="grossprofit_margin",
                field_name="grossprofit_margin",
                display_name="毛利率",
                description="毛利率",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=False,
                tushare_field="grossprofit_margin",
                tushare_api="fina_indicator",
                example_value="25.6",
                validation_rules={"min": -100, "max": 100},
                api_call_example="pro.fina_indicator(ts_code='000001.SZ', period='20231231')"
            )
        ]
        
        # 按类别组织字段
        configs.append(DataFieldConfig(
            category=DataFieldCategory.PRICE,
            display_name="价格数据",
            description="股票价格相关数据，来自Tushare daily接口",
            fields=price_fields
        ))
        
        configs.append(DataFieldConfig(
            category=DataFieldCategory.FUNDAMENTAL,
            display_name="基本面数据",
            description="股票基本面指标，来自Tushare daily_basic和fina_indicator接口",
            fields=fundamental_fields + financial_fields
        ))
        
        configs.append(DataFieldConfig(
            category=DataFieldCategory.DERIVED,
            display_name="衍生数据",
            description="复权因子等衍生数据",
            fields=adj_factor_fields
        ))
        
        return configs
    
    def get_field_by_name(self, field_name: str) -> Optional[DataField]:
        """根据字段名获取字段配置"""
        for config in self._field_configs:
            for field in config.fields:
                if field.field_name == field_name:
                    return field
        return None
    
    def get_api_info(self, api_name: str) -> Optional[TushareApiInfo]:
        """获取API接口信息"""
        return self._api_configs.get(api_name)
    
    def get_fields_by_api(self, api_name: str) -> List[DataField]:
        """根据API接口获取相关字段"""
        fields = []
        for config in self._field_configs:
            for field in config.fields:
                if hasattr(field, 'tushare_api') and field.tushare_api == api_name:
                    fields.append(field)
        return fields
    
    def get_required_apis_for_fields(self, field_names: List[str]) -> List[str]:
        """根据字段名列表获取所需的API接口"""
        required_apis = set()
        for field_name in field_names:
            field = self.get_field_by_name(field_name)
            if field and hasattr(field, 'tushare_api'):
                required_apis.add(field.tushare_api)
        return list(required_apis)
    
    def generate_api_calls(self, field_names: List[str]) -> Dict[str, str]:
        """根据字段名生成对应的API调用代码"""
        api_calls = {}
        for field_name in field_names:
            field = self.get_field_by_name(field_name)
            if field and hasattr(field, 'api_call_example'):
                api_name = field.tushare_api
                if api_name not in api_calls:
                    api_calls[api_name] = field.api_call_example
        
        return api_calls 