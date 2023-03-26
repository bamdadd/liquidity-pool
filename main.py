import threading
import time
from collections import defaultdict

import yaml
from fastapi import FastAPI, Depends, HTTPException

from account import deposit, withdraw, get_balance
from db import db
from models import DepositInput, WithdrawInput, PlaceOrderInput, AddLiquidityInput, RemoveLiquidityInput

app = FastAPI()

def get_current_user(username: str, password: str):
    if authenticate(username, password):
        return username
    raise HTTPException(status_code=401, detail="Invalid credentials")

def authenticate(username: str, password: str) -> bool:
    return (username, password) in db['users']

def get_fee(product: str) -> float:
    def get_config():
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)

    config = get_config()
    return config['fees'].get(product, 0)


def place_order(username: str, order_type: str, product: str, amount: float, price: float):
    if order_type not in ["buy", "sell"]:
        raise ValueError("Invalid order type")

    token_a, token_b = product.split("-")

    if order_type == "buy":
        required_balance = amount * price
        if db["balances"][username][token_b] < required_balance:
            raise ValueError("Insufficient balance")
        db["balances"][username][token_b] -= required_balance
    elif order_type == "sell":
        if db["balances"][username][token_a] < amount:
            raise ValueError("Insufficient balance")
        db["balances"][username][token_a] -= amount

    order = {
        "username": username,
        "type": order_type,
        "product": product,
        "amount": amount,
        "price": price,
    }

    db["orders"].append(order)


def add_liquidity(username: str, token_a: str, token_b: str, amount_a: float, amount_b: float):
    if db['balances'][username][token_a] >= amount_a and db['balances'][username][token_b] >= amount_b:
        db['balances'][username][token_a] -= amount_a
        db['balances'][username][token_b] -= amount_b
        db['liquidity_pools'][username][f"{token_a}-{token_b}"] = (amount_a, amount_b)
        print(username, "added liquiditity for", token_a, token_b, db['liquidity_pools'][username][f"{token_a}-{token_b}"])
    else:
        raise ValueError("Insufficient balance")

def remove_liquidity(username: str, token_a: str, token_b: str):
    pool_key = f"{token_a}-{token_b}"
    if pool_key in db['liquidity_pools'][username]:
        amount_a, amount_b = db['liquidity_pools'][username][pool_key]
        db['balances'][username][token_a] += amount_a
        db['balances'][username][token_b] += amount_b
        del db['liquidity_pools'][username][pool_key]
        print(username, "removed liquidity for", token_a, token_b, amount_a, amount_b)
    else:
        raise ValueError("No liquidity provided for this pool")

def get_order_book():
    order_book = defaultdict(lambda: defaultdict(list))

    # Iterate through the orders list and organize the order book
    for order in db["orders"]:
        order_book[order["product"]][order["type"]].append(order)

    # Sort buy and sell orders by price
    for product, order_types in order_book.items():
        order_types["buy"].sort(key=lambda x: x["price"], reverse=True)
        order_types["sell"].sort(key=lambda x: x["price"])

    return order_book

def get_liquidity():
    liquidity = defaultdict(lambda: defaultdict(float))

    for user, user_liquidity in db["liquidity_pools"].items():
        for pair, amounts in user_liquidity.items():
            liquidity[pair]["liquidity_a"] += amounts["amount_a"]
            liquidity[pair]["liquidity_b"] += amounts["amount_b"]

    return liquidity


def get_exchange_rates():
    exchange_rates = defaultdict(float)

    for pair, liquidity in db["liquidity_pools"].items():
        token_a, token_b = pair.split("-")
        rate = liquidity / db["liquidity_pools"][f"{token_b}-{token_a}"]
        exchange_rates[pair] = rate

    return exchange_rates

# API
@app.post("/deposit/")
def deposit_route(input_data: DepositInput, user: str = Depends(get_current_user)):
    deposit(user, input_data.token, input_data.amount)
    return {"detail": "Deposit successful"}


