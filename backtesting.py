"""
This script includes functions and classes
needed to run the backtesting block of the code
"""

import backtrader as bt             # for backtesting the strategies
import numpy as np
import matplotlib.pyplot as plt     # to plot results heatmaps

def backtesting_run(dataframe, start_cash, RSI_fast_param, RSI_slow_param, stop_loss_threshold):
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

        # Stop loss threshold
    stop_loss_th = stop_loss_threshold

    # Add data feed to Cerebro
    data = bt.feeds.PandasData(dataname=dataframe)
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(rsiStrategy,
                    RSI_fast_period=RSI_fast_period, RSI_fast_low_th=RSI_fast_lower_th, RSI_fast_up_th=RSI_fast_upper_th,
                    RSI_slow_period=RSI_slow_period, RSI_slow_low_th=RSI_slow_lower_th, RSI_slow_up_th=RSI_slow_upper_th,
                    stop_loss_th=stop_loss_th)

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


def map_plot_3d(stock_name, db, label_names):

    # Extract data
    x_data = np.asarray(db.iloc[:, 0].values)
    y_data = np.asarray(db.iloc[:, 1].values)
    z_data = np.asarray(db.iloc[:, 2].values)

    # create 2d x,y grid (both X and Y will be 2d)
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    # Sort coordinates and reshape in grid
    idx = np.lexsort((y_data, x_data)).reshape(len(np.unique(x_data)), len(np.unique(y_data)))
    # Plot
    surf = ax.plot_surface(x_data[idx], y_data[idx], z_data[idx], cmap='coolwarm')
    ax.set_xlabel(db.columns[0] +' [-]', fontsize=16)
    ax.set_ylabel(db.columns[1] +' [-]', fontsize=16)
    ax.set_zlabel(db.columns[2] +' [%]', fontsize=16, rotation=90, labelpad=0)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    for t in ax.zaxis.get_major_ticks(): t.label.set_fontsize(14)
    ax.set_title(stock_name + ": Stock sensitivity", fontsize=16)

    plt.show()

#=================================
# Strategy class
#=================================

class rsiStrategy(bt.Strategy):

    def __init__(self, RSI_fast_period = 7 , RSI_fast_low_th = 20, RSI_fast_up_th = 70,
                    RSI_slow_period = 21, RSI_slow_low_th = 40, RSI_slow_up_th = 80,
                    stop_loss_th = 1.00):

        # Initialize the parameters
        self.RSI_fast_period = RSI_fast_period
        self.RSI_fast_low_th = RSI_fast_low_th
        self.RSI_fast_up_th = RSI_fast_up_th
        self.RSI_slow_period = RSI_slow_period
        self.RSI_slow_low_th = RSI_slow_low_th
        self.RSI_slow_up_th = RSI_slow_up_th
        self.stop_loss_percentage = stop_loss_th
        print(self.stop_loss_percentage)
        # Define the strategies
        self.rsi_fast = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.RSI_fast_period)
        self.rsi_slow = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.RSI_slow_period)

        print(RSI_fast_period, RSI_fast_low_th, RSI_slow_up_th)

    def next(self):

        # Buy Conditions
        if not self.position:

            if (self.rsi_fast < self.RSI_fast_low_th and self.rsi_slow < self.RSI_slow_low_th):
                self.buy(size=100)
                self.buy_price = self.data.close[0]
                # print("I buy at " + str(round(self.data.close[0],2)) + " $")

        # Sell Conditions
        else:

             # Sell on RSI high
             if (self.rsi_fast > self.RSI_fast_up_th and self.rsi_slow > self.RSI_slow_up_th):
                self.close(size=100)

             # Sell on stop loss
             loss_gain = (self.data.close[0] - self.buy_price) / self.buy_price
             if loss_gain < - self.stop_loss_percentage:
                 self.close(size=100)
                 #print("Sold thanks to stop loss")
                 # print("I sell at " + str(round(self.data.close[0],2)) + " $")


