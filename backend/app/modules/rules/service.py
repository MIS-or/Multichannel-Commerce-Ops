from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.models import AlertSeverity, AlertType
from app.modules.exceptions.models import ExceptionDomain, ExceptionSeverity
from app.modules.exceptions.schemas import ExceptionCreate
from app.modules.rules.models import (
    ActionType,
    ConditionOperator,
    Rule,
    RuleExecutionLog,
    RuleExecutionStatus,
    TriggerEvent,
)
from app.modules.rules.repository import RuleRepository
from app.modules.rules.schemas import (
    RuleCreate,
    RuleExecutionLogRead,
    RuleRead,
    RuleUpdate,
)
from app.shared.errors import NotFoundError
from app.shared.time import utc_now

if TYPE_CHECKING:
    from app.modules.alerts.service import AlertService
    from app.modules.exceptions.service import ExceptionService

logger = logging.getLogger(__name__)

WebhookClientType = Callable[[str, dict[str, Any], dict[str, str] | None], Awaitable[bool]]


class RuleEngineService:
    """Evaluates declarative rules against operational triggers and dispatches automated actions."""

    def __init__(
        self,
        session: AsyncSession,
        repository: RuleRepository | None = None,
        alert_service: AlertService | None = None,
        exception_service: ExceptionService | None = None,
        webhook_client: WebhookClientType | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or RuleRepository(session)
        self._alert_service = alert_service
        self._exception_service = exception_service
        self._webhook_client = webhook_client

    @property
    def exception_service(self) -> ExceptionService | None:
        return self._exception_service

    def set_webhook_client(self, client: WebhookClientType) -> None:
        self._webhook_client = client

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------
    async def create_rule(self, payload: RuleCreate) -> RuleRead:
        now = utc_now()
        conditions_data: list[dict[str, Any]] = [
            c.model_dump() if hasattr(c, "model_dump") else dict(c)
            for c in payload.conditions
        ]
        rule = Rule(
            name=payload.name,
            description=payload.description,
            trigger_event=payload.trigger_event,
            conditions=conditions_data,
            actions=payload.actions,
            is_active=payload.is_active,
            priority=payload.priority,
            created_at=now,
            updated_at=now,
        )
        saved = await self._repository.create(rule)
        return RuleRead.model_validate(saved)

    async def get_rule(self, rule_id: int) -> RuleRead:
        rule = await self._repository.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError(
                "RULE_NOT_FOUND",
                f"Rule id '{rule_id}' does not exist",
                details={"rule_id": rule_id},
            )
        return RuleRead.model_validate(rule)

    async def update_rule(self, rule_id: int, payload: RuleUpdate) -> RuleRead:
        rule = await self._repository.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError(
                "RULE_NOT_FOUND",
                f"Rule id '{rule_id}' does not exist",
                details={"rule_id": rule_id},
            )

        if payload.name is not None:
            rule.name = payload.name
        if payload.description is not None:
            rule.description = payload.description
        if payload.conditions is not None:
            rule.conditions = [c.model_dump() for c in payload.conditions]
        if payload.actions is not None:
            rule.actions = payload.actions
        if payload.is_active is not None:
            rule.is_active = payload.is_active
        if payload.priority is not None:
            rule.priority = payload.priority
        rule.updated_at = utc_now()

        updated = await self._repository.update(rule)
        return RuleRead.model_validate(updated)

    async def delete_rule(self, rule_id: int) -> None:
        rule = await self._repository.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError(
                "RULE_NOT_FOUND",
                f"Rule id '{rule_id}' does not exist",
                details={"rule_id": rule_id},
            )
        await self._repository.delete(rule)

    async def list_rules(self, *, active_only: bool = False) -> list[RuleRead]:
        rules = await self._repository.list_all(active_only=active_only)
        return [RuleRead.model_validate(r) for r in rules]

    async def list_logs(
        self, *, rule_id: int | None = None, limit: int = 50
    ) -> list[RuleExecutionLogRead]:
        logs = await self._repository.list_logs(rule_id=rule_id, limit=limit)
        return [RuleExecutionLogRead.model_validate(log) for log in logs]

    # -------------------------------------------------------------------------
    # Condition Evaluation Engine
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_nested_value(data: dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        current: Any = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def evaluate_condition(
        self, actual: Any, operator: ConditionOperator | str, target: Any
    ) -> bool:
        if isinstance(operator, str):
            try:
                op_enum = ConditionOperator(operator)
            except ValueError:
                return False
        else:
            op_enum = operator

        # Numeric comparisons
        if op_enum in {
            ConditionOperator.GREATER_THAN,
            ConditionOperator.GREATER_THAN_OR_EQUAL,
            ConditionOperator.LESS_THAN,
            ConditionOperator.LESS_THAN_OR_EQUAL,
        }:
            try:
                actual_num = float(actual)
                target_num = float(target)
            except (ValueError, TypeError):
                return False

            if op_enum == ConditionOperator.GREATER_THAN:
                return actual_num > target_num
            elif op_enum == ConditionOperator.GREATER_THAN_OR_EQUAL:
                return actual_num >= target_num
            elif op_enum == ConditionOperator.LESS_THAN:
                return actual_num < target_num
            elif op_enum == ConditionOperator.LESS_THAN_OR_EQUAL:
                return actual_num <= target_num

        if op_enum == ConditionOperator.EQUALS:
            if actual == target:
                return True
            try:
                return float(actual) == float(target)
            except (ValueError, TypeError):
                return str(actual) == str(target)

        if op_enum == ConditionOperator.NOT_EQUALS:
            return not self.evaluate_condition(actual, ConditionOperator.EQUALS, target)

        if op_enum == ConditionOperator.CONTAINS:
            if actual is None:
                return False
            if isinstance(actual, (list, tuple, set)):
                return target in actual or any(str(x) == str(target) for x in actual)
            return str(target).lower() in str(actual).lower()

        if op_enum == ConditionOperator.IN:
            if not isinstance(target, (list, tuple, set)):
                return False
            return actual in target or any(str(x) == str(actual) for x in target)

        return False

    def _matches_all_conditions(
        self, conditions: list[dict[str, Any]], context: dict[str, Any]
    ) -> bool:
        for cond in conditions:
            field_name = cond.get("field", "")
            operator = cond.get("operator", "")
            target_value = cond.get("value")

            actual_value = self._extract_nested_value(context, field_name)
            if actual_value is None:
                return False

            if not self.evaluate_condition(actual_value, operator, target_value):
                return False
        return True

    # -------------------------------------------------------------------------
    # Action Dispatcher
    # -------------------------------------------------------------------------
    async def _dispatch_action(
        self, action: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        action_type = action.get("action_type")
        params = action.get("parameters", {})
        result_info: dict[str, Any] = {"action_type": action_type}

        if action_type == ActionType.TRIGGER_WEBHOOK:
            url = params.get("webhook_url", "")
            headers = params.get("headers", {})
            if not url:
                raise ValueError("Webhook action missing required 'webhook_url' parameter")

            if self._webhook_client is not None:
                await self._webhook_client(url, context, headers)
            else:
                # Default async delivery using httpx if available
                try:
                    import httpx

                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(url, json=context, headers=headers)
                        response.raise_for_status()
                except ImportError:
                    logger.warning(
                        "httpx is not installed. Webhook delivery simulated for %s", url
                    )
            result_info["webhook_url"] = url
            result_info["status"] = "delivered"

        elif action_type == ActionType.CREATE_EXCEPTION:
            if self._exception_service is None:
                raise RuntimeError("ExceptionService is not configured for CREATE_EXCEPTION action")

            domain_str = str(params.get("domain", "inventory_variance"))
            if domain_str in ("inventory", "inventory_variance"):
                domain = ExceptionDomain.INVENTORY_VARIANCE
            elif domain_str in ("settlement", "settlement_discrepancy"):
                domain = ExceptionDomain.SETTLEMENT_DISCREPANCY
            elif domain_str in ExceptionDomain:
                domain = ExceptionDomain(domain_str)
            else:
                domain = ExceptionDomain.INVENTORY_VARIANCE

            severity_str = params.get("severity", "medium")
            if severity_str in ExceptionSeverity:
                severity = ExceptionSeverity(severity_str)
            else:
                severity = ExceptionSeverity.MEDIUM

            ref_field = params.get("reference_id_field", "reference_id")
            reference_id = str(context.get(ref_field, context.get("reference_id", "REF-UNKNOWN")))

            title_tmpl = params.get("title_template", "Operational Discrepancy for {reference_id}")
            desc_tmpl = params.get("description_template", "Variance detected: {variance_amount}")

            try:
                title = title_tmpl.format(**context, reference_id=reference_id)
            except KeyError:
                title = title_tmpl
            try:
                description = desc_tmpl.format(**context)
            except KeyError:
                description = desc_tmpl

            variance_val = context.get("variance_amount")
            variance_dec = Decimal(str(variance_val)) if variance_val is not None else None

            created_exc = await self._exception_service.create_exception(
                ExceptionCreate(
                    domain=domain,
                    severity=severity,
                    reference_id=reference_id,
                    channel_code=context.get("channel_code"),
                    title=title,
                    description=description,
                    variance_amount=variance_dec,
                    payload_snapshot=context,
                )
            )
            result_info["exception_id"] = created_exc.id
            result_info["reference_id"] = reference_id

        elif action_type == ActionType.CREATE_ALERT:
            if self._alert_service is None:
                raise RuntimeError("AlertService is not configured for CREATE_ALERT action")

            alert_type_str = params.get("alert_type", "reconciliation_mismatch")
            if alert_type_str in AlertType:
                alert_type = AlertType(alert_type_str)
            else:
                alert_type = AlertType.RECONCILIATION_MISMATCH

            sev_str = params.get("severity", "warning")
            sev = AlertSeverity(sev_str) if sev_str in AlertSeverity else AlertSeverity.WARNING

            dedup_tmpl = str(params.get("dedup_key", "rule_alert:{reference_id}"))
            msg_tmpl = str(params.get("message", "Rule alert triggered for {reference_id}"))
            try:
                dedup_key = dedup_tmpl.format(**context)
            except KeyError:
                dedup_key = dedup_tmpl
            try:
                message = msg_tmpl.format(**context)
            except KeyError:
                message = msg_tmpl

            alert = await self._alert_service.create_once(
                alert_type=alert_type,
                severity=sev,
                dedup_key=dedup_key,
                message=message,
            )
            result_info["alert_id"] = alert.id

        elif action_type == ActionType.AUTO_ASSIGN_EXCEPTION:
            if self._exception_service is None:
                raise RuntimeError(
                    "ExceptionService is not configured for AUTO_ASSIGN_EXCEPTION action"
                )
            exc_id = context.get("exception_id")
            assignee = params.get("assign_to", "ops_team")
            if exc_id is not None:
                assigned = await self._exception_service.assign(
                    int(exc_id), str(assignee)
                )
                result_info["exception_id"] = assigned.id
                result_info["assigned_to"] = assignee

        return result_info

    # -------------------------------------------------------------------------
    # Trigger Evaluation Pipeline
    # -------------------------------------------------------------------------
    async def evaluate_trigger(
        self, trigger_event: TriggerEvent, context: dict[str, Any]
    ) -> list[RuleExecutionLogRead]:
        rules = await self._repository.get_active_by_trigger(trigger_event)
        execution_logs: list[RuleExecutionLogRead] = []

        for rule in rules:
            if rule.id is None:
                continue

            matches = self._matches_all_conditions(rule.conditions, context)
            if not matches:
                log = RuleExecutionLog(
                    rule_id=rule.id,
                    trigger_event=trigger_event,
                    matched=False,
                    status=RuleExecutionStatus.SKIPPED,
                    payload_snapshot=context,
                    actions_taken=[],
                    error_message=None,
                    executed_at=utc_now(),
                )
                saved_log = await self._repository.log_execution(log)
                execution_logs.append(RuleExecutionLogRead.model_validate(saved_log))
                continue

            # Rule matches: execute actions safely with isolation
            actions_taken: list[dict[str, Any]] = []
            status = RuleExecutionStatus.SUCCESS
            error_msg: str | None = None

            try:
                for action in rule.actions:
                    action_result = await self._dispatch_action(action, context)
                    actions_taken.append(action_result)
            except Exception as exc:
                logger.exception("Failed to execute rule action for rule %s: %s", rule.id, exc)
                status = RuleExecutionStatus.FAILED
                error_msg = str(exc)

            log = RuleExecutionLog(
                rule_id=rule.id,
                trigger_event=trigger_event,
                matched=True,
                status=status,
                payload_snapshot=context,
                actions_taken=actions_taken,
                error_message=error_msg,
                executed_at=utc_now(),
            )
            saved_log = await self._repository.log_execution(log)
            execution_logs.append(RuleExecutionLogRead.model_validate(saved_log))

        return execution_logs
