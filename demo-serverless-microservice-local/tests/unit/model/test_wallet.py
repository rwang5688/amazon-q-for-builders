import unittest
import sys
sys.path.append(".")

import boto3
from ewallet.model.wallet import Wallet
from ewallet.model.transaction import TransactionType, TransactionStatus

class WalletTest(unittest.TestCase):

    def test_wallet_creation(self):
        wallet = Wallet('test_wallet')
        self.assertDictEqual(wallet.balance, {})
        self.assertCountEqual(wallet.transactions, [])
        self.assertEqual(wallet.id, None)
        self.assertEqual(wallet.name, 'test_wallet')

    def test_transfer(self):
        origin_wallet = Wallet('test_wallet')
        destination_wallet = Wallet('test_wallet_2')
        dollar_top_up_transaction = origin_wallet.add_transaction(100, 'USD', TransactionType.TOP_UP)
        euro_top_up_transaction = origin_wallet.add_transaction(300, 'EUR', TransactionType.TOP_UP)

        (origin_transaction, destination_transaction) = origin_wallet.transfer(50, 'USD', destination_wallet)
        self.assertEqual(origin_transaction.amount, -50)
        self.assertEqual(origin_transaction.currency, 'USD')
        self.assertEqual(origin_transaction.type, TransactionType.TRANSFER)
        self.assertEqual(origin_transaction.wallet, origin_wallet)
        self.assertIsNone(origin_transaction.id)
        self.assertEqual(origin_transaction.status, TransactionStatus.PENDING)

        self.assertEqual(destination_transaction.amount, 50)
        self.assertEqual(destination_transaction.currency, 'USD')
        self.assertEqual(destination_transaction.type, TransactionType.TRANSFER)
        self.assertEqual(destination_transaction.wallet, destination_wallet)
        self.assertIsNone(destination_transaction.id)
        self.assertEqual(destination_transaction.status, TransactionStatus.PENDING)

        self.assertDictEqual(origin_wallet.balance, {'USD': 50, 'EUR': 300})
        self.assertEqual(
            origin_wallet.transactions, 
            [dollar_top_up_transaction, 
             euro_top_up_transaction, 
             origin_transaction])
        self.assertDictEqual(destination_wallet.balance, {'USD': 50})
        self.assertEqual(destination_wallet.transactions, [destination_transaction])

    def test_add_transaction_invalid_currency_code(self):
        wallet = Wallet('test_wallet')
        invalid_currency_code = 'XYZ'

        with self.assertRaises(Exception):
            wallet.add_transaction(100, invalid_currency_code)

        self.assertDictEqual(wallet.balance, {})
        self.assertEqual(wallet.transactions, [])

    def test_withdraw(self):
        wallet = Wallet('test_wallet')
        dollar_top_up_transaction = wallet.add_transaction(100, 'USD', TransactionType.TOP_UP)
        euro_top_up_transaction = wallet.add_transaction(300, 'EUR', TransactionType.TOP_UP)

        dollar_withdrawal_transaction = wallet.withdraw(50, 'USD')
        self.assertEqual(dollar_withdrawal_transaction.amount, -50)
        self.assertEqual(dollar_withdrawal_transaction.currency, 'USD')
        self.assertEqual(dollar_withdrawal_transaction.type, TransactionType.WITHDRAWAL)
        self.assertEqual(dollar_withdrawal_transaction.wallet, wallet)
        self.assertIsNone(dollar_withdrawal_transaction.id)
        self.assertEqual(dollar_withdrawal_transaction.status, TransactionStatus.PENDING)

        euro_withdrawal_transaction = wallet.withdraw(100, 'EUR')
        self.assertEqual(euro_withdrawal_transaction.amount, -100)
        self.assertEqual(euro_withdrawal_transaction.currency, 'EUR')
        self.assertEqual(euro_withdrawal_transaction.type, TransactionType.WITHDRAWAL)
        self.assertEqual(euro_withdrawal_transaction.wallet, wallet)
        self.assertIsNone(euro_withdrawal_transaction.id)
        self.assertEqual(euro_withdrawal_transaction.status, TransactionStatus.PENDING)

        self.assertDictEqual(wallet.balance, {'USD': 50, 'EUR': 200})
        self.assertEqual(wallet.transactions, 
                         [dollar_top_up_transaction, 
                          euro_top_up_transaction, 
                          dollar_withdrawal_transaction, 
                          euro_withdrawal_transaction]
                        )

    def test_withdraw_not_enough_funds(self):
        wallet = Wallet('test_wallet')
        dollar_top_up_transaction = wallet.add_transaction(100, 'USD', TransactionType.TOP_UP)
        euro_top_up_transaction = wallet.add_transaction(300, 'EUR', TransactionType.TOP_UP)

        with self.assertRaises(Exception):
            wallet.withdraw(150, 'USD')

        self.assertDictEqual(wallet.balance, {'USD': 100, 'EUR': 300})
        self.assertEqual(wallet.transactions, [dollar_top_up_transaction, euro_top_up_transaction])

    def test_top_up(self):
        wallet = Wallet('test_wallet')

        dollar_top_up_transaction = wallet.top_up(100, 'USD')
        self.assertEqual(dollar_top_up_transaction.amount, 100)
        self.assertEqual(dollar_top_up_transaction.currency, 'USD')
        self.assertEqual(dollar_top_up_transaction.type, TransactionType.TOP_UP)
        self.assertEqual(dollar_top_up_transaction.wallet, wallet)
        self.assertIsNone(dollar_top_up_transaction.id)
        self.assertEqual(dollar_top_up_transaction.status, TransactionStatus.PENDING)

        euro_top_up_transaction = wallet.top_up(300, 'EUR')
        self.assertEqual(euro_top_up_transaction.amount, 300)
        self.assertEqual(euro_top_up_transaction.currency, 'EUR')
        self.assertEqual(euro_top_up_transaction.type, TransactionType.TOP_UP)
        self.assertEqual(euro_top_up_transaction.wallet, wallet)
        self.assertIsNone(euro_top_up_transaction.id)
        self.assertEqual(euro_top_up_transaction.status, TransactionStatus.PENDING)

        self.assertDictEqual(wallet.balance, {'USD': 100, 'EUR': 300})
        self.assertEqual(wallet.transactions, [dollar_top_up_transaction, euro_top_up_transaction])

    def test_list_balance(self):
        wallet = Wallet('test_wallet')
        wallet.add_transaction(100, 'USD', TransactionType.TOP_UP)
        wallet.add_transaction(300, 'EUR', TransactionType.TOP_UP)
        wallet.add_transaction(50, 'GBP', TransactionType.TOP_UP)
        wallet.withdraw(50, 'GBP')

        balance = wallet.list_balance()

        self.assertListEqual(balance, ['USD 100.00', 'EUR 300.00', 'GBP 0.00'])