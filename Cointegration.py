import pandas as pd
import matplotlib.pyplot as plt

import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller

cryptos = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'BCHUSD']

pds = [pd.read_csv('BTC-USD.csv'), pd.read_csv('ETH-USD.csv'), pd.read_csv('LTC-USD.csv'), pd.read_csv('BCH-USD.csv')]


def compile_close(close_data):
    for index, crypto in enumerate(cryptos):
        close_data[crypto] = pds[index].pop('Adj Close')


def log_plot(close_data):
    plt.rcParams['figure.figsize'] = (12, 7)
    plt.plot(close_data['BTCUSD'], color='red')
    plt.plot(close_data['ETHUSD'], color='orange')
    plt.plot(close_data['LTCUSD'], color='yellow')
    plt.plot(close_data['BCHUSD'], color='green')
    plt.yscale('log')
    plt.show()


def calculate_hedge(close_data):
    x = close_data[['ETHUSD', 'LTCUSD', 'BCHUSD']]
    x = sm.add_constant(x)
    y = close_data['BTCUSD']
    est = sm.OLS(y, x).fit()
    return list(est.params)


def CADF(close_data, params):
    spread = close_data['BTCUSD'] + params[1] * close_data['ETHUSD'] + \
             params[2] * close_data['LTCUSD'] + params[3] * close_data['BCHUSD']
    adf = adfuller(spread, maxlag=1)
    print('Critical value = %s' % (adf[0]))
    print(adf)

    ax = spread.plot(figsize=(12,6), title='Crypto Spread')
    ax.set_ylabel('Value in $')
    ax.grid(True)

    print('Spread mean = %s' % (spread.mean()))
    print('Spread STD = %s' % (spread.std()))


def run():
    close = pd.DataFrame()
    compile_close(close)
    log_plot(close)
    hedge = calculate_hedge(close)
    print(hedge)
    CADF(close, hedge)


if __name__ == '__main__':
    run()
