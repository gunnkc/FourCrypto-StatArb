import alpaca_trade_api as alpaca
import requests
import asyncio

from kalman_filter import KalmanFilter

ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'
DATA_URL = 'https://data.alpaca.markets'


class LiveTrader():

    def __init__(self, keys: list[str]) -> None:
        self.api = alpaca.REST()
        self.headers = {'APCA-API-KEY-ID': keys[0],
                        'APCA-API-SECRET-KEY': keys[1]}
        
        self.loop = asyncio.get_event_loop()

        self.initial = [4612.39, 7.15, -65.79, 76.14]
        self.kalman = KalmanFilter(self.initial)

        self.hedgeMean = 31841.09
        self.hedgeSig = 3078.75

        self.sigMod = 1
        self.tail = 3
        self.entry = lambda x: self.hedgeMean - x * self.hedgeSig
        self.exits = lambda x: self.hedgeMean + x * self.hedgeSig

        self.cryptos = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD']
        self.prices = [0, 0, 0, 0]


    def run(self) -> None:
        self.loop.run_until_complete(self.main())
        self.loop.close()
    

    async def main(self):
        quotes = [self.get_quote(symbol) for symbol in self.cryptos]
        tasks = [self.loop.create_task() for quote in quotes]

        await asyncio.wait(tasks)
        await self.check_arb()
    


    async def check_arb(self):
        self.hedgeMean, self.hedgeSig = self.kalman.update_state(self.prices, self.hedge)

        spread = 0
        for i, val in enumerate(self.hedge):
            spread = spread + val * self.prices[i]

        if self.position and self.pos is None:  # Don't want to integrate self.position; can't implement in Alpaca
            raise Exception('Anomalous position')

        if self.pos == 'short' and spread <= self.entry(self.tail):      # Tail hedge for lower boundary
            self.liquidate()
            self.pos = None

        elif self.pos == 'Long' and spread >= self.exits(self.tail):     # Tail hedge for upper boundary
            self.liquidate()
            self.pos = None

        elif self.pos == 'Long' and spread >= self.exits(self.sigMod):   # Liquidate long position
            self.liquidate()
            self.pos = None
            print('exit long')

        elif self.pos == 'Short' and spread <= self.entry(self.sigMod):  # Liquidate short position
            self.liquidate()
            self.pos = None
            print('exit short')

        elif self.pos is None and spread <= self.entry(self.sigMod):     # Enter long position
            self.buy_spread()
            self.pos = 'Long'
            print('enter long')

        elif self.pos is None and spread >= self.exits(self.sigMod):     # Enter short position
            self.sell_spread()
            self.pos = 'Short'
            print('enter short')
    

    def get_position(self):
        pass


    async def get_quote(self, symbol: str):
        pass


    def post_order(self, symbol: str):
        pass


    def liquidate(self, symbol: str):
        pass
