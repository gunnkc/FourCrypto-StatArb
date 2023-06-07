import backtrader as bt             # Library that streamlines backtesting
import backtrader.feeds as btfeed   # For easier datafeed access
import os 

from kalman_filter import KalmanFilter

# Class FourCrypto facilitates a statistical arbitrage based on hedge ratios
class BackTrader(bt.Strategy):

    def __init__(self):
        self.pos = None
        self.hedge = [1.0, 0.0, 0.0, 0.0]
        self.initial = [4612.39, 7.15, -65.79, 76.14]  # Calculated from backtest data - DOES NOT PASS CADF
        self.mod = 1  # Coefficient that modifies purchase size
        self.kalman = KalmanFilter(self.initial)

        # Mean & Standard deviation of spread - used for trading signal
        # both values match the timeframe of 10/10/22 - 12/30/22
        self.hedgeMean = 31841.09
        self.hedgeSig = 3078.75  # STD not being updated fast enough

        # Calculating entry/exit thresholds in terms of STD
        self.sigMod = 1
        self.tail = 3
        self.entry = lambda x: self.hedgeMean - x * self.hedgeSig
        self.exits = lambda x: self.hedgeMean + x * self.hedgeSig

        self.cryptos = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD']
        self.prices = [0, 0, 0, 0]

    # Function required by BackTrader, contains trading logic
    def next(self):
        for index in range(4):
            self.prices[index] = self.datas[index][0]
        # print(self.hedge)
        self.check_arb()

    # Function that contains arbitrage logic; captures mean-reversion on cointegrated portfolio
    # Important to note that it does not have stop loss or trailing stop; relies on logic entirely
    def check_arb(self):
        # the STD is too low; the Kalman Filter is not working as intended
        self.hedgeMean, self.hedgeSig = self.kalman.update_state(self.prices, self.hedge)

        spread = 0
        for i, val in enumerate(self.hedge):
            spread = spread + val * self.prices[i]  # Calculating current spread price

        if self.position and self.pos is None:  # Don't want to integrate self.position; can't implement in Alpaca
            raise Exception('Anomalous position')   # Something is wrong with position - keeps throwing this exception

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

    # Functions that facilitates going long on the spread
    def buy_spread(self):
        for index, value in enumerate(self.hedge):
            if value > 0:    # Buying assets with positive hedge coefficient
                self.buy(
                    data=self.datas[index],
                    size=(self.mod * value),
                    exectype=bt.Order.Market
                )
            elif value < 0:  # Shorting assets with negative hedge coefficient
                self.sell(
                    data=self.datas[index],
                    size=abs(self.mod * value),
                    exectype=bt.Order.Market
                )

    # Function that facilitates going short on the spread
    def sell_spread(self):
        for index, value in enumerate(self.hedge):
            if value > 0:    # Shorting assets with positive hedge coefficient
                self.sell(
                    data=self.datas[index],
                    size=abs(self.mod * value),
                    exectype=bt.Order.Market
                )
            elif value < 0:  # Buying assets with negative hedge coefficient
                self.buy(
                    data=self.datas[index],
                    size=(self.mod * value),
                    exectype=bt.Order.Market
                )
    

    # Function that closes all positions
    def liquidate(self):
        for index, value in enumerate(self.hedge):
            self.close(
                data=self.datas[index]
            )
    

    def load_data(self, cerebro: bt.Cerebro, filepath: str):
        files = [file for file in os.listdir(filepath) if file.endswith('.csv')]

        for file in files:
            try:
                cerebro.adddata(file)

            except:
                print(f'Unrecognized file: {file}')


    def run(self, dirpath: str, initial: float):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(initial)
        self.load_data(dirpath)

        cerebro.addstrategy(BackTrader)
        cerebro.broker.setcommission(0.1)

        cerebro.run()

        print('Final Portfolio Value:', cerebro.broker.getvalue())
    