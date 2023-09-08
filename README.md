# Four Crypto Statistical Arbitrage
Cryptocurrencies are still considered highly volatile. It would be possible to create profit from if the volatility can be captured.
Luckily, cryptocurrencies are highly correlated, which can be used to our advantage. This repository seeks to create a cointegrated portfolio, that trades four correlated crypto in specific amounts to achieve stability & capture profit even in market downturns.

## :warning: Disclaimer
This trading algorithm is for educational purposes only and not intended for real trading or financial advice. The code is provided as-is without any warranty. Use at your own risk. The author is not responsible for any financial losses or other damages caused by the use of this code. Always conduct your own research and consider consulting a financial advisor before engaging in real trading.

## :construction: Under Development
Please note that this project is currently under development. Some features and parts of the code may not be fully functional or might not work as intended. It's possible that the algorithm could produce inaccurate or misleading results. I strongly advise against using this code for real trading or investment purposes at this stage. Use it at your own risk and always verify the results with other sources.

## Usage
After cloning the repo and creating a virtual environment, you could use the repo to backtest or live trading.\
For more information on data format and cointegration, check `\fc-statarb\cointegration\research.ipynb`.\
Depending on what you are doing, the program has different configurations:

### Backtesting
Base : `python3 fc-statarb/main.py --backtest`
- `--traindata path\to\directory`: specifies path to training data
- `--testdata path\to\directory`: specifies path to test data
- `--initial_amount float_number`: specifies initial cash position

### Live Trading
Live trading can both be with paper trading or real trading.\
Base: `python3 fc-statarb/main.py --live`
- `--traindata path\to\directory`: specifies path to training data
- `--credentials path\to\file`: specifies path to Alpaca credentials

## Strategy
There are three parts to the strategy:
1. Cointegration & Initial Value
2. Kalman Filter
3. Trading on Hedge Ratio

Basically, we obtain initial values for hedge ratio (done only once), then dynamically adjust it using Kalman Filter, and trade on the adjusted ratio.

### Cointegation
The cointegration is done by taking advantage of correlation.
We use Engle-Granger 2-Step process to get the initial value, but Johansen test would suffice as well.
Engle-Granger was chosen as it seems to focus more on correlation and stability, 
as opposed to the Johansen test being more inherently mean reverting.
OLS is performed, and then its mean reversion is testing in ADF.
Based on this [paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3235890)

### Kalman Filter
The addtion of Kalman Filter functions as making the whole process as a dynamic linear regression.
It constructs two Gaussian blobs: one to model the uncertainty in the state we are trying to predict (the hedge ratio),
and another to model the uncertainty in our measurement (the spot price). Since both blobs have a mean and variance,
we can look at their intersection to find the most likely prediction of the state. We can extract out the mean and variance
of the intersection, which we can use as trading signals.
The filter was constructed based on this [article](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/).


## Broker & Implementation
I primarily used BackTrader since I couldn't find a trustworthy broker that allows shorting cryptos.
It is possible to implement your own LiveTrader to allow for shorting through CEX like Binance;
You might want to do this since my implementation (Alpaca) doesn't allow shorting of cryptocurrencies.

As for trading signals, we can calculate the spread using hedge ratios and spot prices. Then we can construct an upper and lower boundary,
using mean and the standard deviation we extracted from our Kalman Filter. The current model uses one STD away from mean as the boundaries.
We enter the long position when the spread is below the lower bound, and exit when spread is above the upper bound.
For short position, the bounds we use for entry and exit are flipped.

It's also important to note we are only exposed to one unit of spread at a time, as to limit risk exposure.
I also added a tail hedge to further limit risk.

## Contact
[Gunn Chun](https://www.linkedin.com/in/gunn-k-chun/)
<mailto: gunncre@gmail.com>
