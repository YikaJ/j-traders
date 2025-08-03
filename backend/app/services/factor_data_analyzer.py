"""
因子数据需求分析器
负责分析因子公式，自动推断所需的数据字段，并映射到相应的Tushare API接口
"""

import re
import ast
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TushareInterface(Enum):
    """Tushare接口枚举"""
    DAILY = "daily"                    # 日线数据
    DAILY_BASIC = "daily_basic"        # 每日基本面数据
    INCOME = "income"                  # 利润表
    BALANCESHEET = "balancesheet"      # 资产负债表
    CASHFLOW = "cashflow"              # 现金流量表
    FORECAST = "forecast"              # 业绩预告
    EXPRESS = "express"                # 业绩快报
    DIVIDEND = "dividend"              # 分红送股
    FIN_INDICATOR = "fina_indicator"   # 财务指标数据
    TOP10_HOLDERS = "top10_holders"    # 前十大股东
    TOP10_FLOATHOLDERS = "top10_floatholders"  # 前十大流通股东


@dataclass
class FieldMapping:
    """字段映射信息"""
    tushare_field: str      # Tushare API中的字段名
    interface: TushareInterface  # 所属接口
    description: str        # 字段描述
    data_type: str         # 数据类型
    is_required: bool = False  # 是否必需字段


