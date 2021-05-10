from datetime import datetime

import pandas as pd
import yfinance as yf


def download_data(tickers, period='5y', start_date=None, end_date=None,
                  interval='1d', filename=None, threads=True):
    '''
    Parameters
    ----------
    tickers : array-like
    period : str
        Check `yfinance` API.
    start_date : str
        Format: `%Y-%m-%d`.
    end_date : str
        If None, the current date is used.
    interval : str
        Check `yfinance` API.
    filename : str
        If None, data is not stored.
    threads : bool or int
        Number of threads.

    Notes
    -----
    * If start_date is specified, then period is ignored.
    '''

    kwargs = {}
    if start_date is not None:
        kwargs['start'] = start_date
        if end_date is None and start_date is not None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        kwargs['end'] = end_date
    else:
        kwargs['period'] = period

    df = yf.download(
        tickers=tickers,
        interval=interval,
        group_by='ticker',
        auto_adjust=True,
        prepost=True,
        threads=threads,
        proxy=None,
        **kwargs
    )

    if filename is not None:
        df.to_csv(filename)

    return df


def load_data(filename):
    df = pd.read_csv(filename, header=[0, 1], index_col=0,
                     parse_dates=True)

    return df
