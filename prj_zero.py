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

# Variables for averaginf
window_short = 7
window_long = 21

# Variable initialization
all_stocks = pdr.nasdaq_trader.get_nasdaq_symbols()
stocks = all_stocks['NASDAQ Symbol']
data = {}
table = {}
tick = []
_test = False
_save = True

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
            for req_info in info_arr:
                try:
                    info_tmp.append(tmp_stock.info[req_info])
                except:
                    info_tmp.append("N.A.")
            info_df.loc[-1] = info_tmp
            tick.append(stk)

# Read data
if _save:
    # read data and save to .csv
    df = yf.download(  # or pdr.get_data_yahoo(...
            tickers = tick,
            period = "5y",
            interval = "1d",
            group_by = 'ticker',
            auto_adjust = True,
            prepost = True,
            threads = 1,
            proxy = None
        )
    print('end Reading',time.time()-start_it)
    df.to_csv('ticker.csv')
else:
    # Read from .csv
    df = pd.read_csv('ticker.csv', header=[0, 1])
    df.drop([0], axis=0, inplace=True)  # drop this row because it only has one column with Date in it
    df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')] = pd.to_datetime(df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')], format='%Y-%m-%d')  # convert the first column to a datetime
    df.set_index(('Unnamed: 0_level_0', 'Unnamed: 0_level_1'), inplace=True)  # set the first column as the index
    df.index.name = None  # rename the index
data={idx: gp.xs(idx, level=0, axis=1) for idx, gp in df.groupby(level=0, axis=1)}


# Data processing
for stk in tick:
    print('    Processing...',stk,all_stocks['Security Name'][stk],time.time()-start_it)
    if len(data[stk].index)>window_long:
        #VARIAZIONE PERCENTUALE
        data[stk]['diff_p']=data[stk]['Close'].pct_change()
      
        # INDICATORI
        data[stk]['mean_short']=data[stk]['Close'].rolling(window=window_short).mean()
        data[stk]['mean_long']=data[stk]['Close'].rolling(window=window_long).mean()
        
        # VOLATILITA'
        #data[stk]['vol_7']= data[stk]['diff_p'].rolling(7).std() * np.sqrt(7) 
        #data[stk]['vol_14']= data[stk]['diff_p'].rolling(14).std() * np.sqrt(14) 
        #data[stk]['vol_21']= data[stk]['diff_p'].rolling(21).std() * np.sqrt(21) 
        
        #data[stk]['cumprod']=(1+data[stk]['diff_p']).cumprod()
        
        #STRATEGIA
        data[stk]['signal']=0.0
        data[stk]['signal'][window_long:]=np.where(data[stk]['mean_short'][window_long:]>data[stk]['mean_long'][window_long:],1.0,0.0)
        data[stk]['positions'] = data[stk]['signal'].diff()
        
        if  data[stk]['positions'][len(data[stk].index)-1]==1:
            table[stk]=all_stocks['Security Name'][stk]
        #PLOT
        if _plot:
            fig = plt.figure()
            # Add a subplot and label for y-axis
            ax1 = fig.add_subplot(111,  ylabel='Price in $')
            # Plot the closing price
            data[stk]['Adj Close'].plot(ax=ax1, color='r', lw=2.)
            # Plot the short and long moving averages
            data[stk][['mean_short','mean_long']].plot(ax=ax1, lw=2.)
            # Plot the buy signals
            ax1.plot(data[stk].loc[data[stk]['positions'] == 1.0].index, 
                     data[stk]['mean_short'][data[stk]['positions'] == 1.0],
                     '^', markersize=10, color='m')
            # Plot the sell signals
            ax1.plot(data[stk].loc[data[stk]['positions'] == -1.0].index, 
                     data[stk]['mean_short'][data[stk]['positions'] == -1.0],
                     'v', markersize=10, color='k')
            # Show the plot
            plt.show()
        
        #EARNINGS
        data[stk]['portfolio']=1*data[stk]['signal'].shift(1)
        #data[stk]['portfolio_value']=data[stk]['portfolio'].multiply(data[stk]['Adj Close'])
        data[stk]['portfolio_return']=data[stk]['portfolio'].multiply(data[stk]['diff_p']).cumsum()
    else:
        data.pop(stk)
        

print('end Processing',time.time()-start_it)
print(table)

#TO DO
# Riduzione numero di azioni
#   Salvataggio e lettura lista
# Implementazione altri indicatori e strategie
# Aggiunta ultimo dato da realtime
# salvare dati ed aggiungere solo ultimo giorno
# Invio Mail


#PLOT
#data['AAPL'][['Adj Close','mean_short', 'mean_long','signal']].plot(grid=True)
#data['AMZN'][['Adj Close','mean_short', 'mean_long','signal']].plot(grid=True)
#pd.plotting.scatter_matrix(data['AAPL'][['diff_p']], diagonal='kde', alpha=0.1,figsize=(12,12))

##start_it=time.time()
#pnls = {i:pdr.get_data_yahoo(i, start=start_time-datetime.timedelta(np.ceil(window_long*7/5)), end=end_time) for i,stock in all_stocks.iterrows()}
##end_it=time.time()
##print(end_it-start_it)

##start_it=time.time()
###data_new=pdr.get_data_yahoo(all_stocks['NASDAQ Symbol'],start=start_time,end=end_time)
##end_it=time.time()
##print(end_it-start_it)
