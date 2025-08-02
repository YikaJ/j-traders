"""
数据字段配置服务
基于Tushare标准字段提供因子输入字段配置
"""

from typing import List, Dict, Optional
import logging

from app.schemas.data_fields import (
    DataField, DataFieldConfig, DataFieldCategory, DataFieldType,
    FactorInputFieldsRequest, FactorInputFieldsResponse
)
from app.config.tushare_config import ALPHA101_REQUIRED_FIELDS, TUSHARE_FIELD_MAPPING

logger = logging.getLogger(__name__)


class DataFieldService:
    """数据字段配置服务"""
    
    def __init__(self):
        self._field_configs = self._initialize_field_configs()
    
    def _initialize_field_configs(self) -> List[DataFieldConfig]:
        """初始化数据字段配置"""
        
        # 价格类数据字段
        price_fields = [
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
                example_value="12.45",
                validation_rules={"min": 0, "max": 10000}
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
                example_value="12.89",
                validation_rules={"min": 0, "max": 10000}
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
                example_value="12.01",
                validation_rules={"min": 0, "max": 10000}
            ),
            DataField(
                field_id="close",
                field_name="close",
                display_name="收盘价",
                description="当日收盘价格",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=True,
                is_common=True,
                tushare_field="close",
                example_value="12.34",
                validation_rules={"min": 0, "max": 10000}
            ),
            DataField(
                field_id="pre_close",
                field_name="pre_close",
                display_name="前收盘价",
                description="前一交易日收盘价",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="pre_close",
                example_value="12.10",
                validation_rules={"min": 0, "max": 10000}
            ),
            DataField(
                field_id="adj_close",
                field_name="adj_close",
                display_name="复权收盘价",
                description="前复权调整后的收盘价",
                category=DataFieldCategory.PRICE,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=False,
                tushare_field="close",  # 需要结合复权因子计算
                example_value="45.67",
                validation_rules={"min": 0, "max": 50000}
            )
        ]
        
        # 成交量类数据字段
        volume_fields = [
            DataField(
                field_id="volume",
                field_name="volume",
                display_name="成交量",
                description="当日成交量（股）",
                category=DataFieldCategory.VOLUME,
                field_type=DataFieldType.NUMERIC,
                unit="股",
                is_required=False,
                is_common=True,
                tushare_field="vol",
                example_value="1234567",
                validation_rules={"min": 0}
            ),
            DataField(
                field_id="amount",
                field_name="amount",
                display_name="成交额",
                description="当日成交金额（千元）",
                category=DataFieldCategory.VOLUME,
                field_type=DataFieldType.NUMERIC,
                unit="千元",
                is_required=False,
                is_common=True,
                tushare_field="amount",
                example_value="15234.56",
                validation_rules={"min": 0}
            ),
            DataField(
                field_id="turnover_rate",
                field_name="turnover_rate",
                display_name="换手率",
                description="成交量占流通股本的比例",
                category=DataFieldCategory.VOLUME,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=False,
                tushare_field="turnover_rate",
                example_value="2.34",
                validation_rules={"min": 0, "max": 100}
            )
        ]
        
        # 技术指标类数据字段
        technical_fields = [
            DataField(
                field_id="change",
                field_name="change",
                display_name="涨跌额",
                description="相对前收盘价的涨跌金额",
                category=DataFieldCategory.TECHNICAL,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=True,
                tushare_field="change",
                example_value="0.24",
                validation_rules={"min": -1000, "max": 1000}
            ),
            DataField(
                field_id="pct_change",
                field_name="pct_change",
                display_name="涨跌幅",
                description="相对前收盘价的涨跌幅",
                category=DataFieldCategory.TECHNICAL,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=True,
                tushare_field="pct_chg",
                example_value="1.98",
                validation_rules={"min": -20, "max": 20}
            ),
            DataField(
                field_id="vwap",
                field_name="vwap",
                display_name="成交量加权平均价",
                description="Volume Weighted Average Price",
                category=DataFieldCategory.TECHNICAL,
                field_type=DataFieldType.NUMERIC,
                unit="元",
                is_required=False,
                is_common=False,
                tushare_field=None,  # 需要计算
                example_value="12.23",
                validation_rules={"min": 0, "max": 10000}
            )
        ]
        
        # 基本面数据字段
        fundamental_fields = [
            DataField(
                field_id="pe_ratio",
                field_name="pe_ratio",
                display_name="市盈率",
                description="Price to Earnings Ratio",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="倍",
                is_required=False,
                is_common=False,
                tushare_field="pe",
                example_value="15.6",
                validation_rules={"min": 0, "max": 1000}
            ),
            DataField(
                field_id="pb_ratio",
                field_name="pb_ratio",
                display_name="市净率",
                description="Price to Book Ratio",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="倍",
                is_required=False,
                is_common=False,
                tushare_field="pb",
                example_value="2.1",
                validation_rules={"min": 0, "max": 100}
            ),
            DataField(
                field_id="total_mv",
                field_name="total_mv",
                display_name="总市值",
                description="股票总市值",
                category=DataFieldCategory.FUNDAMENTAL,
                field_type=DataFieldType.NUMERIC,
                unit="万元",
                is_required=False,
                is_common=False,
                tushare_field="total_mv",
                example_value="123456789",
                validation_rules={"min": 0}
            )
        ]
        
        # 衍生数据字段
        derived_fields = [
            DataField(
                field_id="returns",
                field_name="returns",
                display_name="收益率",
                description="基于收盘价计算的收益率",
                category=DataFieldCategory.DERIVED,
                field_type=DataFieldType.NUMERIC,
                unit="%",
                is_required=False,
                is_common=True,
                tushare_field=None,  # 需要计算
                example_value="0.0198",
                validation_rules={"min": -1, "max": 1}
            ),
            DataField(
                field_id="log_returns",
                field_name="log_returns",
                display_name="对数收益率",
                description="基于收盘价计算的对数收益率",
                category=DataFieldCategory.DERIVED,
                field_type=DataFieldType.NUMERIC,
                unit="",
                is_required=False,
                is_common=False,
                tushare_field=None,  # 需要计算
                example_value="0.0196",
                validation_rules={"min": -10, "max": 10}
            ),
            DataField(
                field_id="volatility",
                field_name="volatility",
                display_name="波动率",
                description="价格波动率指标",
                category=DataFieldCategory.DERIVED,
                field_type=DataFieldType.NUMERIC,
                unit="",
                is_required=False,
                is_common=False,
                tushare_field=None,  # 需要计算
                example_value="0.25",
                validation_rules={"min": 0, "max": 5}
            )
        ]
        
        return [
            DataFieldConfig(
                category=DataFieldCategory.PRICE,
                fields=price_fields,
                description="股票价格相关数据字段"
            ),
            DataFieldConfig(
                category=DataFieldCategory.VOLUME,
                fields=volume_fields,
                description="成交量和成交额相关数据字段"
            ),
            DataFieldConfig(
                category=DataFieldCategory.TECHNICAL,
                fields=technical_fields,
                description="技术指标相关数据字段"
            ),
            DataFieldConfig(
                category=DataFieldCategory.FUNDAMENTAL,
                fields=fundamental_fields,
                description="基本面分析相关数据字段"
            ),
            DataFieldConfig(
                category=DataFieldCategory.DERIVED,
                fields=derived_fields,
                description="基于基础数据计算的衍生字段"
            )
        ]
    
    def get_available_fields(self, request: FactorInputFieldsRequest) -> FactorInputFieldsResponse:
        """获取可用的数据字段配置"""
        try:
            # 筛选字段配置
            filtered_configs = []
            total_fields = 0
            
            for config in self._field_configs:
                # 按分类筛选
                if request.categories and config.category not in request.categories:
                    continue
                
                # 按常用性筛选
                fields = config.fields
                if request.include_common_only:
                    fields = [f for f in fields if f.is_common]
                
                if fields:  # 只包含有字段的配置
                    filtered_config = DataFieldConfig(
                        category=config.category,
                        fields=fields,
                        description=config.description
                    )
                    filtered_configs.append(filtered_config)
                    total_fields += len(fields)
            
            return FactorInputFieldsResponse(
                categories=filtered_configs,
                total_fields=total_fields
            )
            
        except Exception as e:
            logger.error(f"获取数据字段配置失败: {e}")
            raise
    
    def get_field_by_id(self, field_id: str) -> Optional[DataField]:
        """根据字段ID获取字段信息"""
        for config in self._field_configs:
            for field in config.fields:
                if field.field_id == field_id:
                    return field
        return None
    
    def get_common_fields(self) -> List[DataField]:
        """获取常用字段列表"""
        common_fields = []
        for config in self._field_configs:
            common_fields.extend([f for f in config.fields if f.is_common])
        return common_fields
    
    def validate_field_combination(self, field_ids: List[str]) -> Dict[str, str]:
        """验证字段组合的有效性"""
        validation_result = {"status": "valid", "message": ""}
        
        # 检查是否包含必需字段
        required_fields = [f.field_id for config in self._field_configs 
                          for f in config.fields if f.is_required]
        
        missing_required = [f for f in required_fields if f not in field_ids]
        if missing_required:
            validation_result["status"] = "warning"
            validation_result["message"] = f"缺少必需字段: {', '.join(missing_required)}"
        
        # 检查字段是否存在
        invalid_fields = []
        for field_id in field_ids:
            if not self.get_field_by_id(field_id):
                invalid_fields.append(field_id)
        
        if invalid_fields:
            validation_result["status"] = "error"
            validation_result["message"] = f"无效字段: {', '.join(invalid_fields)}"
        
        return validation_result


# 全局实例
data_field_service = DataFieldService()