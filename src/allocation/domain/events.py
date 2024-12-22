# pylint: disable=too-few-public-methods
from dataclasses import dataclass


class Event:
  pass

  
@dataclass
class OutOfStock(Event):
  sku: str

  
@dataclass
class Allocated(Event):
  orderid: str
  sku: str
  qty: int
  batchref: str