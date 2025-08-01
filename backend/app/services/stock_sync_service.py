"""
股票数据同步服务
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.db.database import get_db
from app.db.models.stock import Stock
from app.services.tushare_service import tushare_service

logger = logging.getLogger(__name__)


class StockSyncService:
    """股票数据同步服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 从配置中获取调试模式
        from app.core.config import settings
        self.debug_mode = settings.DEBUG
    
    async def sync_stock_list(self, db: Session) -> Dict[str, Any]:
        """
        同步股票列表数据
        
        Returns:
            Dict: 同步结果统计
        """
        try:
            self.logger.info("开始同步股票列表数据...")
            
            # 从Tushare获取股票列表
            stock_df = await tushare_service.get_stock_list()
            
            if stock_df is None or stock_df.empty:
                self.logger.error("未获取到股票数据")
                raise ValueError("无法从Tushare获取股票数据")
            
            # 统计信息
            stats = {
                "total_fetched": len(stock_df),
                "new_stocks": 0,
                "updated_stocks": 0,
                "errors": 0,
                "start_time": datetime.now(),
                "end_time": None
            }
            
            # 批量处理股票数据
            for _, row in stock_df.iterrows():
                try:
                    await self._process_stock_record(db, row, stats)
                except Exception as e:
                    self.logger.error(f"处理股票记录失败 {row.get('ts_code', 'Unknown')}: {e}")
                    stats["errors"] += 1
            
            # 提交事务
            db.commit()
            
            stats["end_time"] = datetime.now()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            
            self.logger.info(f"股票列表同步完成: {stats}")
            return stats
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"股票列表同步失败: {e}")
            raise e
    
    async def _process_stock_record(self, db: Session, row: Any, stats: Dict[str, Any]):
        """处理单个股票记录"""
        symbol = row.get('ts_code', '')
        if not symbol:
            return
        
        # 检查股票是否已存在
        existing_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        
        if existing_stock:
            # 更新现有股票信息
            self._update_stock_info(existing_stock, row)
            stats["updated_stocks"] += 1
            self.logger.debug(f"更新股票: {symbol} - {row.get('name', '')}")
        else:
            # 创建新股票记录
            new_stock = self._create_stock_record(row)
            db.add(new_stock)
            stats["new_stocks"] += 1
            self.logger.debug(f"新增股票: {symbol} - {row.get('name', '')}")
    
    def _create_stock_record(self, row: Any) -> Stock:
        """创建股票记录"""
        symbol = row.get('ts_code', '')
        market = symbol.split('.')[1] if '.' in symbol else ''
        
        return Stock(
            symbol=symbol,
            name=row.get('name', ''),
            industry=row.get('industry', ''),
            area=row.get('area', ''),
            market=market,
            list_date=row.get('list_date', ''),
            list_status=row.get('list_status', 'L'),
            total_share=row.get('total_share'),
            float_share=row.get('float_share'),
            is_active=row.get('list_status', 'L') == 'L'
        )
    
    def _update_stock_info(self, stock: Stock, row: Any):
        """更新股票信息"""
        stock.name = row.get('name', stock.name)
        stock.industry = row.get('industry', stock.industry)
        stock.area = row.get('area', stock.area)
        stock.list_status = row.get('list_status', stock.list_status)
        stock.total_share = row.get('total_share', stock.total_share)
        stock.float_share = row.get('float_share', stock.float_share)
        stock.is_active = row.get('list_status', 'L') == 'L'
    

    
    async def get_stock_count(self, db: Session) -> Dict[str, int]:
        """获取股票数量统计"""
        try:
            total_count = db.query(Stock).count()
            active_count = db.query(Stock).filter(Stock.is_active == True).count()
            
            # 按市场统计
            sz_count = db.query(Stock).filter(Stock.market == 'SZ').count()
            sh_count = db.query(Stock).filter(Stock.market == 'SH').count()
            
            return {
                "total": total_count,
                "active": active_count,
                "sz_market": sz_count,
                "sh_market": sh_count
            }
        except Exception as e:
            self.logger.error(f"获取股票统计失败: {e}")
            return {"total": 0, "active": 0, "sz_market": 0, "sh_market": 0}
    
    async def search_stocks(self, db: Session, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            if not keyword:
                return []
            
            # 构建搜索查询
            query = db.query(Stock).filter(
                Stock.is_active == True
            ).filter(
                (Stock.symbol.like(f'%{keyword}%')) |
                (Stock.name.like(f'%{keyword}%'))
            ).limit(limit)
            
            stocks = query.all()
            
            result = []
            for stock in stocks:
                result.append({
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "industry": stock.industry,
                    "area": stock.area,
                    "market": stock.market,
                    "list_date": stock.list_date
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"搜索股票失败: {e}")
            return []
    
    async def get_last_sync_info(self, db: Session) -> Dict[str, Any]:
        """获取最后同步信息"""
        try:
            self.logger.info("开始获取同步信息...")
            
            # 查询最新的股票记录创建时间
            result = db.execute(text("SELECT MAX(updated_at) as last_update FROM stocks")).fetchone()
            last_update = result[0] if result and result[0] else None
            
            self.logger.info(f"数据库查询结果: {result}")
            self.logger.info(f"last_update 类型: {type(last_update)}, 值: {last_update}")
            
            stock_count = await self.get_stock_count(db)
            self.logger.info(f"股票统计: {stock_count}")
            
            # 处理 last_update 的格式
            if last_update:
                if isinstance(last_update, str):
                    # 如果是字符串，直接返回
                    last_sync_time = last_update
                    self.logger.info(f"last_update 是字符串，直接使用: {last_sync_time}")
                else:
                    # 如果是 datetime 对象，转换为 ISO 格式
                    last_sync_time = last_update.isoformat()
                    self.logger.info(f"last_update 是 datetime，转换为 ISO: {last_sync_time}")
            else:
                last_sync_time = None
                self.logger.warning("last_update 为空")
            
            result_data = {
                "last_sync_time": last_sync_time,
                "stock_count": stock_count,
                "sync_available": True
            }
            
            self.logger.info(f"返回同步信息: {result_data}")
            return result_data
            
        except Exception as e:
            self.logger.error(f"获取同步信息失败: {e}", exc_info=True)
            # 在开发环境下，重新抛出异常以便调试
            if hasattr(self, 'debug_mode') and self.debug_mode:
                raise
            return {
                "last_sync_time": None,
                "stock_count": {"total": 0, "active": 0, "sz_market": 0, "sh_market": 0},
                "sync_available": False
            }


# 创建全局实例
stock_sync_service = StockSyncService()