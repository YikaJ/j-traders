"""
数据字段配置相关的模式定义
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class DataFieldCategory(str, Enum):
    """数据字段分类"""
    PRICE = "price"           # 价格类数据
    VOLUME = "volume"         # 成交量类数据
    TECHNICAL = "technical"   # 技术指标类数据
    FUNDAMENTAL = "fundamental"  # 基本面数据
    DERIVED = "derived"       # 衍生数据


class DataFieldType(str, Enum):
    """数据字段类型"""
    NUMERIC = "numeric"       # 数值型
    STRING = "string"         # 字符串型
    DATE = "date"            # 日期型
    BOOLEAN = "boolean"      # 布尔型


class DataField(BaseModel):
    """数据字段定义"""
    field_id: str                    # 字段ID
    field_name: str                  # 字段名称
    display_name: str                # 显示名称
    description: str                 # 字段描述
    category: DataFieldCategory      # 字段分类
    field_type: DataFieldType        # 字段类型
    unit: Optional[str] = None       # 单位
    is_required: bool = False        # 是否必需
    is_common: bool = True           # 是否常用
    tushare_field: Optional[str] = None  # 对应的Tushare字段名
    example_value: Optional[str] = None  # 示例值
    validation_rules: Optional[Dict[str, Any]] = None  # 验证规则
    

class DataFieldConfig(BaseModel):
    """数据字段配置"""
    category: DataFieldCategory
    fields: List[DataField]
    description: str


class FactorInputFieldsRequest(BaseModel):
    """因子输入字段请求"""
    categories: Optional[List[DataFieldCategory]] = None
    include_common_only: bool = True


class FactorInputFieldsResponse(BaseModel):
    """因子输入字段响应"""
    categories: List[DataFieldConfig]
    total_fields: int