from unittest import TestCase

from account import get_balance, deposit, withdraw
from main import add_liquidity, remove_liquidity


class DepositAndWithdrawalTest(TestCase):
    def test_balance_should_be_zero_to_start(self):
        balance = get_balance("test")
        self.assertEqual(balance["balances"], {})
        self.assertEqual(balance["total_value"], {})
        self.assertEqual(balance["liquidity_pools"], {})

    def test_deposit_200GBP_withdraw100GBP(self):
        deposit("test", "GBP", 200)
        deposit("test", "USD", 120)
        withdraw("test", "GBP", 100)
        balance = get_balance("test")
        self.assertEqual({'GBP': 100.0, 'USD': 120.0}, balance["balances"])
        self.assertEqual({'GBP': 100.0, 'USD': 120.0}, balance["total_value"])
        self.assertEqual({'GBP': 0,
                          'USD': 0}, balance["liquidity_pools"])

        add_liquidity("test", "GBP", "USD", 100, 120)
        balance = get_balance("test")
        self.assertEqual({'GBP': 0.0, 'USD': 0.0}, balance["balances"])
        self.assertEqual({'GBP': 100.0, 'USD': 120.0}, balance["total_value"])
        self.assertEqual({'GBP': 100,
                          'USD': 120}, balance["liquidity_pools"])

        remove_liquidity("test", "GBP", "USD")
        balance = get_balance("test")
        self.assertEqual({'GBP': 100.0, 'USD': 120.0}, balance["balances"])
        self.assertEqual({'GBP': 100.0, 'USD': 120.0}, balance["total_value"])
        self.assertEqual({'GBP': 0,
                          'USD': 0}, balance["liquidity_pools"])

