from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.exceptions.models import ExceptionDomain, ExceptionSeverity
from app.modules.exceptions.repository import ExceptionRepository
from app.modules.exceptions.service import ExceptionService
from app.modules.rules.models import (
    ActionType,
    ConditionOperator,
    RuleCondition,
    RuleExecutionStatus,
    TriggerEvent,
)
from app.modules.rules.repository import RuleRepository
from app.modules.rules.schemas import RuleCreate, RuleUpdate
from app.modules.rules.service import RuleEngineService


@pytest.fixture
def mock_webhook_calls() -> list[dict[str, Any]]:
    return []


@pytest.fixture
def rule_service(
    session: AsyncSession, mock_webhook_calls: list[dict[str, Any]]
) -> RuleEngineService:
    repo = RuleRepository(session)
    alert_service = AlertService(session, AlertRepository(session))
    exception_service = ExceptionService(session, ExceptionRepository(session))

    async def mock_webhook_client(
        url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> bool:
        mock_webhook_calls.append({"url": url, "payload": payload, "headers": headers or {}})
        return True

    return RuleEngineService(
        session=session,
        repository=repo,
        alert_service=alert_service,
        exception_service=exception_service,
        webhook_client=mock_webhook_client,
    )


@pytest.mark.asyncio
async def test_rule_crud_lifecycle(rule_service: RuleEngineService) -> None:
    # 1. Create rule
    create_payload = RuleCreate(
        name="Auto-Escalate Critical Variance",
        description="Notify n8n and ops when inventory variance > 10",
        trigger_event=TriggerEvent.INVENTORY_VARIANCE_DETECTED,
        conditions=[
            RuleCondition(
                field="variance_amount",
                operator=ConditionOperator.GREATER_THAN,
                value=10,
            )
        ],
        actions=[
            {
                "action_type": ActionType.TRIGGER_WEBHOOK,
                "parameters": {"webhook_url": "https://n8n.internal.example.com/webhook/variance"},
            }
        ],
        is_active=True,
        priority=5,
    )

    created = await rule_service.create_rule(create_payload)
    assert created.id is not None
    assert created.name == "Auto-Escalate Critical Variance"
    assert created.priority == 5
    assert len(created.conditions) == 1
    assert len(created.actions) == 1

    # 2. Get rule
    fetched = await rule_service.get_rule(created.id)
    assert fetched.id == created.id
    assert fetched.name == created.name

    # 3. Update rule
    updated = await rule_service.update_rule(
        created.id,
        RuleUpdate(priority=1, is_active=False),
    )
    assert updated.priority == 1
    assert updated.is_active is False

    # 4. List rules
    all_rules = await rule_service.list_rules()
    assert len(all_rules) == 1

    active_rules = await rule_service.list_rules(active_only=True)
    assert len(active_rules) == 0

    # 5. Delete rule
    await rule_service.delete_rule(created.id)
    assert len(await rule_service.list_rules()) == 0


@pytest.mark.asyncio
async def test_condition_evaluation_operators(rule_service: RuleEngineService) -> None:
    evaluator = rule_service.evaluate_condition

    # EQUALS
    assert evaluator(100, ConditionOperator.EQUALS, 100) is True
    assert evaluator("shopee", ConditionOperator.EQUALS, "shopee") is True
    assert evaluator("tiktok", ConditionOperator.EQUALS, "shopee") is False

    # NOT_EQUALS
    assert evaluator("tiktok", ConditionOperator.NOT_EQUALS, "shopee") is True
    assert evaluator(10, ConditionOperator.NOT_EQUALS, 10) is False

    # GREATER_THAN / GREATER_THAN_OR_EQUAL
    assert evaluator(15.5, ConditionOperator.GREATER_THAN, 10) is True
    assert evaluator(10, ConditionOperator.GREATER_THAN, 10) is False
    assert evaluator(10, ConditionOperator.GREATER_THAN_OR_EQUAL, 10) is True
    assert evaluator(9.9, ConditionOperator.GREATER_THAN_OR_EQUAL, 10) is False

    # LESS_THAN / LESS_THAN_OR_EQUAL
    assert evaluator(5, ConditionOperator.LESS_THAN, 10) is True
    assert evaluator(10, ConditionOperator.LESS_THAN, 10) is False
    assert evaluator(10, ConditionOperator.LESS_THAN_OR_EQUAL, 10) is True

    # CONTAINS
    assert evaluator("SKU-PROMO-99", ConditionOperator.CONTAINS, "PROMO") is True
    assert evaluator("SKU-STANDARD", ConditionOperator.CONTAINS, "PROMO") is False
    assert evaluator(["tag1", "tag2"], ConditionOperator.CONTAINS, "tag1") is True

    # IN
    target_set = ["GHOST_ORDER", "FEE_OVERCHARGED"]
    assert evaluator("GHOST_ORDER", ConditionOperator.IN, target_set) is True
    assert evaluator("CLEAN_MATCH", ConditionOperator.IN, target_set) is False


@pytest.mark.asyncio
async def test_trigger_evaluation_triggers_webhook_and_creates_log(
    rule_service: RuleEngineService, mock_webhook_calls: list[dict[str, Any]]
) -> None:
    rule = await rule_service.create_rule(
        RuleCreate(
            name="Notify n8n on Settlement Ghost Order",
            trigger_event=TriggerEvent.SETTLEMENT_DISCREPANCY_DETECTED,
            conditions=[
                RuleCondition(
                    field="discrepancy_type",
                    operator=ConditionOperator.EQUALS,
                    value="GHOST_ORDER",
                )
            ],
            actions=[
                {
                    "action_type": ActionType.TRIGGER_WEBHOOK,
                    "parameters": {"webhook_url": "https://n8n.internal.example.com/webhook/ghost-order"},
                }
            ],
            is_active=True,
            priority=1,
        )
    )

    # 1. Matching trigger
    matching_context = {
        "discrepancy_type": "GHOST_ORDER",
        "order_id": "SP-UNKNOWN-999",
        "net_payout": 450000,
        "channel_code": "shopee",
    }
    logs = await rule_service.evaluate_trigger(
        TriggerEvent.SETTLEMENT_DISCREPANCY_DETECTED, matching_context
    )

    assert len(logs) == 1
    assert logs[0].rule_id == rule.id
    assert logs[0].matched is True
    assert logs[0].status == RuleExecutionStatus.SUCCESS
    assert len(logs[0].actions_taken) == 1

    # Check webhook invocation
    assert len(mock_webhook_calls) == 1
    assert mock_webhook_calls[0]["url"] == "https://n8n.internal.example.com/webhook/ghost-order"
    assert mock_webhook_calls[0]["payload"]["discrepancy_type"] == "GHOST_ORDER"

    # 2. Non-matching trigger
    mock_webhook_calls.clear()
    non_matching_context = {
        "discrepancy_type": "CLEAN_MATCH",
        "order_id": "SP-OK-111",
        "net_payout": 500000,
    }
    logs_skipped = await rule_service.evaluate_trigger(
        TriggerEvent.SETTLEMENT_DISCREPANCY_DETECTED, non_matching_context
    )
    assert len(logs_skipped) == 1
    assert logs_skipped[0].matched is False
    assert logs_skipped[0].status == RuleExecutionStatus.SKIPPED
    assert len(mock_webhook_calls) == 0


@pytest.mark.asyncio
async def test_trigger_evaluation_creates_operational_exception(
    rule_service: RuleEngineService,
) -> None:
    # Rule: when inventory variance > 20, create a CRITICAL operational exception
    await rule_service.create_rule(
        RuleCreate(
            name="Auto Exception on Severe Variance",
            trigger_event=TriggerEvent.INVENTORY_VARIANCE_DETECTED,
            conditions=[
                RuleCondition(
                    field="variance_amount",
                    operator=ConditionOperator.GREATER_THAN,
                    value=20,
                )
            ],
            actions=[
                {
                    "action_type": ActionType.CREATE_EXCEPTION,
                    "parameters": {
                        "domain": "inventory",
                        "severity": "critical",
                        "reference_id_field": "sku",
                        "title_template": "Severe Inventory Discrepancy for SKU {sku}",
                        "description_template": (
                            "Physical ERP stock is {erp_stock}, "
                            "channel allocated is {channel_stock}"
                        ),
                    },
                }
            ],
            is_active=True,
            priority=1,
        )
    )

    context = {
        "sku": "TSHIRT-BLK-L",
        "variance_amount": 25,
        "erp_stock": 10,
        "channel_stock": 35,
        "channel_code": "tiktok",
    }

    logs = await rule_service.evaluate_trigger(
        TriggerEvent.INVENTORY_VARIANCE_DETECTED, context
    )

    assert len(logs) == 1
    assert logs[0].matched is True
    assert logs[0].status == RuleExecutionStatus.SUCCESS

    # Verify exception was created in exceptions table
    all_exceptions = await rule_service.exception_service.list_exceptions()
    assert len(all_exceptions) == 1
    created_ex = all_exceptions[0]
    assert created_ex.reference_id == "TSHIRT-BLK-L"
    assert created_ex.domain == ExceptionDomain.INVENTORY_VARIANCE
    assert created_ex.severity == ExceptionSeverity.CRITICAL
    assert "Severe Inventory Discrepancy" in created_ex.title


@pytest.mark.asyncio
async def test_multi_rule_priority_order_and_resiliency(
    rule_service: RuleEngineService, mock_webhook_calls: list[dict[str, Any]]
) -> None:
    # Rule 1: High priority (1), but webhook fails
    async def failing_webhook(
        url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> bool:
        if "faulty" in url:
            raise ConnectionError("n8n server unreachable")
        mock_webhook_calls.append({"url": url, "payload": payload})
        return True

    rule_service.set_webhook_client(failing_webhook)

    r1 = await rule_service.create_rule(
        RuleCreate(
            name="Faulty Rule",
            trigger_event=TriggerEvent.ORDER_INGESTED,
            conditions=[
                RuleCondition(
                    field="total_amount",
                    operator=ConditionOperator.GREATER_THAN,
                    value=1000,
                )
            ],
            actions=[
                {
                    "action_type": ActionType.TRIGGER_WEBHOOK,
                    "parameters": {"webhook_url": "https://faulty.com"},
                }
            ],
            is_active=True,
            priority=1,
        )
    )

    r2 = await rule_service.create_rule(
        RuleCreate(
            name="Healthy Rule",
            trigger_event=TriggerEvent.ORDER_INGESTED,
            conditions=[
                RuleCondition(
                    field="total_amount",
                    operator=ConditionOperator.GREATER_THAN,
                    value=1000,
                )
            ],
            actions=[
                {
                    "action_type": ActionType.TRIGGER_WEBHOOK,
                    "parameters": {"webhook_url": "https://healthy.com"},
                }
            ],
            is_active=True,
            priority=2,
        )
    )

    context = {"total_amount": 5000, "order_id": "ORD-123"}
    logs = await rule_service.evaluate_trigger(TriggerEvent.ORDER_INGESTED, context)

    assert len(logs) == 2
    # Rule 1 failed, but logged with status=FAILED and error_message
    assert logs[0].rule_id == r1.id
    assert logs[0].status == RuleExecutionStatus.FAILED
    assert "n8n server unreachable" in (logs[0].error_message or "")

    # Rule 2 still executed successfully!
    assert logs[1].rule_id == r2.id
    assert logs[1].status == RuleExecutionStatus.SUCCESS
    assert len(mock_webhook_calls) == 1
    assert mock_webhook_calls[0]["url"] == "https://healthy.com"


@pytest.mark.asyncio
async def test_trigger_evaluation_creates_alert(
    rule_service: RuleEngineService,
) -> None:
    await rule_service.create_rule(
        RuleCreate(
            name="Create Alert on Order Sync Failure",
            trigger_event=TriggerEvent.ORDER_INGESTED,
            conditions=[
                RuleCondition(
                    field="sync_status",
                    operator=ConditionOperator.EQUALS,
                    value="FAILED",
                )
            ],
            actions=[
                {
                    "action_type": ActionType.CREATE_ALERT,
                    "parameters": {
                        "alert_type": "sync_failure",
                        "severity": "critical",
                        "dedup_key": "sync_fail:{order_id}",
                        "message": "Order sync failed for {order_id}",
                    },
                }
            ],
            is_active=True,
            priority=1,
        )
    )

    context = {"sync_status": "FAILED", "order_id": "ORD-FAIL-999"}
    logs = await rule_service.evaluate_trigger(TriggerEvent.ORDER_INGESTED, context)
    assert len(logs) == 1
    assert logs[0].matched is True
    assert logs[0].status == RuleExecutionStatus.SUCCESS

    # Verify alert exists in database
    alerts = await rule_service._alert_service.list_alerts()  # type: ignore[union-attr]
    assert len(alerts) >= 1
    assert any("ORD-FAIL-999" in a.message for a in alerts)


@pytest.mark.asyncio
async def test_rules_api_endpoints(session: AsyncSession) -> None:
    from httpx import ASGITransport, AsyncClient

    from app.database import get_session
    from app.main import app

    app.dependency_overrides[get_session] = lambda: session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Create rule via POST /api/v1/rules
            create_res = await client.post(
                "/api/v1/rules",
                json={
                    "name": "API Created Rule",
                    "description": "Rule created via HTTP API",
                    "trigger_event": "settlement_discrepancy_detected",
                    "conditions": [
                        {
                            "field": "net_payout",
                            "operator": "less_than",
                            "value": 0,
                        }
                    ],
                    "actions": [
                        {
                            "action_type": "trigger_webhook",
                            "parameters": {"webhook_url": "https://n8n.example.com"},
                        }
                    ],
                    "is_active": True,
                    "priority": 10,
                },
            )
            assert create_res.status_code == 201, create_res.text
            rule_id = create_res.json()["id"]

            # 2. Get rule via GET /api/v1/rules/{id}
            get_res = await client.get(f"/api/v1/rules/{rule_id}")
            assert get_res.status_code == 200
            assert get_res.json()["name"] == "API Created Rule"

            # 3. List rules via GET /api/v1/rules
            list_res = await client.get("/api/v1/rules")
            assert list_res.status_code == 200
            assert any(r["id"] == rule_id for r in list_res.json())

            # 4. Evaluate trigger via POST /api/v1/rules/evaluate
            eval_res = await client.post(
                "/api/v1/rules/evaluate",
                json={
                    "trigger_event": "settlement_discrepancy_detected",
                    "context": {"net_payout": -50000},
                },
            )
            assert eval_res.status_code == 200
            data = eval_res.json()
            assert data["matched_count"] >= 1

            # 5. Delete rule via DELETE /api/v1/rules/{id}
            del_res = await client.delete(f"/api/v1/rules/{rule_id}")
            assert del_res.status_code == 204
    finally:
        app.dependency_overrides.clear()
