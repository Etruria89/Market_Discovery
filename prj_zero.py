"""
This is a python script to extract the stock market data from yahoo finance and to process them to predict the
evolution of the stock price.
This is not a finance tool!

"""
#-----------------------------------------------------------------------------------------------------------------------
#IMPORT MODULES
import pandas as pd
import pandas_datareader as pdr
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import yfinance as yf
from tabulate import tabulate
from utils import *
from backtesting import *

# ----------
# INPUT
# ----------

# Select the activity you want to perform
_backtesting = True
_suggesting = False

# Testing flag to run the script on a reduced list of tickers
_test = True
# Market of interest (active if _test is false)
stock_of_interest = 'NASDAQ Symbol'
# Reduced list of tickers used in the run (active if _test is true)
tick_list = ['AAPL', 'AMZN', 'SPLK', 'CRM', 'BPMC', 'EKSO']

# ===
_read = True
database_name = 'day_data.csv'

# Flag to send the email at the end of the run
_mail = False
email_txt = "email_info.txt" # (the file should be stored in the same folder of this script)

_read = True
_filter_list = False
list_filter_name = 'Revolut_Stocks_List.csv'

# Backtest flag
_backtest = True
start_cash = 10000
# RSI parameteers for backtesting: [period, lower threshold, upper threshold]
RSI_fast_param = [7, 20, 75]
RSI_slow_param = [21, 40, 80]

# Plot flag
_plot = False

# Period to be inspected
start_time = datetime.datetime(2016, 1, 1).strftime("%Y-%m-%d")
end_time = datetime.datetime.today().strftime("%Y-%m-%d")

# Strategy parameters
_signal = 'RSI' # 'mean', 'RSI'

window_short = 7
window_long = 21
sell_rsi_sell_th = 75
sell_rsi_buy_th = 30

# Extra info extraction
info_arr = ["sector", "industry", "marketCap"]

# ----------
# CORE
# ----------

# Timer starter
start_it = time.time()

# Lists and dictionaries initialization
data = {}
table = {}
tick = []

# Variable initialization
all_stocks = pdr.nasdaq_trader.get_nasdaq_symbols()
stocks = all_stocks[stock_of_interest]

# Download yf database
yf.pdr_override()

# Define tickers of interest
if _test:

    tick = tick_list

else:

    info_df = pd.DataFrame(columns=["tick"] + info_arr)

    for stk, stock in all_stocks.iterrows():
        print('Check if eligible...', stk, stock['Security Name'], time.time()-start_it)
        if stock['Financial Status'] == 'N' and stock['Listing Exchange'] == 'Q' and stock['ETF'] == False:
            try:
                #if float(yf.Ticker(stk).info["earningsQuarterlyGrowth"] or 0) > 1:
                if "Common Stock" in stock['Security Name']:
                    #tmp_stock = yf.Ticker(stk)
                    #info_tmp = [stk]
                    #for req_info in info_arr:
                    #   try:
                    #       info_tmp.append(tmp_stock.info[req_info])
                    #   except:
                    #       info_tmp.append("N.A.")
                    #info_df.loc[-1] = info_tmp
                    tick.append(stk)
            except:
                pass

# Read data
print('Start Reading', time.time()-start_it)

if _read:

    # READ DATA AND SAVE TO .csv
    df = yf.download(
            tickers=tick,
            #period="5y",
            start=start_time,
            end=end_time,
            interval="1d",
            group_by='ticker',
            auto_adjust=True,
            prepost=True,
            threads=True,
            proxy=None
        )
    df.to_csv(database_name)

else:

    # READ FROM .csv
    df = pd.read_csv('ticker.csv', header=[0, 1])
    df.drop([0], axis=0, inplace=True)  # drop this row because it only has one column with Date in it
    df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')] = pd.to_datetime(df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')], format='%Y-%m-%d')  # convert the first column to a datetime
    df.set_index(('Unnamed: 0_level_0', 'Unnamed: 0_level_1'), inplace=True)  # set the first column as the index
    df.index.name = None  # rename the index

data={idx: gp.xs(idx, level=0, axis=1) for idx, gp in df.groupby(level=0, axis=1)}
print('end Reading', time.time()-start_it)

if _filter_list:

    # Revo_DB
    revo_db = pd.read_csv(list_filter_name, header=[0, 1])
    revo_tick_lol = revo_db["Symbol"][:].values.tolist()
    tick = [item for sublist in revo_tick_lol for item in sublist]

# ----------------
# END READING
# ----------------

