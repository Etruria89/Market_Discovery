"""
This script includes functions and classes
needed to run the backtesting block of the code
"""

import backtrader as bt

def backtesting_run(dataframe, start_cash, RSI_fast_param, RSI_slow_param):
    """
    Backtesting function.

    This function instantiate a back-test Cerbero
    and use it to run the back-testing script

    Args:
        dataframe = (pandas.db) formatted pandas db containing the values needed to perform the back-testing
        start_cash = (float) Amount of cash considered at the beginning of the simulation
        RSI_fast_param = [int, float, float] RSI parameters used in the back-testing phase: RSI period, lower buy
                                             threshold, upper sell threshold
        RSI_fast_param = [int, float, float] RSI parameters used in the back-testing phase: RSI period, lower buy
                                     threshold, upper sell threshold
    Return:
        end_portfolio_value = (float) final portfolio value

    """

    # Instantiate Cerebro engine
    cerebro = bt.Cerebro()

    # Unroll the input
        #RSI fast params
    RSI_fast_period = RSI_fast_param[0]
    RSI_fast_lower_th = RSI_fast_param[1]
    RSI_fast_upper_th = RSI_fast_param[2]
        #RSI slow params
    RSI_slow_period = RSI_slow_param[0]
    RSI_slow_lower_th = RSI_slow_param[1]
    RSI_slow_upper_th = RSI_slow_param[2]

    # Add data feed to Cerebro
    data = bt.feeds.PandasData(dataname=dataframe)
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(rsiStrategy,
                    RSI_fast_period=RSI_fast_period, RSI_fast_low_th=RSI_fast_lower_th, RSI_fast_up_th=RSI_fast_upper_th,
                    RSI_slow_period=RSI_slow_period, RSI_slow_low_th=RSI_slow_lower_th, RSI_slow_up_th=RSI_slow_upper_th)

    # Set your desired initial portfolio value
    cerebro.broker.setcash(start_cash)
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Get final portfolio Value
    end_portfolio_value = cerebro.broker.getvalue()


    # Print out the final result
    print('Final Portfolio Value: ${}'.format(end_portfolio_value))

    # Finally plot the end results
    #cerebro.plot(style='candlestick')

    return end_portfolio_value

class rsiStrategy(bt.Strategy):

    def __init__(self, RSI_fast_period = 7 , RSI_fast_low_th = 20, RSI_fast_up_th = 70,
                    RSI_slow_period = 21, RSI_slow_low_th = 40, RSI_slow_up_th = 80):

        # Initialize the parameters
        self.RSI_fast_period = RSI_fast_period
        self.RSI_fast_low_th = RSI_fast_low_th
        self.RSI_fast_up_th = RSI_fast_up_th
        self.RSI_slow_period = RSI_slow_period
        self.RSI_slow_low_th = RSI_slow_low_th
        self.RSI_slow_up_th = RSI_slow_up_th

        # Define the strategies
        self.rsi_fast = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.RSI_fast_period)
        self.rsi_slow = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.RSI_slow_period)

    def next(self):

        if not self.position:

            if self.rsi_fast < self.RSI_fast_low_th and self.rsi_slow < self.RSI_slow_low_th:
                self.buy(size=100)
                # print("I buy at " + str(round(self.data.close[0],2)) + " $")
        else:
             if self.rsi_fast > self.RSI_fast_up_th and self.rsi_slow > self.RSI_slow_up_th:
                self.close(size=100)
                # print("I sell at " + str(round(self.data.close[0],2)) + " $")