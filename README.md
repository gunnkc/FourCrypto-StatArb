# Four Crypto Statistical Arbitrage
Cryptocurrencies are still considered highly volatile. It would be possible to create profit from if the volatility can be captured.
Luckily, cryptocurrencies are highly correlated, which can be used to our advantage. This repository seeks to create a cointegrated portfolio,
that trades four correlated crypto in specific amounts to achieve stability & capture profit even in market downturns.

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
Based on this paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3235890

### Kalman Filter
The addtion of Kalman Filter functions as making the whole process as a dynamic linear regression.
It constructs two Gaussian blobs: one to model the uncertainty in the state we are trying to predict (the hedge ratio),
and another to model the uncertainty in our measurement (the spot price). Since both blobs have a mean and variance,
we can look at their intersection to find the most likely prediction of the state. We can extract out the mean and variance
of the intersection, which we can use as trading signals.
The filter was constructed based on this article: https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/


## Broker & Implementation
I used BackTrader since I couldn't find a trustworthy broker that allows shorting cryptos.

As for trading signals, we can calculate the spread using hedge ratios and spot prices. Then we can construct an upper and lower boundary,
using mean and the standard deviation we extracted from our Kalman Filter. The current model uses one STD away from mean as the boundaries.
We enter the long position when the spread is below the lower bound, and exit when spread is above the upper bound.
For short position, the bounds we use for entry and exit are flipped.

It's also important to note we are only exposed to one unit of spread at a time, as to limit risk exposure.
I also added a tail hedge to further limit risk.

## TODO
- [ ] Fix STD value returned by Kalman Filter
