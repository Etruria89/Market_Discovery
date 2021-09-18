"""
This script includes functions for the
sector analysis and the selection of the best
stocks for each sector
"""

import pandas as pd
import csv

def top_tick_finder(saved_tick_file):

    # Read database  with tick info
    stock_info_db = pd.read_csv(saved_tick_file, index_col=0)

    # Clan the database removing empty rows
    sector_sets = list(stock_info_db.Sector.unique())
    industry_sets = list(stock_info_db.Industry.unique())

    # Remove empty and N.A. from the sector and industry lists
    try:
        sector_sets = [x for x in sector_sets if str(x) != 'nan']
    except:
        pass
    try:
        industry_sets = [x for x in industry_sets if str(x) != 'nan']
    except:
        pass
    try:
        sector_sets.revove("N.A.")
    except:
        pass
    try:
        industry_sets.revove("N.A.")
    except:
        pass

    # Create



    # Filter the database using the available sectors
    df = stock_info_db[(stock_info_db.Sector[sector_sets[0]])]
