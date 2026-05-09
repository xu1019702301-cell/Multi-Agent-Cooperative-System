"""
任务调度服务层 - 智能任务分配、动态调度、协同执行
采用强化学习算法优化任务分配策略
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import numpy as np

from ..models.schemas import Task, Agent, TaskStatus, TaskPriority, AgentStatus
from ..core.config import get_settings

settings = get_settings()


class TaskScheduler:
    """智能任务调度器"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.scheduler_algorithm = settings.SCHEDULER_ALGORITHM
    
    async def create_task(
        self,
        task_name: str,
        task_type: str,
        input_data: Dict[str, Any],
        required_capabilities: List[str],
        description: Optional[str] = None,
        expected_output: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: Optional[str] = None,
        dependent_tasks: Optional[List[str]] = None,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """创建新任务"""
        task = Task(
            task_id=str(uuid.uuid4()),
            task_name=task_name,
            task_type=task_type,
            input_data=input_data,
            required_capabilities=required_capabilities,
            description=description,
            expected_output=expected_output or {},
            priority=priority,
            status=TaskStatus.PENDING,
            parent_task_id=parent_task_id,
            dependent_tasks=dependent_tasks or [],
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        result = await self.db.execute(
            select(Task).where(Task.task_id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_task_by_db_id(self, db_id: int) -> Optional[Task]:
        """通过数据库 ID 获取任务"""
        result = await self.db.execute(
            select(Task).where(Task.id == db_id)
        )
        return result.scalar_one_or_none()
    
    async def assign_task(self, task_id: str, agent_id: int) -> bool:
        """分配任务给指定智能体"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # 检查依赖任务是否完成
        if task.dependent_tasks:
            for dep_task_id in task.dependent_tasks:
                dep_task = await self.get_task(dep_task_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    return False  # 依赖任务未完成
        
        # 更新任务状态
        await self.db.execute(
            update(Task)
            .where(Task.task_id == task_id)
            .values(
                assigned_agent_id=agent_id,
                status=TaskStatus.ASSIGNED,
                scheduled_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        
        return True
    
    async def select_best_agent(
        self,
        required_capabilities: List[str],
        task_priority: TaskPriority = TaskPriority.MEDIUM
    ) -> Optional[int]:
        """
        智能选择最优智能体
        支持多种调度算法：reinforcement_learning, weighted, round_robin
        """
        # 获取可用智能体
        query = select(Agent).where(
            Agent.status == AgentStatus.ONLINE,
            Agent.current_load < 80.0
        )
        
        # 过滤能力匹配的智能体
        for cap in required_capabilities:
            query = query.where(Agent.capabilities.contains([cap]))
        
        result = await self.db.execute(query)
        available_agents = result.scalars().all()
        
        if not available_agents:
            return None
        
        if self.scheduler_algorithm == "round_robin":
            # 轮询算法
            return available_agents[0].id
        
        elif self.scheduler_algorithm == "weighted":
            # 加权评分算法
            scores = []
            for agent in available_agents:
                score = self._calculate_weighted_score(agent, task_priority)
                scores.append((score, agent.id))
            
            scores.sort(reverse=True, key=lambda x: x[0])
            return scores[0][1]
        
        else:  # reinforcement_learning (默认)
            # 强化学习评分算法
            scores = []
            for agent in available_agents:
                score = self._calculate_rl_score(agent, task_priority)
                scores.append((score, agent.id))
            
            scores.sort(reverse=True, key=lambda x: x[0])
            return scores[0][1]
    
    def _calculate_weighted_score(self, agent: Agent, priority: TaskPriority) -> float:
        """加权评分算法"""
        # 负载分数（负载越低分数越高）
        load_score = (100 - agent.current_load) / 100.0
        
        # 成功率分数
        success_score = agent.success_rate / 100.0
        
        # 响应时间分数（响应越快分数越高）
        response_score = 1.0 / (1.0 + agent.avg_response_time / 1000.0)
        
        # 优先级权重
        priority_weight = priority.value / 4.0
        
        # 综合评分
        total_score = (
            load_score * 0.4 +
            success_score * 0.4 +
            response_score * 0.2
        ) * (1.0 + priority_weight * 0.5)
        
        return total_score
    
    def _calculate_rl_score(self, agent: Agent, priority: TaskPriority) -> float:
        """
        强化学习评分算法（简化版）
        实际生产中可替换为训练好的 RL 模型
        """
        base_score = self._calculate_weighted_score(agent, priority)
        
        # 历史表现奖励
        if agent.success_rate > 95.0:
            base_score *= 1.2
        elif agent.success_rate > 90.0:
            base_score *= 1.1
        
        # 低负载奖励
        if agent.current_load < 30.0:
            base_score *= 1.15
        elif agent.current_load < 50.0:
            base_score *= 1.05
        
        # 快速响应奖励
        if agent.avg_response_time < 100.0:
            base_score *= 1.1
        
        return base_score
    
    async def auto_assign_pending_tasks(self) -> int:
        """自动分配所有待处理任务"""
        query = select(Task).where(Task.status == TaskStatus.PENDING)
        result = await self.db.execute(query)
        pending_tasks = result.scalars().all()
        
        assigned_count = 0
        for task in pending_tasks:
            # 检查依赖
            if task.dependent_tasks:
                all_completed = True
                for dep_id in task.dependent_tasks:
                    dep_task = await self.get_task(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        all_completed = False
                        break
                
                if not all_completed:
                    continue
            
            # 选择最优智能体
            required_caps = task.metadata.get("required_capabilities", [])
            agent_id = await self.select_best_agent(required_caps, task.priority)
            
            if agent_id:
                await self.assign_task(task.task_id, agent_id)
                assigned_count += 1
        
        return assigned_count
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """更新任务状态"""
        update_data = {"status": status}
        
        if progress is not None:
            update_data["progress"] = progress
        
        if result is not None:
            update_data["result"] = result
        
        if error_message is not None:
            update_data["error_message"] = error_message
        
        if status == TaskStatus.EXECUTING and not hasattr(update_data, 'started_at'):
            update_data["started_at"] = datetime.now(timezone.utc)
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            update_data["completed_at"] = datetime.now(timezone.utc)
        
        await self.db.execute(
            update(Task)
            .where(Task.task_id == task_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return await self.get_task(task_id)
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """重试失败任务"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        if task.status != TaskStatus.FAILED:
            return False
        
        if task.retry_count >= task.max_retries:
            return False  # 已达最大重试次数
        
        # 重新分配任务
        required_caps = task.metadata.get("required_capabilities", [])
        agent_id = await self.select_best_agent(required_caps, task.priority)
        
        if agent_id:
            await self.db.execute(
                update(Task)
                .where(Task.task_id == task_id)
                .values(
                    status=TaskStatus.ASSIGNED,
                    assigned_agent_id=agent_id,
                    retry_count=task.retry_count + 1,
                    error_message=None
                )
            )
            await self.db.commit()
            return True
        
        return False
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        # 各状态任务数量
        status_counts = {}
        for status in TaskStatus:
            result = await self.db.execute(
                select(Task).where(Task.status == status)
            )
            status_counts[status.value] = len(result.scalars().all())
        
        # 平均完成时间
        completed_tasks_result = await self.db.execute(
            select(Task).where(Task.status == TaskStatus.COMPLETED)
        )
        completed_tasks = completed_tasks_result.scalars().all()
        
        avg_completion_time = 0.0
        if completed_tasks:
            completion_times = []
            for task in completed_tasks:
                if task.started_at and task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    completion_times.append(duration)
            
            if completion_times:
                avg_completion_time = np.mean(completion_times)
        
        return {
            "total_tasks": sum(status_counts.values()),
            "status_distribution": status_counts,
            "avg_completion_time_seconds": avg_completion_time,
            "success_rate": (
                status_counts.get("completed", 0) / 
                max(1, sum(status_counts.values())) * 100
            )
        }
