from lumibot.brokers import Alpaca  # broker
from lumibot.backtesting import YahooDataBacktesting  # data
from lumibot.strategies.strategy import Strategy  # trading bot
from lumibot.traders import Trader  # deployments
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from config import API_KEY, API_SECRET, BASE_URL
from finbert_utils import estimate_sentiment

ALPACA_CREDS = {"API_KEY": API_KEY, "API_SECRET": API_SECRET, "PAPER": True}


class MLTrader(Strategy):
    def initialize(self, symbol: str = "SPY", cash_at_risk: float = 0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        pass

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime("%Y-%m-%d"), three_days_prior.strftime("%Y-%m-%d")

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        data = self.api.get_news(self.symbol, start=three_days_prior, end=today)

        news = [events.__dict__["_raw"]["headline"] for events in data]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        probability, sentiment = self.get_sentiment()

        if cash > last_price:
            if sentiment == "positive" and probability > 0.95:
                self.place_buy_order(quantity, last_price)
            elif sentiment == "negative" and probability > 0.95:
                self.place_sell_order(last_price)

    def place_buy_order(self, quantity: float, last_price: float):
        order = self.create_order(
            self.symbol,
            quantity,
            "buy",
            type="bracket",
            take_profit_price=last_price * 1.20,
            stop_loss_price=last_price * 0.95,
        )
        self.submit_order(order)

    def place_sell_order(self, last_price: float):
        position = self.get_position(self.symbol)
        if position and position.quantity > 0:
            order = self.create_order(
                self.symbol,
                position.quantity,
                "sell",
                type="bracket",
                take_profit_price=last_price * 0.8,
                stop_loss_price=last_price * 1.05,
            )
            self.submit_order(order)


start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 9, 17)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(
    name="mlstrat", broker=broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5}
)
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk": 0.5},
)
# trader = Trader()
# trader.add_strategy(strategy)
# trader.run_all()
