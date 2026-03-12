"""
Agent 业务逻辑
"""
import uuid
import secrets
from sqlalchemy.orm import Session

from app.models.agent import Agent


def generate_api_key() -> str:
    """生成唯一的 API Key，格式 ak_<32位随机hex>"""
    return f"ak_{secrets.token_hex(16)}"


# 预定义的任务类别
TASK_CATEGORIES = {
    "product", "ui_design", "frontend", "backend",
    "database", "devops", "general",
}


def register_agent(
    db: Session,
    name: str,
    role: str,
    description: str = "",
    job_title: str = "",
    specialties: list = None,
) -> Agent:
    """注册新 Agent，生成 API Key"""
    valid_roles = {"planner", "executor", "reviewer", "patrol"}
    if role not in valid_roles:
        raise ValueError(f"无效角色 '{role}'，可选: {', '.join(valid_roles)}")

    # 校验 specialties 合法性
    if specialties:
        invalid = set(specialties) - TASK_CATEGORIES
        if invalid:
            raise ValueError(f"无效的任务类别: {', '.join(invalid)}，可选: {', '.join(sorted(TASK_CATEGORIES))}")

    # 防止重复注册
    existing = db.query(Agent).filter(Agent.name == name).first()
    if existing:
        raise ValueError(f"名称 '{name}' 已被注册")

    agent = Agent(
        id=str(uuid.uuid4()),
        name=name,
        role=role,
        description=description,
        job_title=job_title,
        specialties=specialties or [],
        api_key=generate_api_key(),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def reset_agent_api_key(db: Session, agent_id: str) -> Agent:
    """重置 Agent 的 API Key"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent {agent_id} 不存在")

    agent.api_key = generate_api_key()
    db.commit()
    db.refresh(agent)
    return agent


def list_agents(db: Session, role: str = None, status: str = None) -> list:
    """查询 Agent 列表，可按角色/状态过滤"""
    query = db.query(Agent)
    if role:
        query = query.filter(Agent.role == role)
    if status:
        query = query.filter(Agent.status == status)
    return query.all()


def find_agents_by_category(db: Session, category: str) -> list:
    """
    根据任务类别查找匹配的 Agent（specialties 包含该类别）。
    返回结果按积分降序排列，优先高分 Agent。
    """
    if category not in TASK_CATEGORIES:
        raise ValueError(f"无效的任务类别 '{category}'，可选: {', '.join(sorted(TASK_CATEGORIES))}")

    # general 类别匹配所有 executor
    if category == "general":
        return (
            db.query(Agent)
            .filter(Agent.role == "executor", Agent.status != "offline")
            .order_by(Agent.total_score.desc())
            .all()
        )

    # 查询 specialties JSON 数组中包含该 category 的 Agent
    # SQLite JSON 查询：使用 json_each 或 LIKE 匹配
    all_executors = (
        db.query(Agent)
        .filter(Agent.role == "executor", Agent.status != "offline")
        .order_by(Agent.total_score.desc())
        .all()
    )
    return [a for a in all_executors if category in (a.specialties or [])]


def get_agent_by_id(db: Session, agent_id: str) -> Agent:
    """根据 ID 获取 Agent"""
    return db.query(Agent).filter(Agent.id == agent_id).first()


def update_agent_status(db: Session, agent_id: str, status: str) -> Agent:
    """更新 Agent 状态"""
    valid_statuses = {"available", "busy", "offline"}
    if status not in valid_statuses:
        raise ValueError(f"无效状态 '{status}'，可选: {', '.join(valid_statuses)}")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent {agent_id} 不存在")

    agent.status = status
    db.commit()
    db.refresh(agent)
    return agent