@app.post("/withdraw/")
def withdraw_route(input_data: WithdrawInput, user: str = Depends(get_current_user)):
    try:
        withdraw(user, input_data.token, input_data.amount)
        return {"detail": "Withdrawal successful"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/place_order/")
def place_order_route(input_data: PlaceOrderInput, user: str = Depends(get_current_user)):
    place_order(user, input_data.type, input_data.product, input_data.amount, input_data.price)
    return {"detail": "Order placed"}

@app.get("/balance/")
def balance_route(user: str = Depends(get_current_user)):
    return get_balance(user)

@app.post("/add_liquidity/")
def add_liquidity_route(input_data: AddLiquidityInput, user: str = Depends(get_current_user)):
    try:
        add_liquidity(user, input_data.token_a, input_data.token_b, input_data.amount_a, input_data.amount_b)
        return {"detail": "Liquidity added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/remove_liquidity/")
def remove_liquidity_route(input_data: RemoveLiquidityInput, user: str = Depends(get_current_user)):
    try:
        remove_liquidity(user, input_data.token_a, input_data.token_b)
        return {"detail": "Liquidity removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/order_book/")
def order_book_route():
    return get_order_book()

@app.get("/liquidity/")
def liquidity_route():
    return get_liquidity()


@app.get("/exchange_rates/")
def exchange_rates_route():
    return get_exchange_rates()

@app.get("/exchange_rates/{pair}")
def exchange_rate_route(pair: str):
    token_a, token_b = pair.split("-")
    rate = db["liquidity_pools"][pair] / db["liquidity_pools"][f"{token_b}-{token_a}"]
    return {"pair": pair, "rate": rate}


@app.on_event("startup")
async def startup_event():
    endpoints = []
    for route in app.routes:
        if "GET" in route.methods and route.path != "/":
            endpoints.append(route.path)
    print("Available APIs:", endpoints)


# Usage example
# if authenticate("user1", "password1"):
#     deposit("user1", "BTC", 10)
#     deposit("user1", "ETH", 20)
#     add_order("user1", {'type': 'buy', 'product': 'BTC-ETH', 'amount': 5})
#     process_orders()
#
#     print("Balances:", db['balances'])
# else:
#     print("Authentication failed")

# def execute_trade(buy_order: dict, sell_order: dict):
#     token_a, token_b = buy_order["product"].split("-")
#
#     trade_amount = min(buy_order["amount"], sell_order["amount"])
#     trade_price = (buy_order["price"] + sell_order["price"]) / 2
#
#     db["balances"][buy_order["username"]][token_a] += trade_amount
#     db["balances"][sell_order["username"]][token_b] += trade_amount * trade_price
#
#     buy_order["amount"] -= trade_amount
#     sell_order["amount"] -= trade_amount
#
#     # Return remaining orders or None if fully executed
#     return (
#         buy_order if buy_order["amount"] > 0 else None,
#         sell_order if sell_order["amount"] > 0 else None,
#     )

def execute_trade(buy_order: dict, sell_order: dict):
    token_a, token_b = buy_order["product"].split("-")

    trade_amount = min(buy_order["amount"], sell_order["amount"])
    trade_price = (buy_order["price"] + sell_order["price"]) / 2

    # Check available liquidity in the liquidity pool
    liquidity_a = db["liquidity_pools"][token_a]
    liquidity_b = db["liquidity_pools"][token_b]
    max_trade_amount = min(liquidity_a / trade_price, liquidity_b)

    # Adjust trade amount if it exceeds available liquidity
    if trade_amount > max_trade_amount:
        trade_amount = max_trade_amount
        buy_order["amount"] = max(0, buy_order["amount"] - trade_amount)
        sell_order["amount"] = max(0, sell_order["amount"] - trade_amount)

    # Update balances and liquidity pool
    db["balances"][buy_order["username"]][token_a] += trade_amount
    db["balances"][sell_order["username"]][token_b] += trade_amount * trade_price
    db["liquidity_pools"][token_a] -= trade_amount * trade_price
    db["liquidity_pools"][token_b] -= trade_amount

    # Return remaining orders or None if fully executed
    return (
        buy_order if buy_order["amount"] > 0 else None,
        sell_order if sell_order["amount"] > 0 else None,
    )

def matching_engine():
    while True:
        if db["orders"]:
            current_order = db["orders"].pop(0)

            # Find a matching order in the list
            matched_order = None
            for i, potential_match in enumerate(db["orders"]):
                if (
                        potential_match["product"] == current_order["product"]
                        and potential_match["type"] != current_order["type"]
                ):
                    matched_order = db["orders"].pop(i)
                    break

            # Execute the trade if there's a match
            if matched_order:
                remaining_orders = execute_trade(
                    current_order if current_order["type"] == "buy" else matched_order,
                    current_order if current_order["type"] == "sell" else matched_order,
                )

                # Re-add remaining orders to the list if not fully executed
                for order in remaining_orders:
                    if order:
                        db["orders"].append(order)
            else:
                db["orders"].append(current_order)

        time.sleep(1)  # Check the queue every second


if __name__ == "__main__":
    import uvicorn
    # deposit("admin", "USD", 1000)
    # deposit("admin", "USD", 500)
    # print(get_balance("admin"))
    # add_liquidity("admin", "BTC", "ETH", 100, 100)
    engine_thread = threading.Thread(target=matching_engine)
    engine_thread.start()

    uvicorn.run("main:app", host="127.0.0.1", port=8000)