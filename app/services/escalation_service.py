"""
任务上报业务逻辑 — Executor 向 Planner 上报新需求
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.escalation import Escalation
from app.models.sub_task import SubTask
from app.models.task import Task
from app.models.agent import Agent


def create_escalation(
    db: Session,
    source_agent: str,
    task_id: str,
    title: str,
    description: str = "",
    suggested_category: str = "",
    source_sub_task_id: str = None,
) -> Escalation:
    """Executor 创建任务上报"""
    # 校验任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"任务 {task_id} 不存在")

    # 校验来源子任务存在（可选）
    if source_sub_task_id:
        st = db.query(SubTask).filter(SubTask.id == source_sub_task_id).first()
        if not st:
            raise ValueError(f"子任务 {source_sub_task_id} 不存在")

    escalation = Escalation(
        id=str(uuid.uuid4()),
        source_agent=source_agent,
        source_sub_task_id=source_sub_task_id,
        task_id=task_id,
        title=title,
        description=description,
        suggested_category=suggested_category,
    )
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def list_escalations(
    db: Session,
    task_id: str = None,
    status: str = None,
) -> list:
    """查询上报列表"""
    query = db.query(Escalation)
    if task_id:
        query = query.filter(Escalation.task_id == task_id)
    if status:
        query = query.filter(Escalation.status == status)
    return query.order_by(Escalation.created_at.desc()).all()


def get_escalation(db: Session, escalation_id: str) -> Escalation:
    """获取单条上报"""
    return db.query(Escalation).filter(Escalation.id == escalation_id).first()


def accept_escalation(
    db: Session,
    escalation_id: str,
    result_sub_task_id: str = None,
) -> Escalation:
    """Planner 接受上报"""
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not escalation:
        raise ValueError(f"上报 {escalation_id} 不存在")
    if escalation.status != "pending":
        raise ValueError(f"上报状态为 {escalation.status}，只有 pending 可以接受")

    escalation.status = "accepted"
    escalation.resolved_at = datetime.now()
    if result_sub_task_id:
        escalation.result_sub_task_id = result_sub_task_id
    db.commit()
    db.refresh(escalation)
    return escalation


def reject_escalation(
    db: Session,
    escalation_id: str,
    reason: str = "",
) -> Escalation:
    """Planner 拒绝上报"""
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not escalation:
        raise ValueError(f"上报 {escalation_id} 不存在")
    if escalation.status != "pending":
        raise ValueError(f"上报状态为 {escalation.status}，只有 pending 可以拒绝")

    escalation.status = "rejected"
    escalation.reject_reason = reason
    escalation.resolved_at = datetime.now()
    db.commit()
    db.refresh(escalation)
    return escalation
