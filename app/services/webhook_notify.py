"""
OpenClaw Webhook 事件通知服务
当任务状态发生关键变化时，通过 OpenClaw Gateway 的 Webhook 端点唤醒对应 Agent。

使用方式：
  在 service 层关键操作完成后调用 fire_event()，它会异步发送 HTTP 请求到
  OpenClaw Gateway 的 /hooks/agent 或 /hooks/wake 端点，唤醒目标 Agent。

配置项（config.yaml 中添加）：
  openclaw:
    gateway_url: "http://localhost:4160"
    webhook_token: "your-secret-token"
    webhook_enabled: true
"""
import logging
import threading
from typing import Optional

logger = logging.getLogger("openclaw_webhook")


class OpenClawWebhookNotifier:
    """OpenClaw Webhook 通知器（轻量级，无外部依赖）"""

    def __init__(self):
        self._gateway_url: str = ""
        self._webhook_token: str = ""
        self._enabled: bool = False

    def configure(self, gateway_url: str, webhook_token: str, enabled: bool = True):
        """初始化配置（应用启动时调用）"""
        self._gateway_url = gateway_url.rstrip("/")
        self._webhook_token = webhook_token
        self._enabled = enabled
        if enabled:
            logger.info(f"[OpenClaw Webhook] 已启用 → {self._gateway_url}")
        else:
            logger.info("[OpenClaw Webhook] 未启用（webhook_enabled=false）")

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._gateway_url)

    def fire_event(
        self,
        event: str,
        target_agent: str,
        payload: Optional[dict] = None,
    ):
        """
        触发事件通知（异步，不阻塞调用者）

        Args:
            event: 事件名称（如 task_submitted, review_completed）
            target_agent: 目标 Agent ID（如 reviewer, planner）
            payload: 事件附带数据
        """
        if not self.enabled:
            return

        # 在后台线程中发送，避免阻塞 API 响应
        thread = threading.Thread(
            target=self._send_webhook,
            args=(event, target_agent, payload or {}),
            daemon=True,
        )
        thread.start()

    def _send_webhook(self, event: str, target_agent: str, payload: dict):
        """实际发送 Webhook 请求（在后台线程中执行）"""
        import urllib.request
        import urllib.error
        import json

        url = f"{self._gateway_url}/hooks/agent"
        data = json.dumps({
            "agentId": target_agent,
            "event": event,
            "payload": payload,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }
        if self._webhook_token:
            headers["Authorization"] = f"Bearer {self._webhook_token}"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(
                    f"[OpenClaw Webhook] ✅ {event} → {target_agent} (HTTP {resp.status})"
                )
        except urllib.error.HTTPError as e:
            logger.warning(
                f"[OpenClaw Webhook] ⚠️ {event} → {target_agent} 失败: HTTP {e.code} {e.reason}"
            )
        except Exception as e:
            logger.warning(
                f"[OpenClaw Webhook] ⚠️ {event} → {target_agent} 失败: {e}"
            )


# === 全局单例 ===
notifier = OpenClawWebhookNotifier()


# === 便捷函数（供 service 层调用） ===

def fire_event(event: str, target_agent: str, payload: Optional[dict] = None):
    """触发事件通知的便捷入口"""
    notifier.fire_event(event, target_agent, payload)


# ============================================================
# 预定义事件常量
# ============================================================

class Events:
    """标准事件名称"""
    # 子任务生命周期
    TASK_ASSIGNED = "task_assigned"          # Planner 分配了子任务
    TASK_SUBMITTED = "task_submitted"        # Executor 提交了成果
    TASK_COMPLETED = "task_completed"        # 子任务最终完成

    # 审查相关
    REVIEW_APPROVED = "review_approved"      # 审查通过
    REVIEW_REJECTED = "review_rejected"      # 审查驳回（需要返工）

    # 上报相关
    ESCALATION_CREATED = "escalation_created"  # Executor 上报了新需求

    # 巡查相关
    PATROL_ALERT = "patrol_alert"            # 巡查发现异常

    # 全局
    ALL_SUBTASKS_DONE = "all_subtasks_done"   # 某任务的所有子任务完成
