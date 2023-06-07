import numpy as np  # For matrix math in Kalman Filter

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

        return self.theta[0], q_sqrt
        # std of error not the spread