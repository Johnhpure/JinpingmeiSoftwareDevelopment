"""
任务上报路由 — Executor 向 Planner 上报需求
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime as dt

from app.database import get_db
from app.auth.dependencies import get_current_agent, require_role
from app.services import escalation_service
from app.models.agent import Agent


router = APIRouter(prefix="/escalations", tags=["Escalation"])


# ============================================================
# 请求/响应模型
# ============================================================

class EscalationCreateRequest(BaseModel):
    task_id: str = Field(..., description="所属任务 ID")
    title: str = Field(..., description="上报标题")
    description: str = Field("", description="需求描述")
    suggested_category: str = Field("", description="建议的任务类别: product/ui_design/frontend/backend/database/devops")
    source_sub_task_id: Optional[str] = Field(None, description="来源子任务 ID（可选）")


class EscalationResponse(BaseModel):
    id: str
    source_agent: str
    source_sub_task_id: Optional[str]
    task_id: str
    title: str
    description: str
    suggested_category: str
    status: str
    reject_reason: str
    result_sub_task_id: Optional[str]
    created_at: Optional[dt] = None
    resolved_at: Optional[dt] = None

    class Config:
        from_attributes = True


class AcceptRequest(BaseModel):
    result_sub_task_id: Optional[str] = Field(None, description="处理结果：创建的新子任务 ID")


class RejectRequest(BaseModel):
    reason: str = Field("", description="拒绝原因")


# ============================================================
# 路由
# ============================================================

@router.post("", response_model=EscalationResponse, summary="创建任务上报")
async def create_escalation(
    req: EscalationCreateRequest,
    agent: Agent = Depends(require_role("executor")),
    db: Session = Depends(get_db),
):
    """Executor 上报新需求给 Planner"""
    try:
        escalation = escalation_service.create_escalation(
            db,
            source_agent=agent.id,
            task_id=req.task_id,
            title=req.title,
            description=req.description,
            suggested_category=req.suggested_category,
            source_sub_task_id=req.source_sub_task_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return escalation


@router.get("", summary="查看上报列表")
async def list_escalations(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """查看任务上报列表，可按任务/状态过滤"""
    return escalation_service.list_escalations(db, task_id=task_id, status=status)


@router.get("/{escalation_id}", response_model=EscalationResponse, summary="查看上报详情")
async def get_escalation(
    escalation_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """获取单条上报详情"""
    escalation = escalation_service.get_escalation(db, escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="上报不存在")
    return escalation


@router.put("/{escalation_id}/accept", response_model=EscalationResponse, summary="接受上报")
async def accept_escalation(
    escalation_id: str,
    req: AcceptRequest = AcceptRequest(),
    agent: Agent = Depends(require_role("planner")),
    db: Session = Depends(get_db),
):
    """Planner 接受上报，可关联已创建的子任务"""
    try:
        return escalation_service.accept_escalation(
            db, escalation_id, result_sub_task_id=req.result_sub_task_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{escalation_id}/reject", response_model=EscalationResponse, summary="拒绝上报")
async def reject_escalation(
    escalation_id: str,
    req: RejectRequest = RejectRequest(),
    agent: Agent = Depends(require_role("planner")),
    db: Session = Depends(get_db),
):
    """Planner 拒绝上报"""
    try:
        return escalation_service.reject_escalation(
            db, escalation_id, reason=req.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
