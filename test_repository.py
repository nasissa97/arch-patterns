# pylint: diable=protected-access
import model
import repository

from sqlalchemy import text

def insert_order_line(session):
  session.execute(
    text("INSERT INTO order_lines (orderid, sku, qty) VALUES (:orderid, :sku, :qty)"), 
    dict(orderid="order1", sku="GENERIC-SOFA", qty=12),
  )
  [[orderline_id]] = session.execute(
    text('SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku'),
    dict(orderid="order1", sku="GENERIC-SOFA"),
  )
  return orderline_id

def test_repository_can_save_a_batch(session):
  batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
  
  repo = repository.SqlAlchemyRepository(session)
  repo.add(batch)
  session.commit()

  rows = session.execute(
    text('SELECT reference, sku, _purchased_quantity, eta FROM batches')
  )
  assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]

def insert_batch(session, batch_id):
  session.execute(
    text("INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES (:batch_id, :sku, :qty, null)"),
    dict(batch_id=batch_id, sku="GENERIC-SOFA", qty=100),
  )
  result = session.execute(
    text("SELECT id FROM batches WHERE reference=:batch_id AND sku=:sku"),
    dict(batch_id=batch_id, sku="GENERIC-SOFA")
  )
  batch_id = result.scalar_one()
  return batch_id

def insert_allocations(session, orderline_id, batch_id):
  session.execute(
    text("INSERT INTO allocations (orderline_id, batch_id) VALUES (:orderline_id, :batch_id)"),
    dict(orderline_id=orderline_id, batch_id=batch_id)
  )

def test_repository_can_retrieve_a_batch_with_allocations(clear_db, session):
  orderline_id = insert_order_line(session)
  batch1_id = insert_batch(session, "batch1")
  insert_batch(session, "batch2")
  insert_allocations(session, orderline_id, batch1_id)

  repo = repository.SqlAlchemyRepository(session)
  retrived = repo.get("batch1")
  print(retrived)

  expected = model.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
  assert retrived == expected
  assert retrived.sku == expected.sku
  assert retrived._purchased_quantity == expected._purchased_quantity
  assert retrived._allocations == {
    model.OrderLine("order1", "GENERIC-SOFA", 12)
  }
