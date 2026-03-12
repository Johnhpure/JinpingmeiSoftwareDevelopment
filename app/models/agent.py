"""
Agent 注册表模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Index

from app.database import Base


class Agent(Base):
    __tablename__ = "agent"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="Agent 名称")
    role = Column(String(20), nullable=False, index=True, comment="角色类型: planner/executor/reviewer/patrol")
    job_title = Column(String(100), default="", comment="业务岗位: 产品经理/UI设计师/前端开发/后端开发/数据库开发/运维工程师 等")
    specialties = Column(JSON, default=list, comment="擅长的任务类别数组: ['product','ui_design','frontend','backend','database','devops']")
    description = Column(Text, default="", comment="职责简要")
    status = Column(String(20), default="available", index=True, comment="状态: available/busy/offline")
    api_key = Column(String(64), unique=True, nullable=False, comment="API Key")
    total_score = Column(Integer, default=0, comment="累计积分")
    created_at = Column(DateTime, default=datetime.now, comment="注册时间")
