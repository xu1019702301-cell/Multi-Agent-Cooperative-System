"""
智能体服务层 - 管理智能体注册、状态监控、能力发现
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ..models.schemas import Agent, AgentStatus
from ..core.config import get_settings

settings = get_settings()


class AgentService:
    """智能体服务类"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: List[str],
        endpoint_url: str,
        auth_token: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        max_concurrent_tasks: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """注册新智能体"""
        agent = Agent(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            capabilities=capabilities,
            endpoint_url=endpoint_url,
            auth_token=auth_token,
            description=description,
            version=version,
            max_concurrent_tasks=max_concurrent_tasks,
            status=AgentStatus.ONLINE,
            last_heartbeat=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        
        return agent
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取智能体信息"""
        result = await self.db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()
    
    async def get_agent_by_db_id(self, db_id: int) -> Optional[Agent]:
        """通过数据库 ID 获取智能体"""
        result = await self.db.execute(
            select(Agent).where(Agent.id == db_id)
        )
        return result.scalar_one_or_none()
    
    async def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Agent]:
        """查询智能体列表（支持多条件过滤）"""
        query = select(Agent)
        
        if status:
            query = query.where(Agent.status == status)
        if agent_type:
            query = query.where(Agent.agent_type == agent_type)
        if capabilities:
            # 查询包含所有指定能力的智能体
            for cap in capabilities:
                query = query.where(Agent.capabilities.contains([cap]))
        
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        current_load: Optional[float] = None,
        success_rate: Optional[float] = None,
        avg_response_time: Optional[float] = None
    ) -> Optional[Agent]:
        """更新智能体状态"""
        update_data = {
            "status": status,
            "last_heartbeat": datetime.now(timezone.utc)
        }
        
        if current_load is not None:
            update_data["current_load"] = current_load
        if success_rate is not None:
            update_data["success_rate"] = success_rate
        if avg_response_time is not None:
            update_data["avg_response_time"] = avg_response_time
        
        await self.db.execute(
            update(Agent)
            .where(Agent.agent_id == agent_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return await self.get_agent(agent_id)
    
    async def heartbeat(self, agent_id: str, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """智能体心跳上报"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        update_data = {
            "last_heartbeat": datetime.now(timezone.utc),
            "status": AgentStatus.ONLINE
        }
        
        if metrics:
            if "current_load" in metrics:
                update_data["current_load"] = metrics["current_load"]
            if "success_rate" in metrics:
                update_data["success_rate"] = metrics["success_rate"]
            if "avg_response_time" in metrics:
                update_data["avg_response_time"] = metrics["avg_response_time"]
        
        await self.db.execute(
            update(Agent)
            .where(Agent.agent_id == agent_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        await self.db.delete(agent)
        await self.db.commit()
        
        return True
    
    async def get_available_agents(
        self,
        required_capabilities: Optional[List[str]] = None,
        max_load: float = 80.0
    ) -> List[Agent]:
        """获取可用智能体（在线且负载低于阈值）"""
        query = select(Agent).where(
            Agent.status == AgentStatus.ONLINE,
            Agent.current_load < max_load
        )
        
        if required_capabilities:
            for cap in required_capabilities:
                query = query.where(Agent.capabilities.contains([cap]))
        
        # 按负载升序排序，优先选择负载低的智能体
        query = query.order_by(Agent.current_load.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def detect_offline_agents(self, timeout_seconds: int = None) -> List[Agent]:
        """检测超时离线的智能体"""
        if timeout_seconds is None:
            timeout_seconds = settings.AGENT_HEARTBEAT_INTERVAL * 3
        
        from sqlalchemy import and_
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        
        query = select(Agent).where(
            and_(
                Agent.status != AgentStatus.OFFLINE,
                Agent.last_heartbeat < cutoff_time
            )
        )
        
        result = await self.db.execute(query)
        offline_agents = result.scalars().all()
        
        # 批量更新状态为 OFFLINE
        for agent in offline_agents:
            agent.status = AgentStatus.OFFLINE
        
        if offline_agents:
            await self.db.commit()
        
        return offline_agents