# ----------------
# START PROCESSING
# ----------------
if _suggesting:
    for stk in tick:
        print('    Processing...', stk, all_stocks['Security Name'][stk], time.time()-start_it)






        if len(data[stk].index) > window_long:

            #  BAsIC READINGS
                # PERCENTAGE CHANGE
            data[stk]['diff_p'] = data[stk]['Close'].pct_change()
            delta = data[stk]['diff_p']

                # VOLUME
            volumes = data[stk]['Volume']

            # ----------
            # INDICATORS

                # READ MA
            data[stk]['mean_short'] = data[stk]['Close'].rolling(window=window_short).mean()
            data[stk]['mean_long'] = data[stk]['Close'].rolling(window=window_long).mean()

                # EVALUATE RSI
            up_days = delta.copy()
            up_days[delta <= 0] = 0.0
            down_days = abs(delta.copy())
            down_days[delta > 0] = 0.0
            RS_up = up_days.rolling(window_long).mean()
            RS_down = down_days.rolling(window_long).mean()
            data[stk]['rsi'] = 100.0 - 100.0 / (1.0 + RS_up / RS_down)

            # Check of the sectors

            # VOLATILITA'
            #data[stk]['vol_7']= data[stk]['diff_p'].rolling(7).std() * np.sqrt(7)
            #data[stk]['vol_14']= data[stk]['diff_p'].rolling(14).std() * np.sqrt(14)
            #data[stk]['vol_21']= data[stk]['diff_p'].rolling(21).std() * np.sqrt(21)

            #data[stk]['cumprod']=(1+data[stk]['diff_p']).cumprod()

            #STRATEGIA
            data[stk]['signal'] = 0.0

            if _signal == 'mean':

                data[stk]['signal'][window_long:] = np.where(data[stk]['mean_short'][window_long:] >
                                                             data[stk]['mean_long'][window_long:],
                                                             1.0, 0.0)

            elif _signal=='RSI':
                #data[stk]['signal_sell'] = (data[stk]['rsi'] > sell_rsi_sell_th) & (data[stk]['rsi'].shift(1) <= sell_rsi_sell_th)
                #data[stk]['signal_buy'] = (data[stk]['rsi'] < sell_rsi_buy_th) & (data[stk]['rsi'].shift(1) >= sell_rsi_buy_th)
                data[stk]['signal'] = np.where((data[stk]['rsi'] < sell_rsi_buy_th),1,np.nan)
                data[stk]['signal'] = np.where((data[stk]['rsi'] > sell_rsi_sell_th),0,data[stk]['signal'])
                data[stk]['signal'].iloc[0] = 0
                data[stk]['signal'].ffill(inplace=True)
                #data[stk]['positions'] = data[stk]['signal_sell'].astype(int) - data[stk]['signal_buy'].astype(int)
            data[stk]['positions'] = data[stk]['signal'].diff()

            #EARNINGS
            data[stk]['portfolio'] = 1 * data[stk]['signal'].shift(1)
            #data[stk]['portfolio_value']=data[stk]['portfolio'].multiply(data[stk]['Adj Close'])
            data[stk]['portfolio_return']=data[stk]['portfolio'].multiply(data[stk]['diff_p']).cumsum()

            #OUTPUT TABLE
            table[stk]={}
            table[stk]['symbol']=stk
            table[stk]['name']=all_stocks['Security Name'][stk]
            _check_tmp=data[stk]['signal'][len(data[stk].index)-1]+data[stk]['positions'][len(data[stk].index)-1]
            if _check_tmp==-1:
                table[stk]['type']='sell'
            elif _check_tmp==0:
                table[stk]['type']='stay out'
            elif _check_tmp==1:
                table[stk]['type']='hold in'
            elif _check_tmp==2:
                table[stk]['type']='buy'
            table[stk]['ovll_earn']=data[stk]['portfolio_return'][len(data[stk].index)-1]
            try:
                table[stk]['n_trades']=data[stk]['positions'].value_counts()[1.0]
                table[stk]['avg_day_trades']=data[stk]['signal'].sum()/table[stk]['n_trades']
                _df_tmp=data[stk].loc[data[stk]['positions']==1.0]['portfolio_return']
                if data[stk].iloc[-1:]['signal'].item()==1.0 or table[stk]['n_trades']==1:
                    _df_tmp=_df_tmp.append(data[stk]['portfolio_return'].iloc[-1:])
                table[stk]['succ_trades']=len(_df_tmp.diff().loc[_df_tmp.diff()>0])/(len(_df_tmp.diff())-1)
            except:
                table[stk]['n_trades']=0
                table[stk]['avg_day_trades']=np.nan
                table[stk]['succ_trades']=np.nan

            #PLOT
            if _plot:
                fig = plt.figure()
                # Add a subplot and label for y-axis
                ax1 = fig.add_subplot(111,  ylabel='Price in $ '+stk)
                # Plot the closing price
                data[stk]['Close'][-100:].plot(ax=ax1, color='r', lw=2.)
                # Plot the short and long moving averages
                data[stk][['mean_short', 'mean_long']][-100:].plot(ax=ax1, lw=2.)
                # Add the title
                plt.title(stk + " MAs")
                #if _signal=='mean':
                # Plot the buy signals
                ax1.plot(data[stk][-100:].loc[data[stk]['positions'] == 1.0].index,
                         data[stk]['Close'][-100:][data[stk]['positions'] == 1.0],
                         '^', markersize=10, color='m')
                # Plot the sell signals
                ax1.plot(data[stk][-100:].loc[data[stk]['positions'] == -1.0].index,
                         data[stk]['Close'][-100:][data[stk]['positions'] == -1.0],
                         'v', markersize=10, color='k')
                #elif _signal=='RSI':
                if _signal == 'RSI':
                    # Plot RSI
                    fig_rsi = plt.figure("RSI") # RSI
                    ax_rsi = fig_rsi.add_subplot(111, ylabel='RSI [%]')
                    data[stk][['rsi']].plot(ax=ax_rsi, lw=2.)
                    # Add the title
                    plt.title(stk + " RSI plot")
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

        else:
            data.pop(stk)


    print('end Processing', time.time()-start_it,'\n')
    print(tabulate([table[stk].values() for stk in table], headers = ['Symbol', 'Name', 'What To Do', 'Overall_Return', 'n_trades', 'avg_day_trade', 'succ_trades']))

