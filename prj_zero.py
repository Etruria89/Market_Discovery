#IMPORT MODULES
import pandas as pd
import pandas_datareader as pdr
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import yfinance as yf


yf.pdr_override()

#PERIODO DI OSSERVAZIONE
start_time = datetime.datetime(2020, 1, 1)
end_time = datetime.datetime.today()

# Variables for moving average
window_short = 7
window_long = 21

# Variable initialization
all_stocks = pdr.nasdaq_trader.get_nasdaq_symbols()
stocks = all_stocks['NASDAQ Symbol']
data = {}
table = {}
tick = []
_test = False
_read = True
_filter_list = False
signal = 'RSI'
_save = False
buy_rsi_th = 30
sell_rsi_sell_th = 75
sell_rsi_buy_th = 30
list_filter_name = 'Revolut_Stocks_List.csv'

# plot trigger
_plot = False

# starting timer
start_it = time.time()

# Extra info extraction
info_arr = ["sector", "industry", "marketCap"]

# Define tickers
if _test:

    tick = ['AAPL', 'AMZN']

else:

    info_df = pd.DataFrame(columns=["tick"] + info_arr)

    for stk, stock in all_stocks.iterrows():
        print('Check if eligible...', stk, stock['Security Name'], time.time() - start_it)
        if stock['Financial Status'] == 'N' and stock['Listing Exchange'] == 'Q' and stock['ETF'] == False:
            tmp_stock = yf.Ticker(stk)
            info_tmp = [stk]
            #for req_info in info_arr:
             #   try:
              #      info_tmp.append(tmp_stock.info[req_info])
               # except:
                #    info_tmp.append("N.A.")
            #info_df.loc[-1] = info_tmp
            tick.append(stk)

# Read data
if _read:
    # read data and save to .csv
    df = yf.download(  # or pdr.get_data_yahoo(...
            tickers=tick,
            period="5y",
            interval="1d",
            group_by='ticker',
            auto_adjust=True,
            prepost=True,
            threads=1,
            proxy=None)

    print('end Reading', time.time()-start_it)
    df.to_csv('ticker.csv')
else:
    # Read from .csv
    df = pd.read_csv('ticker.csv', header=[0, 1])
    df.drop([0], axis=0, inplace=True)  # drop this row because it only has one column with Date in it
    df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')] = pd.to_datetime(df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')], format='%Y-%m-%d')  # convert the first column to a datetime
    df.set_index(('Unnamed: 0_level_0', 'Unnamed: 0_level_1'), inplace=True)  # set the first column as the index
    df.index.name = None  # rename the index
data = {idx: gp.xs(idx, level=0, axis=1) for idx, gp in df.groupby(level=0, axis=1)}


# Data processing
if _filter_list:
    # Revo_DB
    revo_db = pd.read_csv(list_filter_name, header=[0, 1])
    revo_tick_lol = revo_db["Symbol"][:].values.tolist()
    tick = [item for sublist in revo_tick_lol for item in sublist]

