import alpaca_trade_api as alpaca
import requests
import asyncio

from kalman_filter import KalmanFilter

ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'
DATA_URL = 'https://data.alpaca.markets'


"""
Square away the async code -- not sure if currently functional
"""

class LiveTrader:

    def __init__(self, keys: list[str], initial: dict) -> None:
        self.api = alpaca.REST()
        self.headers = {'APCA-API-KEY-ID': keys[0],
                        'APCA-API-SECRET-KEY': keys[1]}
        
        self.loop = asyncio.get_event_loop()
        self.hedge = []
        self.kalman = KalmanFilter(initial['spread'])

        self.hedgeMean = initial['mean']
        self.hedgeSig = initial['std']

        self.sigMod = 1
        self.tail = 3
        self.entry = lambda x: self.hedgeMean - x * self.hedgeSig
        self.exits = lambda x: self.hedgeMean + x * self.hedgeSig

        self.cryptos = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD']
        self.prices = [0, 0, 0, 0]
        self.position = None


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

        self.get_position()
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

    
    def buy_spread(self):
        """
        Takes long position in spread
        """
        for index, qty in enumerate(self.hedge):
            if qty > 0:
                self.post_order(self.cryptos[index], qty, 'buy')
            else:
                self.post_order(self.cryptos[index], -qty, 'buy')

    def sell_spread(self):
        """
        Takes short position in spread -- not properly supported by Alpaca
        """
        for index, qty in enumerate(self.hedge):
            if qty > 0:
                self.post_order(self.cryptos[index], qty, 'sell')
            else:
                self.post_order(self.cryptos[index], -qty, 'sell')
    

    def get_position(self):
        try:
            order = requests.get(
                f'{ALPACA_BASE_URL}/v2/positions', headers=self.headers
            )
            self.position = order

        except Exception as e:
            print(f'There was an issue getting positions from Alpaca: {e}')
            return False


    async def get_quote(self, symbol: str):
        try:
            quote = requests.get(f'{DATA_URL}/v1beta2/crypto/latest/trades?symbols={symbol}', headers=self.headers)
            self.prices[symbol] = quote.json()['trades'][symbol]['p']

            if quote.status_code != 200:
                print(f'Undesirable response from Alpaca! {quote.json()}')
                return False
 
        except Exception as e:
            print(f'There was an issue getting trade quote from Alpaca: {e}')
            return False


    def post_order(self, symbol: str, qty: float, side: str):
        try:
            order = requests.post(
                f'{ALPACA_BASE_URL}/v2/orders', headers=self.headers, json={
                    'symbol': symbol,
                    'qty': qty,
                    'side': side,
                    'type': 'market',
                    'time_in_force': 'gtc',
                })
            return order
        
        except Exception as e:
            print(f'There was an issue posting order to Alpaca: {e}')
            return False


    def liquidate(self, symbol: str):
        try:
            order = requests.delete(
                f'{ALPACA_BASE_URL}/v2/positions/', headers=self.headers
            )
            return order

        except Exception as e:
            print(f'There was an issue liquidating: {e}')
            return False
