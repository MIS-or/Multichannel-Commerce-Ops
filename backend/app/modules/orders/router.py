from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.channels import ChannelService, get_channel_service
from app.modules.inventory import InventoryService, get_inventory_service
from app.modules.ledger import LedgerService, get_ledger_service
from app.modules.orders.models import OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    OrderDetail,
    OrderImportRequest,
    OrderImportResponse,
    OrderImportStatus,
    OrderRead,
)
from app.modules.orders.service import OrderService
from app.modules.products import ProductService, get_product_service

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(
    session: AsyncSession = Depends(get_session),
    channel_service: ChannelService = Depends(get_channel_service),
    product_service: ProductService = Depends(get_product_service),
    inventory_service: InventoryService = Depends(get_inventory_service),
    ledger_service: LedgerService = Depends(get_ledger_service),
) -> OrderService:
    return OrderService(
        session=session,
        repository=OrderRepository(session),
        channel_service=channel_service,
        product_service=product_service,
        inventory_service=inventory_service,
        ledger_service=ledger_service,
    )


@router.post("/import", response_model=OrderImportResponse, status_code=status.HTTP_201_CREATED)
async def import_order(
    payload: OrderImportRequest,
    response: Response,
    service: OrderService = Depends(get_order_service),
) -> OrderImportResponse:
    result = await service.import_order(payload)
    if result.status is OrderImportStatus.DUPLICATE:
        response.status_code = status.HTTP_200_OK
    return result


@router.get("", response_model=list[OrderRead])
async def list_orders(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    channel: str | None = Query(default=None),
    status: OrderStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    service: OrderService = Depends(get_order_service),
) -> list[OrderRead]:
    return await service.list_orders(
        limit=limit,
        offset=offset,
        channel=channel,
        status=status,
        search=search,
    )


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderDetail:
    return await service.get_order(order_id)