# ----------------
# END PROCESSING
# ----------------

# ------------------
# START BACK-TESTING
# ------------------

if _backtesting:

    # Create an empty list to store the percencange change of your portfolio
    portfolio_performance = []

    # loop over each tick and perform a back-testing task
    for stk in tick:

        print(stk)
        end_cash = backtesting_run(data[stk], start_cash, RSI_fast_param, RSI_slow_param)

        portfolio_performance.append((end_cash - start_cash) / start_cash)

    # Display a barchart containing the relevant information
    tick_id = range(len(tick))
    plt.bar(tick_id, portfolio_performance, align='center')
    plt.xticks(tick_id, tick)
    plt.show()
# ------------------
# END BACK-TESTING
# ------------------

# ----------------
# START SEND EMAIL
# ----------------

if _mail:

    report_db = tabulate([table[stk].values() for stk in table], headers=['Symbol', 'Name', 'What To Do', 'Overall_Return', 'n_trades', 'avg_day_trade', 'succ_trades'])
    mail_sender(email_txt, report_db, end_time)

# ----------------
# END SEND EMAIL
# ----------------

#TODO ======= leaving for 3/Oct/2017 =======
# Reduce number of stocks (Partially done (Revolut example) via list of labels in  csv file)
# Explore talib
# Clean the structure of the script adding functions
# Salvataggio e lettura lista
# Include NYSE stocks
# Implement new strategie and approaches
# Add realtime last data
# read database and add missing days
# Add other indicators
# realtime data add for the current day if market not closed

#PLOT
#data['AAPL'][['Adj Close', 'mean_short', 'mean_long', 'signal']].plot(grid=True)
#data['AMZN'][['Adj Close', 'mean_short', 'mean_long', 'signal']].plot(grid=True)
#pd.plotting.scatter_matrix(data['AAPL'][['diff_p']], diagonal='kde', alpha=0.1,figsize=(12,12))

##start_it=time.time()
#pnls = {i:pdr.get_data_yahoo(i, start=start_time-datetime.timedelta(np.ceil(window_long*7/5)), end=end_time) for i,stock in all_stocks.iterrows()}
##end_it=time.time()
##print(end_it-start_it)

##start_it=time.time()
###data_new=pdr.get_data_yahoo(all_stocks['NASDAQ Symbol'],start=start_time,end=end_time)
##end_it=time.time()
##print(end_it-start_it)

#http://theautomatic.net/yahoo_fin-documentation/
#http://theautomatic.net/2021/02/16/how-to-get-stock-earnings-data-with-python/
