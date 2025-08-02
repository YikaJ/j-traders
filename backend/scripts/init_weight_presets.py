#!/usr/bin/env python3
"""
权重预设初始化脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models.factor import WeightPreset
from datetime import datetime

def init_weight_presets():
    """初始化权重预设数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有预设
        existing_presets = db.query(WeightPreset).count()
        if existing_presets > 0:
            print("权重预设已存在，跳过初始化")
            return
        
        # 创建默认权重预设
        presets = [
            {
                "id": "equal_weight",
                "name": "等权重分配",
                "description": "所有因子使用相等的权重，适合因子间相关性较低的情况",
                "applicable_categories": ["trend", "momentum", "volume", "value", "volatility", "alpha101"],
                "weights": {},
                "is_default": True
            },
            {
                "id": "momentum_focused",
                "name": "动量因子优先",
                "description": "动量类因子权重较高，适合趋势跟踪策略",
                "applicable_categories": ["momentum", "trend"],
                "weights": {},
                "is_default": False
            },
            {
                "id": "value_focused",
                "name": "价值因子优先",
                "description": "价值类因子权重较高，适合价值投资策略",
                "applicable_categories": ["value", "volatility"],
                "weights": {},
                "is_default": False
            },
            {
                "id": "alpha101_balanced",
                "name": "Alpha101平衡",
                "description": "Alpha101因子与其他因子平衡分配",
                "applicable_categories": ["alpha101", "trend", "momentum"],
                "weights": {},
                "is_default": False
            },
            {
                "id": "risk_parity",
                "name": "风险平价",
                "description": "基于风险贡献相等的权重分配",
                "applicable_categories": ["trend", "momentum", "volume", "value", "volatility"],
                "weights": {},
                "is_default": False
            }
        ]
        
        # 插入预设数据
        for preset_data in presets:
            preset = WeightPreset(
                id=preset_data["id"],
                name=preset_data["name"],
                description=preset_data["description"],
                applicable_categories=preset_data["applicable_categories"],
                weights=preset_data["weights"],
                is_default=preset_data["is_default"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(preset)
        
        db.commit()
        print(f"成功初始化 {len(presets)} 个权重预设")
        
    except Exception as e:
        print(f"初始化权重预设失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_weight_presets() 