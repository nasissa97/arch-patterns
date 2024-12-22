# pylint: diasble=unused-argument
from __future__ import annotations
from dataclasses import asdict
from typing import Optional, TYPE_CHECKING
from allocation.domain import commands, events, model
from allocation.domain.model import OrderLine

if TYPE_CHECKING:
    from allocation.adapters import notifications
    from . import unit_of_work


class InvalidSku(Exception):
    pass


def add_batch(
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        product.allocate(line)
        uow.commit()


def reallocate(
  event: events.Deallocated,
  uow: unit_of_work.AbstractUnitOfWork,
):
  allocate(commands.Allocate(**asdict(event)), uow=uow)


def change_batch_quantity(
  event: events.BatchQuantityChanged,
  uow: unit_of_work.AbstractUnitOfWork,
):
  with uow:
    product = uow.products.get_by_batchref(batchref=event.ref)
    product.change_batch_quantity(ref=event.ref, qty=event.qty)
    uow.commit()

  
# pylint: disable=unused-argument


def send_out_of_stock_notification(
  event: events.OutOfStock,
  notifications: notifications.AbstractNotifications,
):
  notifications.send(
    "stock@made.com",
    f"Out of stock for {event.sku}",
  )

def publish_allocated_event(
  event: events.Allocated,
  publish:  callable
):
  publish("line_allocated", event)

  

def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
            """,
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref),
        )
        uow.commit()


def remove_allocation_from_read_model(
    event: events.Deallocated,
    uow: unit_of_work.SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            """
            DELETE FROM allocations_view
            WHERE orderid = :orderid AND sku = :sku
            """,
            dict(orderid=event.orderid, sku=event.sku),
        )
        uow.commit()

        
EVENT_HANDLERS = {
    events.Allocated: [publish_allocated_event, add_allocation_to_read_model],
    events.Deallocated: [remove_allocation_from_read_model, reallocate],
    events.OutOfStock: [send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]

COMMAND_HANDLERS = {
    commands.Allocate: allocate,
    commands.CreateBatch: add_batch,
    commands.ChangeBatchQuantity: change_batch_quantity,
}  # type: Dict[Type[commands.Command], Callable]