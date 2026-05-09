"""
多智能体协同作业平台 - 核心数据模型
支持智能体注册、任务管理、协同执行全流程
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class AgentStatus(enum.Enum):
    """智能体状态枚举"""
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class TaskStatus(enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Agent(Base):
    """智能体注册信息表"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(64), unique=True, index=True, nullable=False)
    agent_name = Column(String(128), nullable=False)
    agent_type = Column(String(64), nullable=False)  # 智能体类型
    description = Column(Text)
    version = Column(String(32), default="1.0.0")
    
    # 能力标签
    capabilities = Column(JSON, default=list)  # ["data_analysis", "image_processing", ...]
    
    # 状态信息
    status = Column(Enum(AgentStatus), default=AgentStatus.OFFLINE)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())
    
    # 连接信息
    endpoint_url = Column(String(256))
    auth_token = Column(String(256))
    
    # 性能指标
    max_concurrent_tasks = Column(Integer, default=1)
    current_load = Column(Float, default=0.0)  # 0-100
    success_rate = Column(Float, default=100.0)
    avg_response_time = Column(Float, default=0.0)  # 毫秒
    
    # 元数据
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    tasks = relationship("Task", back_populates="agent")
    execution_logs = relationship("ExecutionLog", back_populates="agent")


class Task(Base):
    """任务信息表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    task_name = Column(String(128), nullable=False)
    task_type = Column(String(64), nullable=False)
    description = Column(Text)
    
    # 任务参数
    input_data = Column(JSON, default=dict)
    expected_output = Column(JSON, default=dict)
    
    # 调度信息
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    
    # 协同信息
    parent_task_id = Column(String(64), index=True)  # 父任务 ID（用于任务分解）
    sub_tasks = Column(JSON, default=list)  # 子任务列表
    dependent_tasks = Column(JSON, default=list)  # 依赖任务列表
    
    # 执行信息
    progress = Column(Float, default=0.0)  # 0-100
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 时间信息
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 结果信息
    result = Column(JSON, default=dict)
    error_message = Column(Text)
    
    # 校验信息
    validation_status = Column(Boolean, default=False)
    validation_result = Column(JSON, default=dict)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    agent = relationship("Agent", back_populates="tasks")
    execution_logs = relationship("ExecutionLog", back_populates="task")


class ExecutionLog(Base):
    """执行日志表 - 全流程追踪"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(64), unique=True, index=True, nullable=False)
    
    # 关联信息
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    
    # 日志内容
    log_level = Column(String(16), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    context = Column(JSON, default=dict)
    
    # 时间信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 关联关系
    task = relationship("Task", back_populates="execution_logs")
    agent = relationship("Agent", back_populates="execution_logs")


class CollaborationSession(Base):
    """协同会话表 - 多智能体协同上下文"""
    __tablename__ = "collaboration_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    session_name = Column(String(128), nullable=False)
    
    # 参与智能体
    participant_agents = Column(JSON, default=list)  # [agent_id1, agent_id2, ...]
    
    # 会话状态
    status = Column(String(32), default="active")  # active, paused, completed, terminated
    
    # 共享上下文
    shared_context = Column(JSON, default=dict)
    message_history = Column(JSON, default=list)
    
    # 协同任务
    related_tasks = Column(JSON, default=list)
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    
    # 元数据
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemMetrics(Base):
    """系统监控指标表"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(64), index=True, nullable=False)
    metric_type = Column(String(32), nullable=False)  # gauge, counter, histogram
    
    # 指标值
    value = Column(Float, nullable=False)
    labels = Column(JSON, default=dict)  # 标签维度
    
    # 时间信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 元数据
    metadata = Column(JSON, default=dict)
