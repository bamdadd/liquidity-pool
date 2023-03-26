from datetime import datetime
from enum import Enum

from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str


class OrderType(str, Enum):
    buy = "buy"
    sell = "sell"
class Order(BaseModel):
    type: str
    product: str
    amount: float

# class Order(BaseModel):
#     id: str
#     user_id: str
#     type: OrderType
#     product: str
#     amount: float
#     price: float
#     timestamp: datetime


class DepositInput(BaseModel):
    token: str
    amount: float

class WithdrawInput(BaseModel):
    token: str
    amount: float

class AddLiquidityInput(BaseModel):
    token_a: str
    token_b: str
    amount_a: float
    amount_b: float

class RemoveLiquidityInput(BaseModel):
    token_a: str
    token_b: str

class PlaceOrderInput(BaseModel):
    type: str
    product: str
    amount: float
    price: float