import os
from collections import defaultdict



def get_credentials():
    my_dir = os.path.dirname(__file__)
    with open(os.path.join(my_dir, 'credentials.txt'), "r") as f:
        return [tuple(line.strip().split(',')) for line in f.readlines()]

def get_db():
    return {
        'users': get_credentials(),
        'balances': defaultdict(lambda: defaultdict(float)),
        'orders': [],
        'liquidity_pools': defaultdict(lambda: defaultdict(float)),
    }


db = get_db()
def reset_db():
    global db
    db = get_db()
