import unittest
from collections import deque

from liquidity_provider import LiquidityProvider
from market_simulator import MarketSimulator
from order_book import OrderBook
from order_manager import OrderManager
from trading_strategy import TradingStrategy


class TestTradingSimulation(unittest.TestCase):
    def setUp(self):
        self.lp_2_gateway = deque()
        self.ob_2_ts = deque()
        self.ts_2_om = deque()
        self.ms_2_om = deque()
        self.om_2_ts = deque()
        self.gw_2_om = deque()
        self.om_2_gw = deque()

        self.liquidityProvider = LiquidityProvider(self.lp_2_gateway)
        self.bookBuilder = OrderBook(self.lp_2_gateway, self.ob_2_ts)
        self.tradingStrategy = TradingStrategy(self.ob_2_ts, self.ts_2_om, self.om_2_ts)
        self.marketSimulator = MarketSimulator(self.om_2_gw, self.gw_2_om)
        self.orderManager = OrderManager(self.ts_2_om, self.om_2_ts, self.om_2_gw, self.gw_2_om)

    def test_add_liquidity(self):
        # Order sent from the exchange to the trading system
        order1 = {
            'id': 1,
            'price': 219,
            'quantity': 10,
            'side': 'bid',
            'action': 'new'
        }

        # Add Order from Gateway
        self.liquidityProvider.insert_manual_order(order1)
        self.assertEqual(len(self.lp_2_gateway), 1)

        # Book Builder
        self.bookBuilder.handle_order_from_gateway()
        self.assertEqual(len(self.ob_2_ts), 1)

        # Trading Strategy
        self.tradingStrategy.handle_input_from_bb()
        self.assertEqual(len(self.ts_2_om), 0)

        # Second Order
        order2 = {
            'id': 2,
            'price': 218,
            'quantity': 10,
            'side': 'ask',
            'action': 'new'
        }
        self.liquidityProvider.insert_manual_order(order2.copy())
        self.assertEqual(len(self.lp_2_gateway), 1)

        self.bookBuilder.handle_order_from_gateway()
        self.assertEqual(len(self.ob_2_ts), 1)

        self.tradingStrategy.handle_input_from_bb()
        self.assertEqual(len(self.ts_2_om), 2)

        self.orderManager.handle_input_from_ts()
        self.assertEqual(len(self.ts_2_om), 1)
        self.assertEqual(len(self.om_2_gw), 1)

        self.orderManager.handle_input_from_ts()
        self.assertEqual(len(self.ts_2_om), 0)
        self.assertEqual(len(self.om_2_gw), 2)

        self.marketSimulator.handle_order_from_gw()
        self.assertEqual(len(self.gw_2_om), 1)

        self.marketSimulator.handle_order_from_gw()
        self.assertEqual(len(self.gw_2_om), 2)

        self.orderManager.handle_input_from_market()
        self.orderManager.handle_input_from_market()
        self.assertEqual(len(self.om_2_ts), 2)

        self.tradingStrategy.handle_response_from_om()
        self.assertEqual(self.tradingStrategy.get_pnl(), 0)

        self.marketSimulator.fill_all_orders()
        self.assertEqual(len(self.gw_2_om), 2)

        self.orderManager.handle_input_from_market()
        self.orderManager.handle_input_from_market()
        self.assertEqual(len(self.om_2_ts), 3)

        self.tradingStrategy.handle_response_from_om()
        self.assertEqual(len(self.om_2_ts), 2)

        self.tradingStrategy.handle_response_from_om()
        self.assertEqual(len(self.om_2_ts), 1)

        self.tradingStrategy.handle_response_from_om()
        self.assertEqual(len(self.om_2_ts), 0)
        self.assertEqual(self.tradingStrategy.get_pnl(), 10)
