from typing import List, Dict, Tuple, Any

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller

CRYPTOS = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'BCHUSD']

def cointegrate(filepaths: List(str)) -> Dict[str, Any]:
    """
    Takes provided data path to read the data, cointegrate the assets, then returns test results.
    """
    if len(filepaths) != 4:
        raise ValueError(f"Cointegration requires 4 CSV files -- only {len(filepaths)} provided")
    
    pds = []
    for file in filepaths:
        pds.append(pd.read_csv(file))
    
    close_data = compile_close(pds)
    hedge = calculate_hedge(close_data)
    mean, std, passes = CADF(close_data, hedge)

    spread_dict = {
        "mean" : mean,
        "std" : std,
        "passes_adf" : passes,
        "spread": hedge[:4]
    }

    return spread_dict


def compile_close(raw_pds: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Creates a Pandas dataframe of closing prices based on Yahoo Finance OHLC CSV.
    """
    close_data = pd.DataFrame()
    for index, crypto in enumerate(CRYPTOS):
        close_data[crypto] = raw_pds[index].pop('Adj Close')
    return close_data


def calculate_hedge(close_data: pd.DataFrame) -> List[float]:
    """
    Runs Ordinary Linear Regression on closing prices.

    :return: estimated parameters of the closing prices
    """
    x = close_data[['ETHUSD', 'LTCUSD', 'BCHUSD']]
    x = sm.add_constant(x)
    y = close_data['BTCUSD']
    est = OLS(y, x).fit()
    return list(est.params)


def CADF(close_data, params) -> Tuple[float, float, bool]:
    """
    Creates spread and  runs Cointegrated Augmented Dickey-Fuller (CADF) Test against it.

    :return: tuple of spread's parameters (mean and standard deviation) and boolean of whether it passes the test
    """
    spread = close_data['BTCUSD'] + params[1] * close_data['ETHUSD'] + \
            params[2] * close_data['LTCUSD'] + params[3] * close_data['BCHUSD']
    
    adf = adfuller(spread, maxlag=1)
    passes_adf = all(adf[0] < critical for critical in adf[4])

    return (spread.mean(),  spread.std(), passes_adf)