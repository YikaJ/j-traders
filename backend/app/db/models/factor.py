"""
因子数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Factor(Base):
    """因子模型"""
    __tablename__ = "factors"
    
    id = Column(Integer, primary_key=True, index=True, comment="自增ID")
    factor_id = Column(String(100), nullable=False, unique=True, index=True, comment="因子业务ID")
    name = Column(String(200), nullable=False, comment="因子名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="因子描述")
    formula = Column(Text, nullable=False, comment="Python公式代码")
    normalization_method = Column(String(50), default="z_score", comment="标准化方法")
    normalization_code = Column(Text, comment="标准化代码")
    default_parameters = Column(JSON, comment="默认参数配置")
    parameter_schema = Column(JSON, comment="参数验证schema")
    calculation_method = Column(String(50), default="custom", comment="计算方法")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_builtin = Column(Boolean, default=False, comment="是否内置因子")
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    version = Column(String(20), default="1.0.0", comment="版本号")

    def __repr__(self):
        return f"<Factor(id={self.id}, factor_id='{self.factor_id}', name='{self.name}')>"


class FactorTag(Base):
    """因子标签模型"""
    __tablename__ = "factor_tags"
    
    id = Column(Integer, primary_key=True, index=True, comment="自增ID")
    name = Column(String(100), nullable=False, unique=True, comment="标签名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="标签描述")
    color = Column(String(20), default="#3B82F6", comment="标签颜色")
    is_active = Column(Boolean, default=True, comment="是否启用")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<FactorTag(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class FactorTagRelation(Base):
    """因子标签关联表"""
    __tablename__ = "factor_tag_relations"
    
    id = Column(Integer, primary_key=True, index=True, comment="自增ID")
    factor_id = Column(String(100), nullable=False, index=True, comment="因子ID")
    tag_id = Column(Integer, nullable=False, index=True, comment="标签ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<FactorTagRelation(factor_id='{self.factor_id}', tag_id={self.tag_id})>"


class FactorHistory(Base):
    """因子历史记录"""
    __tablename__ = "factor_history"
    
    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(String(100), nullable=False, index=True, comment="因子ID")
    
    # 变更记录
    old_code = Column(Text, comment="旧代码")
    new_code = Column(Text, nullable=False, comment="新代码")
    old_description = Column(Text, comment="旧描述")
    new_description = Column(Text, comment="新描述")
    
    # 变更信息
    changed_by = Column(String(100), comment="变更人")
    change_reason = Column(Text, comment="变更原因")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="变更时间")
    
    def __repr__(self):
        return f"<FactorHistory(id={self.id}, factor_id='{self.factor_id}')>"





