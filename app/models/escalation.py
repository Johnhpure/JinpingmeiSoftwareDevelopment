"""
任务上报模型 — Executor 向 Planner 上报新需求
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index

from app.database import Base


class Escalation(Base):
    __tablename__ = "escalation"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_agent = Column(String(36), ForeignKey("agent.id"), nullable=False, comment="上报人 Agent ID")
    source_sub_task_id = Column(String(36), ForeignKey("sub_task.id"), nullable=True, comment="来源子任务 ID")
    task_id = Column(String(36), ForeignKey("task.id"), nullable=False, comment="所属任务 ID")
    title = Column(String(200), nullable=False, comment="上报标题")
    description = Column(Text, default="", comment="需求描述")
    suggested_category = Column(String(50), default="", comment="建议的任务类别: product/ui_design/frontend/backend/database/devops")
    status = Column(String(20), default="pending", index=True, comment="状态: pending/accepted/rejected")
    reject_reason = Column(Text, default="", comment="拒绝原因")
    result_sub_task_id = Column(String(36), ForeignKey("sub_task.id"), nullable=True, comment="处理结果：创建的新子任务 ID")
    created_at = Column(DateTime, default=datetime.now, comment="上报时间")
    resolved_at = Column(DateTime, nullable=True, comment="处理时间")

    __table_args__ = (
        Index("ix_escalation_task_status", "task_id", "status"),
    )
