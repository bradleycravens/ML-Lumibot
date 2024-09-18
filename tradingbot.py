from lumibot.brokers import Alpaca  # broker
from lumibot.backtesting import YahooDataBacktesting  # data
from lumibot.strategies.strategy import Strategy  # trading bot
from lumibot.traders import Trader  # deployments
from datetime import datetime
from config import API_KEY, API_SECRET, BASE_URL

ALPACA_CREDS = {"API_KEY": API_KEY, "API_SECRET": API_SECRET, "PAPER": True}


class MLTrader(Strategy):
    def initialize(self, symbol: str = "SPY"):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        pass

    def on_trading_iteration(self):
        if self.last_trade == None:
            order = self.create_order(self.symbol, 10, "buy", type="market")
            self.submit_order(order)
            self.last_trade = "buy"
        pass


start_date = datetime(2024, 6, 14)
end_date = datetime(2024, 6, 30)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name="mlstrat", broker=broker, parameters={"symbol": "SPY"})
strategy.backtest(
    YahooDataBacktesting, start_date, end_date, parameters={"symbol": "SPY"}
)
