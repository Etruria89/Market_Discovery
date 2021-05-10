

# TODO: to be continued

class TemporalData:
    '''
    Put pandas.DataFrame on steroids.
    '''

    def __init__(self, df):
        self.df = df

    def get_company_symbols(self):
        return list(self.df.columns.levels[0])

    def get_var_names(self):
        return list(self.df.columns.levels[1])

    def get_swapped_df(self):
        return self.df.swaplevel(i=-2, j=-1, axis=1)