class FactorDataAnalyzer:
    """因子数据需求分析器"""
    
    def __init__(self):
        self.field_mappings = self._init_field_mappings()
        self.keyword_patterns = self._init_keyword_patterns()
    
    def _init_field_mappings(self) -> Dict[str, FieldMapping]:
        """初始化字段映射表"""
        mappings = {}
        
        # 基础行情数据字段 (daily接口)
        daily_fields = {
            'open': FieldMapping('open', TushareInterface.DAILY, '开盘价', 'float'),
            'close': FieldMapping('close', TushareInterface.DAILY, '收盘价', 'float', True),
            'high': FieldMapping('high', TushareInterface.DAILY, '最高价', 'float'),
            'low': FieldMapping('low', TushareInterface.DAILY, '最低价', 'float'),
            'vol': FieldMapping('vol', TushareInterface.DAILY, '成交量', 'float'),
            'amount': FieldMapping('amount', TushareInterface.DAILY, '成交额', 'float'),
            'pre_close': FieldMapping('pre_close', TushareInterface.DAILY, '昨收价', 'float'),
            'change': FieldMapping('change', TushareInterface.DAILY, '涨跌额', 'float'),
            'pct_chg': FieldMapping('pct_chg', TushareInterface.DAILY, '涨跌幅', 'float'),
            'price': FieldMapping('close', TushareInterface.DAILY, '价格(收盘价)', 'float'),
            'volume': FieldMapping('vol', TushareInterface.DAILY, '成交量', 'float'),
        }
        mappings.update(daily_fields)
        
        # 每日基本面数据 (daily_basic接口)
        basic_fields = {
            'turnover_rate': FieldMapping('turnover_rate', TushareInterface.DAILY_BASIC, '换手率', 'float'),
            'turnover_rate_f': FieldMapping('turnover_rate_f', TushareInterface.DAILY_BASIC, '换手率(自由流通股)', 'float'),
            'volume_ratio': FieldMapping('volume_ratio', TushareInterface.DAILY_BASIC, '量比', 'float'),
            'pe': FieldMapping('pe', TushareInterface.DAILY_BASIC, '市盈率', 'float'),
            'pe_ttm': FieldMapping('pe_ttm', TushareInterface.DAILY_BASIC, '市盈率TTM', 'float'),
            'pb': FieldMapping('pb', TushareInterface.DAILY_BASIC, '市净率', 'float'),
            'ps': FieldMapping('ps', TushareInterface.DAILY_BASIC, '市销率', 'float'),
            'ps_ttm': FieldMapping('ps_ttm', TushareInterface.DAILY_BASIC, '市销率TTM', 'float'),
            'dv_ratio': FieldMapping('dv_ratio', TushareInterface.DAILY_BASIC, '股息率', 'float'),
            'dv_ttm': FieldMapping('dv_ttm', TushareInterface.DAILY_BASIC, '股息率TTM', 'float'),
            'total_share': FieldMapping('total_share', TushareInterface.DAILY_BASIC, '总股本', 'float'),
            'float_share': FieldMapping('float_share', TushareInterface.DAILY_BASIC, '流通股本', 'float'),
            'free_share': FieldMapping('free_share', TushareInterface.DAILY_BASIC, '自由流通股本', 'float'),
            'total_mv': FieldMapping('total_mv', TushareInterface.DAILY_BASIC, '总市值', 'float'),
            'circ_mv': FieldMapping('circ_mv', TushareInterface.DAILY_BASIC, '流通市值', 'float'),
            'market_cap': FieldMapping('total_mv', TushareInterface.DAILY_BASIC, '市值(总市值)', 'float'),
        }
        mappings.update(basic_fields)
        
        # 财务指标数据 (fina_indicator接口)
        financial_fields = {
            'roe': FieldMapping('roe', TushareInterface.FIN_INDICATOR, 'ROE', 'float'),
            'roa': FieldMapping('roa', TushareInterface.FIN_INDICATOR, 'ROA', 'float'),
            'roic': FieldMapping('roic', TushareInterface.FIN_INDICATOR, 'ROIC', 'float'),
            'roe_waa': FieldMapping('roe_waa', TushareInterface.FIN_INDICATOR, 'ROE加权', 'float'),
            'dt_roe': FieldMapping('dt_roe', TushareInterface.FIN_INDICATOR, 'ROE摊薄', 'float'),
            'debt_to_assets': FieldMapping('debt_to_assets', TushareInterface.FIN_INDICATOR, '资产负债率', 'float'),
            'assets_to_eqt': FieldMapping('assets_to_eqt', TushareInterface.FIN_INDICATOR, '权益乘数', 'float'),
            'current_ratio': FieldMapping('current_ratio', TushareInterface.FIN_INDICATOR, '流动比率', 'float'),
            'quick_ratio': FieldMapping('quick_ratio', TushareInterface.FIN_INDICATOR, '速动比率', 'float'),
            'gross_margin': FieldMapping('gross_margin', TushareInterface.FIN_INDICATOR, '毛利率', 'float'),
            'netprofit_margin': FieldMapping('netprofit_margin', TushareInterface.FIN_INDICATOR, '净利率', 'float'),
            'op_income_to_ebt': FieldMapping('op_income_to_ebt', TushareInterface.FIN_INDICATOR, '主营业务收入与利润总额比', 'float'),
        }
        mappings.update(financial_fields)
        
        # 利润表数据 (income接口)
        income_fields = {
            'total_revenue': FieldMapping('total_revenue', TushareInterface.INCOME, '营业总收入', 'float'),
            'revenue': FieldMapping('revenue', TushareInterface.INCOME, '营业收入', 'float'),
            'operate_profit': FieldMapping('operate_profit', TushareInterface.INCOME, '营业利润', 'float'),
            'total_profit': FieldMapping('total_profit', TushareInterface.INCOME, '利润总额', 'float'),
            'n_income': FieldMapping('n_income', TushareInterface.INCOME, '净利润', 'float'),
            'net_profit': FieldMapping('n_income', TushareInterface.INCOME, '净利润', 'float'),
            'n_income_attr_p': FieldMapping('n_income_attr_p', TushareInterface.INCOME, '归属于母公司所有者的净利润', 'float'),
            'ebit': FieldMapping('ebit', TushareInterface.INCOME, 'EBIT', 'float'),
            'ebitda': FieldMapping('ebitda', TushareInterface.INCOME, 'EBITDA', 'float'),
            'operate_tax_to_ebt': FieldMapping('operate_tax_to_ebt', TushareInterface.INCOME, '经营活动税前利润', 'float'),
        }
        mappings.update(income_fields)
        
        # 资产负债表数据 (balancesheet接口)
        balance_fields = {
            'total_assets': FieldMapping('total_assets', TushareInterface.BALANCESHEET, '资产总计', 'float'),
            'total_liab': FieldMapping('total_liab', TushareInterface.BALANCESHEET, '负债合计', 'float'),
            'total_equity': FieldMapping('total_hldr_eqy_exc_min_int', TushareInterface.BALANCESHEET, '所有者权益合计', 'float'),
            'total_hldr_eqy_exc_min_int': FieldMapping('total_hldr_eqy_exc_min_int', TushareInterface.BALANCESHEET, '所有者权益合计(不含少数股东权益)', 'float'),
            'money_cap': FieldMapping('money_cap', TushareInterface.BALANCESHEET, '货币资金', 'float'),
            'inventories': FieldMapping('inventories', TushareInterface.BALANCESHEET, '存货', 'float'),
            'total_cur_assets': FieldMapping('total_cur_assets', TushareInterface.BALANCESHEET, '流动资产合计', 'float'),
            'total_cur_liab': FieldMapping('total_cur_liab', TushareInterface.BALANCESHEET, '流动负债合计', 'float'),
        }
        mappings.update(balance_fields)
        
        # 现金流量表数据 (cashflow接口)
        cashflow_fields = {
            'n_cashflow_act': FieldMapping('n_cashflow_act', TushareInterface.CASHFLOW, '经营活动产生的现金流量净额', 'float'),
            'n_cashflow_inv_act': FieldMapping('n_cashflow_inv_act', TushareInterface.CASHFLOW, '投资活动产生的现金流量净额', 'float'),
            'n_cashflow_fin_act': FieldMapping('n_cashflow_fin_act', TushareInterface.CASHFLOW, '筹资活动产生的现金流量净额', 'float'),
            'c_cash_equ_end_period': FieldMapping('c_cash_equ_end_period', TushareInterface.CASHFLOW, '期末现金及现金等价物余额', 'float'),
            'c_recp_cash_sale_goods': FieldMapping('c_recp_cash_sale_goods', TushareInterface.CASHFLOW, '销售商品、提供劳务收到的现金', 'float'),
            'c_paid_goods_s': FieldMapping('c_paid_goods_s', TushareInterface.CASHFLOW, '购买商品、接受劳务支付的现金', 'float'),
        }
        mappings.update(cashflow_fields)
        
        return mappings
    
    def _init_keyword_patterns(self) -> Dict[str, Set[str]]:
        """初始化关键字模式"""
        return {
            # 价格相关
            'price': {'price', 'close', '价格', '收盘', '股价'},
            'open': {'open', '开盘'},
            'high': {'high', '最高', '最高价'},
            'low': {'low', '最低', '最低价'},
            
            # 成交量相关
            'volume': {'volume', 'vol', '成交量', '量'},
            'amount': {'amount', '成交额', '金额'},
            'turnover': {'turnover', '换手', '换手率'},
            
            # 财务指标
            'pe': {'pe', 'pe_ttm', '市盈率'},
            'pb': {'pb', '市净率'},
            'ps': {'ps', 'ps_ttm', '市销率'},
            'roe': {'roe', 'return_on_equity', '净资产收益率'},
            'roa': {'roa', 'return_on_assets', '资产收益率'},
            'market_cap': {'market_cap', 'total_mv', '市值', '总市值'},
            
            # 利润相关
            'net_profit': {'net_profit', 'n_income', '净利润'},
            'revenue': {'revenue', 'total_revenue', '营业收入', '收入'},
            'profit': {'profit', '利润'},
            
            # 现金流相关
            'cashflow': {'cashflow', 'cash_flow', '现金流'},
            'operating_cashflow': {'n_cashflow_act', '经营性现金流', '经营活动现金流'},
            
            # 资产负债相关
            'assets': {'assets', 'total_assets', '资产', '总资产'},
            'liabilities': {'liabilities', 'total_liab', '负债'},
            'equity': {'equity', '权益', '所有者权益'},
            'debt': {'debt', '债务'},
        }
    
    def analyze_factor_code(self, factor_code: str) -> Dict[str, List[str]]:
        """
        分析因子代码，返回所需的数据字段分组
        
        Args:
            factor_code: 因子计算代码
            
        Returns:
            按接口分组的字段字典
        """
        try:
            # 提取代码中使用的变量和字段
            used_fields = self._extract_used_fields(factor_code)
            
            # 映射到Tushare字段
            tushare_fields = self._map_to_tushare_fields(used_fields)
            
            # 按接口分组
            grouped_fields = self._group_by_interface(tushare_fields)
            
            logger.info(f"因子代码分析完成，共识别出 {len(tushare_fields)} 个字段")
            return grouped_fields
            
        except Exception as e:
            logger.error(f"分析因子代码失败: {e}")
            # 返回默认的基础字段
            return {
                TushareInterface.DAILY.value: ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'amount'],
                TushareInterface.DAILY_BASIC.value: ['pe', 'pb', 'total_mv']
            }
    
    def _extract_used_fields(self, factor_code: str) -> Set[str]:
        """从因子代码中提取使用的字段"""
        used_fields = set()
        
        try:
            # 解析代码为AST
            tree = ast.parse(factor_code)
            
            # 遍历AST节点提取变量名
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_fields.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # 处理 data.field 形式
                    if isinstance(node.value, ast.Name):
                        used_fields.add(node.attr)
                elif isinstance(node, ast.Subscript):
                    # 处理 data['field'] 形式
                    if isinstance(node.slice, ast.Str):
                        used_fields.add(node.slice.s)
                    elif isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                        used_fields.add(node.slice.value)
        except:
            # 如果AST解析失败，使用正则表达式
            logger.warning("AST解析失败，使用正则表达式提取字段")
            used_fields = self._extract_fields_by_regex(factor_code)
        
        # 过滤掉Python内置函数和常见变量
        builtin_names = {
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
            'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range',
            'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip', 'pow',
            'pd', 'np', 'data', 'calculate', 'return', 'if', 'else', 'for',
            'while', 'def', 'class', 'import', 'from', 'as', 'try', 'except'
        }
        
        return used_fields - builtin_names
    
    def _extract_fields_by_regex(self, factor_code: str) -> Set[str]:
        """使用正则表达式提取字段"""
        used_fields = set()
        
        # 匹配 data['field'] 或 data["field"] 模式
        bracket_pattern = r"data\[['\"]([\w_]+)['\"]\]"
        bracket_matches = re.findall(bracket_pattern, factor_code)
        used_fields.update(bracket_matches)
        
        # 匹配 data.field 模式
        dot_pattern = r"data\.(\w+)"
        dot_matches = re.findall(dot_pattern, factor_code)
        used_fields.update(dot_matches)
        
        # 匹配常见的财务字段关键词
        for keyword_group, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in factor_code.lower():
                    used_fields.add(keyword)
        
        return used_fields
    
    def _map_to_tushare_fields(self, used_fields: Set[str]) -> List[FieldMapping]:
        """将使用的字段映射到Tushare字段"""
        tushare_fields = []
        
        # 直接映射
        for field in used_fields:
            if field in self.field_mappings:
                tushare_fields.append(self.field_mappings[field])
        
        # 关键词匹配
        for field in used_fields:
            field_lower = field.lower()
            for mapped_field, mapping in self.field_mappings.items():
                if field_lower in mapped_field.lower() or any(
                    keyword in field_lower 
                    for keyword_group in self.keyword_patterns.values() 
                    for keyword in keyword_group
                    if keyword in mapped_field.lower()
                ):
                    if mapping not in tushare_fields:
                        tushare_fields.append(mapping)
        
        # 确保包含必需字段
        required_fields = [mapping for mapping in self.field_mappings.values() if mapping.is_required]
        for required_field in required_fields:
            if required_field not in tushare_fields:
                tushare_fields.append(required_field)
        
        return tushare_fields
    
    def _group_by_interface(self, tushare_fields: List[FieldMapping]) -> Dict[str, List[str]]:
        """按接口分组字段"""
        grouped = {}
        
        for mapping in tushare_fields:
            interface_name = mapping.interface.value
            if interface_name not in grouped:
                grouped[interface_name] = ['ts_code', 'trade_date']  # 基础字段
            
            if mapping.tushare_field not in grouped[interface_name]:
                grouped[interface_name].append(mapping.tushare_field)
        
        return grouped
    
    def get_interface_description(self, interface: TushareInterface) -> str:
        """获取接口描述"""
        descriptions = {
            TushareInterface.DAILY: "股票日线数据",
            TushareInterface.DAILY_BASIC: "每日基本面数据",
            TushareInterface.INCOME: "利润表数据",
            TushareInterface.BALANCESHEET: "资产负债表数据",
            TushareInterface.CASHFLOW: "现金流量表数据",
            TushareInterface.FIN_INDICATOR: "财务指标数据",
            TushareInterface.FORECAST: "业绩预告数据",
            TushareInterface.EXPRESS: "业绩快报数据",
            TushareInterface.DIVIDEND: "分红送股数据",
            TushareInterface.TOP10_HOLDERS: "前十大股东数据",
            TushareInterface.TOP10_FLOATHOLDERS: "前十大流通股东数据",
        }
        return descriptions.get(interface, "未知接口")


# 全局实例
factor_data_analyzer = FactorDataAnalyzer()