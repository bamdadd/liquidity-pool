from collections import defaultdict

from db import db


def deposit(username: str, token: str, amount: float):
    db['balances'][username][token] += amount
    print(username, "Deposited", amount, token, db['balances'][username][token])


def withdraw(username: str, token: str, amount: float):
    if db['balances'][username][token] >= amount:
        db['balances'][username][token] = db['balances'][username][token]- amount
        print(username, "Withdrawed", amount, token, db['balances'][username][token])
    else:
        raise ValueError("Insufficient balance")


def get_balance(username: str):
    # Calculate the total liquidity provided by the user
    total_liquidity = defaultdict(float)
    for pair, amounts in db["liquidity_pools"][username].items():
        token_a, token_b = pair.split("-")
        total_liquidity[token_a] += amounts[0]
        total_liquidity[token_b] += amounts[1]

    # Calculate the total value of each token in the user's balance
    total_value = defaultdict(float)
    for token, amount in db["balances"][username].items():
        total_value[token] = amount + total_liquidity[token]

    return {"balances": db["balances"][username],
            "total_value": total_value,
            "liquidity_pools": total_liquidity}
