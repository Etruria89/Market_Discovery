"""
This is a python script to extract the stock market data from yahoo finance and to process them to predict the
evolution of the stock price.
This is not a finance tool!

"""
#-----------------------------------------------------------------------------------------------------------------------
#IMPORT MODULES
import pandas as pd
import pandas_datareader as pdr
import pandas_datareader.data as web
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import yfinance as yf
from tabulate import tabulate
from utils import *
from backtesting import *
import itertools

# ----------
# INPUT
# ----------

# Select the activity you want to perform
_backtesting = False
_suggesting = False

# Testing flag to run the script on a reduced list of tickers
_test = False
# Market of interest (active if _test is false)
stock_of_interest = 'NASDAQ Symbol'
# Reduced list of tickers used in the run (active if _test is true)
tick_list = ['AAPL', 'AMZN', 'SPLK', 'CRM', 'BPMC', 'EKSO']

# ===
_download = True
database_name = 'day_data.csv'

_update_summary = False                                         # If true, the summary database is fully updated
                                                                # otherwise only missing entries are added
summary_entries = ["sector", "industry", "marketCap","beta"]    # Summary info to be downloaded
summary_database_name = 'summary_data.csv'

# Flag to send the email at the end of the run
_mail = False
email_txt = "email_info.txt" # (the file should be stored in the same folder of this script)

_filter_list = False
list_filter_name = 'Revolut_Stocks_List.csv'

# Backtest flag
_backtest = False
start_cash = 10000
# RSI parameters for back-testing: [period, [lower threshold list], [upper threshold list]]
RSI_fast_param = [7, [15, 20, 25, 30, 35, 40], [70]]
RSI_slow_param = [21, [40], [65, 70, 75, 80, 90]]
# MA parameters for back-testing:
MA_fast_param = [50]
MA_slow_param = [100]
# Stop loss condition
stop_loss_th = 0.05

#Default values:
# RSI_fast_period = 7, RSI_fast_low_th = 20, RSI_fast_up_th = 70,
# RSI_slow_period = 21, RSI_slow_low_th = 40, RSI_slow_up_th = 80,
# stop_loss_th = 1.00 (stop loss disabled)):

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

# Define tickers of interest and prepare/read summary database
if _test:

    tick = tick_list

else:

    # Create the complete tick list
    for symbol in all_stocks.iterrows():
        # Create symbol list
        symbol_list = list(symbol)
        print('Check if eligible...', symbol_list[0], symbol_list[1]['Security Name'], time.time() - start_it)
        # Append all the ticks
        tick.append(symbol[0])

    # Analyse the summary database
        # If the summary database exists in the script folder it reads it
    if os.path.isfile(summary_database_name) and _update_summary == False:
        # Read the db with the stock info
        stock_info_db = pd.read_csv(summary_database_name, header=[0, 1])
        tickers_in_summary = stock_info_db['Stock']
        # Otherwise initialize the stock info database and the ticker summary list
    else:
        stock_info_db = pd.DataFrame(columns=['Stock', 'Industry', 'Sector', 'Beta', 'MarketCap'])
        tickers_in_summary = []

        for symbol in all_stocks.iterrows():

            # Create the info dataframe
            if (symbol_list[1]['Financial Status'] == 'N' or str(symbol_list[1]['Financial Status']) == 'nan')\
                    and (symbol_list[1]['Listing Exchange'] == 'Q' or symbol_list[1]['Listing Exchange'] == 'N')  \
                    and symbol_list[1]['ETF'] == False and "Common Stock" in symbol_list[1]['Security Name']\
                    and not symbol[0] in tickers_in_summary:

                tmp_stock = yf.Ticker(symbol[0])
                info_tmp = [symbol[0]]
                try:
                    info = tmp_stock.info
                    industry = info.get('industry')
                    print(industry)
                    beta = info.get('beta')
                    sector = info.get('sector')
                    marketcap = info.get('marketCap')
                    stock_info_db = stock_info_db.append({'Stock': symbol[0], 'Industry': industry, 'Beta': beta,
                                                          'Sector': sector, 'MarketCap': marketcap},
                                             ignore_index=True)
                except:
                    # Ignore entry without value
                    pass
            # Write the stock info database
            stock_info_db.to_csv(summary_database_name)

# Read historical data for each stock
print('Start Reading', time.time()-start_it)

if _download:

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
    df = pd.read_csv(database_name, header=[0, 1])
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

    # loop over each tick and perform a back-testing task
    for stk in tick:

        print(stk)

        # Initialize a portfolio performance list for this tick
        portfolio_performance = []

        # Prepare list of tuples with all possible combination for RSI fast and slow parameters
        RSI_fast_combinations = list(itertools.product(RSI_fast_param[1], RSI_fast_param[2]))
        RSI_slow_combinations = list(itertools.product(RSI_slow_param[1], RSI_slow_param[2]))

        # loop over all the possible combination of RSI threshold given
        for RSI_fast_th_combo in RSI_fast_combinations:
            for RSI_slow_th_combo in RSI_slow_combinations:

                RSI_fast_param_test = [RSI_fast_param[0], RSI_fast_th_combo[0], RSI_fast_th_combo[1]]
                RSI_slow_param_test = [RSI_slow_param[0], RSI_slow_th_combo[0], RSI_slow_th_combo[1]]

                end_cash = backtesting_run(data[stk], start_cash,
                                           RSI_fast_param_test, RSI_slow_param_test,
                                           MA_fast_param[0], MA_slow_param[0],
                                           stop_loss_th)

                portfolio_performance.append((end_cash - start_cash) / start_cash * 100)

        # Performance sensitivity plot
        combinations_output = list(itertools.product(RSI_fast_param[1], RSI_slow_param[2]))
        x_data = [i[0] for i in combinations_output]
        y_data = [j[1] for j in combinations_output]
        column_names = ['RSI_fast_low_th', 'RSI_slow_high_th', 'Performance']
        RSI_fast_sensitivity_db = pd.DataFrame(list(zip(x_data, y_data, portfolio_performance)),
                                    columns =column_names)
        map_plot_3d(stk, RSI_fast_sensitivity_db, column_names)

        # Display a barchart containing the relevant information
        # tick_id = range(len(tick))
        # plt.bar(tick_id, portfolio_performance, align='center')
        # plt.xticks(tick_id, tick), plt.ylabel("Portfolio % change [-]")
        # plt.show()
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
# Check why single tick crashes
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
