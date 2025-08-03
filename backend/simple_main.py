"""
简化的FastAPI应用 - 只包含数据字段API
用于测试数据字段查看功能
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


# 数据模型定义
class DataFieldCategory(str, Enum):
    """数据字段分类"""
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    DERIVED = "derived"


class DataFieldType(str, Enum):
    """数据字段类型"""
    NUMERIC = "numeric"
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"


class DataField(BaseModel):
    """数据字段定义"""
    field_id: str
    field_name: str
    display_name: str
    description: str
    category: DataFieldCategory
    field_type: DataFieldType
    unit: Optional[str] = None
    is_required: bool = False
    is_common: bool = True
    tushare_field: Optional[str] = None
    example_value: Optional[str] = None
    validation_rules: Optional[dict] = None


class DataFieldConfig(BaseModel):
    """数据字段配置"""
    category: DataFieldCategory
    fields: List[DataField]
    description: str


class FactorInputFieldsResponse(BaseModel):
    """因子输入字段响应"""
    categories: List[DataFieldConfig]
    total_fields: int


# 创建FastAPI应用
app = FastAPI(
    title="数据字段API",
    description="因子公式数据字段查看API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 模拟数据
MOCK_DATA_FIELDS = {
    DataFieldCategory.PRICE: [
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
    ],
    DataFieldCategory.VOLUME: [
        DataField(
            field_id="vol",
            field_name="vol",
            display_name="成交量",
            description="当日成交量",
            category=DataFieldCategory.VOLUME,
            field_type=DataFieldType.NUMERIC,
            unit="手",
            is_required=False,
            is_common=True,
            tushare_field="vol",
            example_value="12345",
            validation_rules={"min": 0}
        ),
        DataField(
            field_id="amount",
            field_name="amount",
            display_name="成交额",
            description="当日成交金额",
            category=DataFieldCategory.VOLUME,
            field_type=DataFieldType.NUMERIC,
            unit="千元",
            is_required=False,
            is_common=True,
            tushare_field="amount",
            example_value="1234567",
            validation_rules={"min": 0}
        ),
    ],
    DataFieldCategory.TECHNICAL: [
        DataField(
            field_id="ma5",
            field_name="ma5",
            display_name="5日均线",
            description="5日移动平均线",
            category=DataFieldCategory.TECHNICAL,
            field_type=DataFieldType.NUMERIC,
            unit="元",
            is_required=False,
            is_common=True,
            tushare_field=None,
            example_value="12.50",
            validation_rules={"min": 0}
        ),
        DataField(
            field_id="ma20",
            field_name="ma20",
            display_name="20日均线",
            description="20日移动平均线",
            category=DataFieldCategory.TECHNICAL,
            field_type=DataFieldType.NUMERIC,
            unit="元",
            is_required=False,
            is_common=True,
            tushare_field=None,
            example_value="12.80",
            validation_rules={"min": 0}
        ),
    ],
    DataFieldCategory.FUNDAMENTAL: [
        DataField(
            field_id="pe",
            field_name="pe",
            display_name="市盈率",
            description="市盈率TTM",
            category=DataFieldCategory.FUNDAMENTAL,
            field_type=DataFieldType.NUMERIC,
            unit="倍",
            is_required=False,
            is_common=True,
            tushare_field="pe_ttm",
            example_value="15.5",
            validation_rules={"min": 0}
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
            example_value="1.8",
            validation_rules={"min": 0}
        ),
    ]
}


# API端点
@app.get("/")
async def root():
    """根路径"""
    return {"message": "数据字段API服务正在运行", "version": "1.0.0"}


@app.get("/api/v1/test")
async def test_endpoint():
    """测试接口"""
    return {"message": "API工作正常", "version": "1.0.0"}


@app.get("/api/v1/data/fields", response_model=FactorInputFieldsResponse)
async def get_factor_input_fields(
    categories: Optional[List[DataFieldCategory]] = Query(None, description="数据字段分类筛选"),
    include_common_only: bool = Query(True, description="是否只包含常用字段")
):
    """
    获取因子输入字段配置
    """
    try:
        # 筛选分类
        if categories:
            selected_categories = categories
        else:
            selected_categories = list(DataFieldCategory)
        
        # 构建响应数据
        category_configs = []
        total_fields = 0
        
        for category in selected_categories:
            if category in MOCK_DATA_FIELDS:
                fields = MOCK_DATA_FIELDS[category]
                
                # 根据是否只显示常用字段进行筛选
                if include_common_only:
                    fields = [f for f in fields if f.is_common]
                
                if fields:  # 只有当有字段时才添加分类
                    category_config = DataFieldConfig(
                        category=category,
                        fields=fields,
                        description=get_category_description(category)
                    )
                    category_configs.append(category_config)
                    total_fields += len(fields)
        
        return FactorInputFieldsResponse(
            categories=category_configs,
            total_fields=total_fields
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/data/fields/common", response_model=List[DataField])
async def get_common_fields():
    """
    获取常用数据字段列表
    """
    try:
        common_fields = []
        for fields in MOCK_DATA_FIELDS.values():
            common_fields.extend([f for f in fields if f.is_common])
        return common_fields
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/data/fields/{field_id}", response_model=DataField)
async def get_field_by_id(field_id: str):
    """
    根据字段ID获取字段详细信息
    """
    try:
        # 搜索所有分类中的字段
        for fields in MOCK_DATA_FIELDS.values():
            for field in fields:
                if field.field_id == field_id:
                    return field
        
        raise HTTPException(status_code=404, detail=f"字段 {field_id} 未找到")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/data/fields/validate")
async def validate_field_combination(field_ids: List[str]):
    """
    验证字段组合的有效性
    """
    try:
        validation_result = {"status": "valid", "message": ""}
        
        # 检查字段是否存在
        all_fields = []
        for fields in MOCK_DATA_FIELDS.values():
            all_fields.extend(fields)
        
        all_field_ids = [f.field_id for f in all_fields]
        invalid_fields = [fid for fid in field_ids if fid not in all_field_ids]
        
        if invalid_fields:
            validation_result["status"] = "error"
            validation_result["message"] = f"无效字段: {', '.join(invalid_fields)}"
        
        # 检查是否包含必需字段
        required_fields = [f.field_id for f in all_fields if f.is_required]
        missing_required = [f for f in required_fields if f not in field_ids]
        
        if missing_required:
            validation_result["status"] = "warning"
            validation_result["message"] = f"缺少必需字段: {', '.join(missing_required)}"
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_category_description(category: DataFieldCategory) -> str:
    """获取分类描述"""
    descriptions = {
        DataFieldCategory.PRICE: "价格相关的基础数据字段，包括开盘价、收盘价、最高价、最低价等",
        DataFieldCategory.VOLUME: "成交量相关的数据字段，包括成交量、成交额等",
        DataFieldCategory.TECHNICAL: "技术指标相关的数据字段，包括移动平均线、技术指标等",
        DataFieldCategory.FUNDAMENTAL: "基本面数据字段，包括财务指标、估值指标等",
        DataFieldCategory.DERIVED: "衍生计算字段，基于基础数据计算得出的字段"
    }
    return descriptions.get(category, "")


if __name__ == "__main__":
    print("启动服务器...")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")