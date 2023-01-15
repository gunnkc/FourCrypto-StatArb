import backtrader as bt             # Library that streamlines backtesting
import backtrader.feeds as btfeed   # For easier datafeed access
import numpy as np                  # For matrix math in Kalman Filter


# Need further documentation
# Class KalmanFilter allows for a dynamic linear regression model that updates with given observations
class KalmanFilter:
    # Takes in an initial linear line: needs intercept and three coefficients
    def __init__(self, theta_0: list[float]):
        # TODO: Add description of each variable
        self.delta = 1e-4  # Basically magic number
        self.wt = self.delta / (1 - self.delta) * np.eye(4)
        self.vt = 1e-3  # Basically magic number
        self.theta = theta_0
        self.P = np.zeros((4, 4))
        self.R = None
        self.C = np.zeros(4)

    # Uses list of the latest prices to update the coefficients, updates the hedge ratio
    def update_state(self, price: list, hedge: list):
        f = np.asarray([1, price[1], price[2], price[3]])   # Change of state matrix
        y = np.asarray(price[0])                            # Current price of "main" asset - BTC/USD

        if self.R is not None:
            self.R = self.C + self.wt   # Updating the
        else:
            self.R = np.zeros((4, 4))   # Initializing

        y_hat = f @ self.theta
        e_t = y - y_hat
        qt = f @ self.R @ f.T + self.vt
        q_sqrt = np.sqrt(qt)

        at = self.R @ f.T / qt
        self.theta = self.theta + at * e_t
        self.C = self.R - at @ f * self.R

        # updates hedge ratio
        hedge[1] = self.theta[1]
        hedge[2] = self.theta[2]
        hedge[3] = self.theta[3]

        return self.theta[0], q_sqrt   # TODO: Double-check this is the STD


# Class FourCrypto facilitates a statistical arbitrage based on hedge ratios
class FourCrypto(bt.Strategy):
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


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(50000.00)

    data1 = btfeed.YahooFinanceCSVData(
        dataname='/Users/hades/PycharmProjects/fourcryptostatarb/venv/BTC-USD.csv'
    )

    data2 = btfeed.YahooFinanceCSVData(
        dataname='/Users/hades/PycharmProjects/fourcryptostatarb/venv/ETH-USD.csv'
    )

    data3 = btfeed.YahooFinanceCSVData(
        dataname='/Users/hades/PycharmProjects/fourcryptostatarb/venv/LTC-USD.csv'
    )

    data4 = btfeed.YahooFinanceCSVData(
        dataname='/Users/hades/PycharmProjects/fourcryptostatarb/venv/BCH-USD.csv'
    )

    cerebro.adddata(data1)
    cerebro.adddata(data2)
    cerebro.adddata(data3)
    cerebro.adddata(data4)

    cerebro.addstrategy(FourCrypto)
    cerebro.broker.setcommission(0.1)
    cerebro.run()
    print('Final Portfolio Value:', cerebro.broker.getvalue())
