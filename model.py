from typing import NewType, Optional 
from datetime import date
from dataclasses import dataclass

Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)

@dataclass(frozen=True)
class OrderLine:
  orderid: str
  sku: str
  qty: int

class Batch:
  def __init__(self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]):
    self.reference = ref
    self.sku = sku
    self.eta = eta
    self._purchased_quantity = qty
    self._allocations = set() # type: Set[OrderLine]

  def allocate(self, line: OrderLine):
    if self.can_allocate(line):
      self._allocations.add(line)

  def decallocate(self, line: OrderLine):
    if line in self._allocations:
      self._allocations.remove(line)

  @property
  def allocated_quantity(self) -> int:
    return sum(line.qty for line in self._allocations)

  @property
  def available_quantity(self) -> int:
    return self._purchased_quantity
  
  def can_allocate(self, line: OrderLine) -> bool:
    return self.sku == line.sku and self.available_quantity >= line.qty