# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script fi
"""

#IMPORT MODULES
import pandas as pd
import pandas_datareader as pdr
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import yfinance as yf
from tabulate import tabulate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
yf.pdr_override()

#PERIODO DI OSSERVAZIONE
start_time=datetime.datetime(2020, 1, 1)
end_time=datetime.datetime.today()

#VARIABILI PER CALCOLO MEDIA
_signal = 'RSI' # 'mean','RSI'

window_short=7
window_long=21
sell_rsi_sell_th = 75
sell_rsi_buy_th = 30

#INIZIALIZZA VARIABILI
all_stocks=pdr.nasdaq_trader.get_nasdaq_symbols()
stocks=all_stocks['NASDAQ Symbol']
data={}
table={}
tick=[]
_test=True
_read=True
_mail=False
_filter_list = False
list_filter_name = 'Revolut_Stocks_List.csv'

#ATTIVA GRAFICI
_plot=False

#START TIMER
start_it=time.time()

# Extra info extraction
info_arr = ["sector", "industry", "marketCap"]

#DEFINE TICKERS
if _test:
    #tick=['AAPL','AMZN','SPLK','CRM','BPMC','EKSO']
    tick=['AAPL','ADBE','ADI','ADP','ADSK','AEP','ALGN','ALXN','AMAT','AMD',
          'AMGN','AMZN','ANSS','ASML','ATVI','AVGO','BIDU','BIIB','BKNG',
          'CDNS','CDW','CERN', 'CHKP','CHTR','CMCSA','COST','CPRT','CSCO',
          'CSX','CTAS','CTSH','DLTR','DOCU','DXCM','EA','EBAY','EXC','FAST',
          'FB','FISV','FOX','FOXA','GILD','GOOG','GOOGL','IDXX','ILMN','INCY',
          'INTC','INTU','ISRG','JD','KDP','KHC','KLAC','LRCX','LULU','MAR',
          'MCHP','MDLZ','MELI','MNST','MRNA','MRVL','MSFT','MTCH','MU','MXIM',
          'NFLX','NTES','NVDA','NXPI','OKTA','ORLY','PAYX','PCAR','PDD','PEP',
          'PTON','PYPL','QCOM','REGN','ROST','SBUX','SGEN','SIRI','SNPS',
          'SPLK','SWKS','TCOM','TEAM','TMUS','TSLA','TXN','VRSK','VRSN',
          'VRTX','WBA','WDAY','XEL','XLNX','ZM']

else:    
    info_df = pd.DataFrame(columns=["tick"] + info_arr)
    for stk,stock in all_stocks.iterrows():
        print('Check if eligible...',stk,stock['Security Name'],time.time()-start_it)
        if stock['Financial Status']=='N' and stock['Listing Exchange']=='Q' and stock['ETF']==False:
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

#READ DATA
print('Start Reading',time.time()-start_it)
if _read:
    #READ DATA AND SAVE TO .csv
    df = yf.download(  # or pdr.get_data_yahoo(...
            tickers = tick,
            period = "5y",
            interval = "1d",
            group_by = 'ticker',
            auto_adjust = True,
            prepost = True,
            threads = True,
            proxy = None
        )
    df.to_csv('ticker.csv')
else:
    #READ FROM .csv
    df = pd.read_csv('ticker.csv', header=[0, 1])
    df.drop([0], axis=0, inplace=True)  # drop this row because it only has one column with Date in it
    df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')] = pd.to_datetime(df[('Unnamed: 0_level_0', 'Unnamed: 0_level_1')], format='%Y-%m-%d')  # convert the first column to a datetime
    df.set_index(('Unnamed: 0_level_0', 'Unnamed: 0_level_1'), inplace=True)  # set the first column as the index
    df.index.name = None  # rename the index
data={idx: gp.xs(idx, level=0, axis=1) for idx, gp in df.groupby(level=0, axis=1)}
print('end Reading',time.time()-start_it)

if _filter_list:
    # Revo_DB
    revo_db = pd.read_csv(list_filter_name, header=[0, 1])
    revo_tick_lol = revo_db["Symbol"][:].values.tolist()
    tick = [item for sublist in revo_tick_lol for item in sublist]

#START PROCESSING
for stk in tick:
    print('    Processing...',stk,all_stocks['Security Name'][stk],time.time()-start_it)
    if len(data[stk].index)>window_long:
        #VARIAZIONE PERCENTUALE
        data[stk]['diff_p']=data[stk]['Close'].pct_change()
        delta = data[stk]['diff_p']

        # INDICATORI
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
        
        #STRATEGIA
        data[stk]['signal']=0.0
        if _signal=='mean':
            data[stk]['signal'][window_long:]=np.where(data[stk]['mean_short'][window_long:]>data[stk]['mean_long'][window_long:],1.0,0.0)
            #data[stk]['positions'] = data[stk]['signal'].diff()
        elif _signal=='RSI':
            #data[stk]['signal_sell'] = (data[stk]['rsi'] > sell_rsi_sell_th) & (data[stk]['rsi'].shift(1) <= sell_rsi_sell_th)
            #data[stk]['signal_buy'] = (data[stk]['rsi'] < sell_rsi_buy_th) & (data[stk]['rsi'].shift(1) >= sell_rsi_buy_th)
            data[stk]['signal']=np.where((data[stk]['rsi'] < sell_rsi_buy_th),1,np.nan)
            data[stk]['signal']=np.where((data[stk]['rsi'] > sell_rsi_sell_th),0,data[stk]['signal'])
            data[stk]['signal'].iloc[0]=0
            data[stk]['signal'].ffill(inplace=True)
            #data[stk]['positions'] = data[stk]['signal_sell'].astype(int) - data[stk]['signal_buy'].astype(int)
        data[stk]['positions'] = data[stk]['signal'].diff()
         
        #EARNINGS
        data[stk]['portfolio']=1*data[stk]['signal'].shift(1)
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
            data[stk][['mean_short','mean_long']][-100:].plot(ax=ax1, lw=2.)
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
                data[stk][['rsi']].plot(ax=ax_rsi)
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
        

print('end Processing',time.time()-start_it,'\n')
print(tabulate([table[stk].values() for stk in table], headers = ['Symbol','Name','What To Do','Overall_Return','n_trades','avg_day_trade','succ_trades']))

#SEND A MAIL
if _mail:
    msg = MIMEMultipart()
    mail_info = READER_HERE
    from_info = from_name
    pwd = from_pwd
    msg['From'] = from_name
    msg['To'] = to_names
    msg['Subject'] = 'simple email in python'
    #message = tabulate([table[stk].values() for stk in table], headers = ['Symbol','Name','What To Do'])
    message = tabulate([table[stk].values() for stk in table], headers = ['Symbol','Name','What To Do','Overall_Return','n_trades','avg_day_trade','succ_trades'])
    msg.attach(MIMEText(message))
    
    mailserver = smtplib.SMTP('smtp.gmail.com',587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(from_info, from_pwd)
    
    mailserver.sendmail(to_names,msg.as_string())
    
    mailserver.quit()


#TO DO
# Reduce number of stocks (Partially done (Revolut example) via list of labels in  csv file)
# Explore talib
# Clean the structure of the script adding functions
#   Salvataggio e lettura lista
# Include NYSE stocks
# Implementazione altri indicatori e strategie
# Aggiunta ultimo dato da realtime
# read database and add missing days
# Add other indicators
# realtime data add for the current day if market not closed



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

#http://theautomatic.net/yahoo_fin-documentation/
#http://theautomatic.net/2021/02/16/how-to-get-stock-earnings-data-with-python/