for stk in tick:

    try:
        print('    Processing...', stk, all_stocks['Security Name'][stk], time.time()-start_it)
        if len(data[stk].index) > window_long:

            # Price percentage change
            data[stk]['diff_p'] = data[stk]['Close'].pct_change()
            delta = data[stk]['diff_p']

            # Indicators
                # MA
            data[stk]['mean_short'] = data[stk]['Close'].rolling(window=window_short).mean()
            data[stk]['mean_long'] = data[stk]['Close'].rolling(window=window_long).mean()
                # RSI
            up_days = delta.copy()
            up_days[delta <= 0] = 0.0
            down_days = abs(delta.copy())
            down_days[delta > 0] = 0.0
            RS_up = up_days.rolling(window_long).mean()
            RS_down = down_days.rolling(window_long).mean()
            data[stk]['rsi'] = 100.0 - 100.0 / (1.0 + RS_up / RS_down)

            # VOLATILITA'
            #data[stk]['vol_7']= data[stk]['diff_p'].rolling(7).std() * np.sqrt(7)
            #data[stk]['vol_14']= data[stk]['diff_p'].rolling(14).std() * np.sqrt(14)
            #data[stk]['vol_21']= data[stk]['diff_p'].rolling(21).std() * np.sqrt(21)

            #data[stk]['cumprod']=(1+data[stk]['diff_p']).cumprod()

            # Strategy
            data[stk]['signal'] = 0.0
            if signal == 'mean':
                data[stk]['signal'][window_long:] = np.where(data[stk]['mean_short'][window_long:] > data[stk]['mean_long'][window_long:], 1.0, 0.0)
                data[stk]['positions'] = data[stk]['signal'].diff()
            elif signal == 'RSI':
                data[stk]['signal_sell'] = (data[stk]['rsi'] > sell_rsi_sell_th) & (data[stk]['rsi'].shift(1) <= sell_rsi_sell_th)
                data[stk]['signal_buy'] = (data[stk]['rsi'] < sell_rsi_buy_th) & (data[stk]['rsi'].shift(1) >= sell_rsi_buy_th)
                data[stk]['positions'] = data[stk]['signal_sell'].astype(int) - data[stk]['signal_buy'].astype(int)

            if  data[stk]['positions'][len(data[stk].index)-1] == 1:
                table[stk] = all_stocks['Security Name'][stk]
            #PLOT
            if _plot:
                fig = plt.figure() # Mean
                # Add a subplot and label for y-axis
                ax1 = fig.add_subplot(111,  ylabel='Price [$]')
                # Plot the closing price
                #data[stk]['Adj Close'].plot(ax=ax1, color='r', lw=2.)
                # Plot the short and long moving averages
                data[stk][['mean_short', 'mean_long']].plot(ax=ax1, lw=2.)
                # Add the title
                plt.title(stk + " MAs")
                if signal == 'mean':
                    # Plot the buy signals
                    ax1.plot(data[stk].loc[data[stk]['positions'] == 1.0].index,
                             data[stk]['mean_short'][data[stk]['positions'] == 1.0],
                             '^', markersize=10, color='m')
                    # Plot the sell signals
                    ax1.plot(data[stk].loc[data[stk]['positions'] == -1.0].index,
                             data[stk]['mean_short'][data[stk]['positions'] == -1.0],
                             'v', markersize=10, color='k')

                # Plot RSI
                fig_rsi = plt.figure("RSI") # RSI
                ax_rsi = fig_rsi.add_subplot(111, ylabel='RSI [%]')
                data[stk][['rsi']].plot(ax=ax_rsi)
                # Add the title
                plt.title(stk + " RSI plot")
                if signal == 'RSI':
                    # Plot the buy signals
                    ax_rsi.plot(data[stk].loc[data[stk]['positions'] == 1.0].index,
                             data[stk]['rsi'][data[stk]['positions'] == 1.0],
                             '^', markersize=10, color='m')
                    # Plot the sell signals
                    ax_rsi.plot(data[stk].loc[data[stk]['positions'] == -1.0].index,
                             data[stk]['rsi'][data[stk]['positions'] == -1.0],
                             'v', markersize=10, color='k')

                # Show the plot for the first stock
                plt.show()

            #EARNINGS
            data[stk]['portfolio'] = 1 * data[stk]['signal'].shift(1)
            #data[stk]['portfolio_value'] = data[stk]['portfolio'].multiply(data[stk]['Adj Close'])
            data[stk]['portfolio_return'] = data[stk]['portfolio'].multiply(data[stk]['diff_p']).cumsum()
        else:
            data.pop(stk)
    except:
        print(stk + " not available")

print('end Processing', time.time()-start_it)
print(table)

#TO DO
# Riduzione numero di azioni
# Salvataggio e lettura lista
# Implementazione altri indicatori e strategie
# Aggiunta ultimo dato da realtime
# salvare dati ed aggiungere solo ultimo giorno
# RSI (2021/05/16 aggiunto
# Invio Mail

