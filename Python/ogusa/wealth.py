'''
------------------------------------------------------------------------
Last updated 7/17/2015

Returns the wealth for all ages of a certain percentile.

This py-file calls the following other file(s):
            data/wealth/scf2007to2013_wealth_age_all_percentiles.csv
            utils.py

This py-file creates the following other file(s):
    (make sure that an OUTPUT folder exists)
            OUTPUT/Demographics/distribution_of_wealth_data.png
            OUTPUT/Demographics/distribution_of_wealth_data_log.png
            OUTPUT/Saved_moments/wealth_data_moments.pkl
------------------------------------------------------------------------
'''

'''
------------------------------------------------------------------------
    Packages
------------------------------------------------------------------------
'''

import numpy as np
import pandas as pd
import utils
import os
from scipy import stats
import cPickle as pickle

cur_path = os.path.split(os.path.abspath(__file__))[0]
WEALTH_DIR = os.path.join(cur_path, "data", "wealth")

'''
------------------------------------------------------------------------
    Import Data
------------------------------------------------------------------------
'''

# read in SCF data collapsed by age and percentile for graphs
def get_wealth_data():
    wealth_file = utils.read_file(
        cur_path, "data/wealth/scf2007to2013_wealth_age_all_percentiles.csv")
    data = pd.read_table(wealth_file, sep=',', header=0)

    # read in raw SCF data to calculate moments
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    year_list = [2013, 2010, 2007]
    scf_dict = {}
    for year in year_list:
        filename = os.path.join(fileDir, '../Data/Survey_of_Consumer_Finances/rscfp'+str(year)+'.dta')
        filename = os.path.abspath(os.path.realpath(filename))
        print 'filename = ', filename
        scf_dict[str(year)] = pd.read_stata(filename, columns=['networth', 'wgt'])

    scf = scf_dict['2013'].append(scf_dict['2010'].append(scf_dict['2007'],ignore_index=True),ignore_index=True)

    return scf, data

'''
------------------------------------------------------------------------
    Graph Data
------------------------------------------------------------------------
'''


def wealth_data_graphs(data, output_dir):
    '''
    Graphs wealth distribution and its log
    '''
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    to_graph = np.array(data)[:, 1:-1]

    domain = np.linspace(18, 95, 78)
    Jgrid = np.linspace(1, 99, 99)
    X, Y = np.meshgrid(domain, Jgrid)
    cmap2 = matplotlib.cm.get_cmap('summer')
    fig10 = plt.figure()
    ax10 = fig10.gca(projection='3d')
    ax10.plot_surface(X, Y, (to_graph).T, rstride=1, cstride=2, cmap=cmap2)
    ax10.set_xlabel(r'age-$s$')
    ax10.set_ylabel(r'percentile')
    ax10.set_zlabel(r'wealth')
    plt.savefig(os.path.join(
        outputdir, '/Demographics/distribution_of_wealth_data'))

    fig10 = plt.figure()
    ax10 = fig10.gca(projection='3d')
    ax10.plot_surface(X, Y, np.log(to_graph).T,
                      rstride=1, cstride=2, cmap=cmap2)
    ax10.set_xlabel(r'age-$s$')
    ax10.set_ylabel(r'percentile')
    ax10.set_zlabel(r'log of wealth')
    plt.savefig(os.path.join(
        outputdir, '/Demographics/distribution_of_wealth_data_log'))



# '''
# ------------------------------------------------------------------------
#     Compute Gini
# ------------------------------------------------------------------------
# '''
# def gini_wgt(df):
#     '''
#     Inputs:
#         list_of_values = series to compute gini from
#     Output:
#         gini coefficient
#     '''
#     sorted_list = sorted(list_of_values)

#     print 'sorted list: ', type(sorted_list), sorted_list[:5]
#     print 'weights', type(weights), weights[:5], weights[sorted_list][:5]
#     quit()

#     weights = weights[sorted_list]/weights.sum()
#     p = weights.cumsum()
#     nu = (weights[sorted_list]*sorted_list).cumsum()
#     print 'nu shape: ', nu, nu.shape
#     nu = nu/nu[-1]

#     return (nu[1:]*p[:-1]).sum() - (nu[:-1] * p[1:]).sum()



'''
------------------------------------------------------------------------
    Get wealth moments
------------------------------------------------------------------------
'''
# Restrict the data: it has other columns that give weights and indexes the age

def get_wealth_data(bin_weights, J, flag_graphs):
    '''
    Inputs:
        bin_weights = ability weights (Jx1 array)
        J = number of ability groups (scalar)
        flag_graphs = whether or not to graph distribution (bool)
        output_dir = path to the starting data
    Output:
        Saves a pickle of the desired wealth percentiles.  Graphs those levels.
    '''
    scf, data = get_wealth_data()    

    if flag_graphs:
        wealth_data_graphs(data, output_dir)

    # calculate percentile shares (percentiles based on lambdas input)
    scf.sort(columns='networth', ascending=True, inplace=True)
    scf['weight_networth'] = scf['wgt']*scf['networth']
    total_weight_wealth = scf.weight_networth.sum()
    cumsum = scf.wgt.cumsum()
    pct_wealth = np.zeros((bin_weights.shape[0],))
    top_pct_wealth = np.zeros((bin_weights.shape[0],))
    wealth = np.zeros((bin_weights.shape[0],))
    cum_weights = bin_weights.cumsum()
    for i in range(bin_weights.shape[0]):
        cutoff = scf.wgt.sum() / (1./cum_weights[i])
        pct_wealth[i] = scf.networth[cumsum >= cutoff].iloc[0]
        top_pct_wealth[i] = 1 - ((scf.weight_networth[cumsum < cutoff].sum())/total_weight_wealth)
        wealth[i] = ((scf.weight_networth[cumsum < cutoff].sum())/total_weight_wealth)


    wealth_share = np.zeros((bin_weights.shape[0],))
    wealth_share[0] = wealth[0]
    wealth_share[1:] = wealth[1:]-wealth[0:-1]

    # compute 90/10 ratio, top 10% share, top 1% share
    cutoff = scf.wgt.sum() / (1./.1)
    pct_10 = scf.networth[cumsum >= cutoff].iloc[0]
    cutoff = scf.wgt.sum() / (1./.9)
    pct_90 = scf.networth[cumsum >= cutoff].iloc[0]
    top_10_share = 1 - ((scf.weight_networth[cumsum < cutoff].sum())/total_weight_wealth)
    ratio_90_10 = pct_90/pct_10 
    cutoff = scf.wgt.sum() / (1./.99)
    pct_99 = scf.networth[cumsum >= cutoff].iloc[0]
    top_1_share = 1 - ((scf.weight_networth[cumsum < cutoff].sum())/total_weight_wealth)


    # compute gini coeff
    scf.sort(columns='networth', ascending=True, inplace=True)
    p = (scf.wgt.cumsum()/scf.wgt.sum()).as_matrix()
    nu = ((scf.wgt*scf.networth).cumsum()).as_matrix()
    nu = nu/nu[-1]
    gini_coeff = (nu[1:]*p[:-1]).sum() - (nu[:-1] * p[1:]).sum()


    # compute variance in logs
    df = scf.drop(scf[scf['networth'] <=0.0].index)
    df['ln_networth'] = np.log(df['networth'])
    df.sort(columns='ln_networth', ascending=True, inplace=True)
    weight_mean = ((df.ln_networth*df.wgt).sum())/(df.wgt.sum())
    var_ln_wealth = ((df.wgt*((df.ln_networth-weight_mean)**2)).sum())*(1./(df.wgt.sum()-1))


    wealth_moments = np.append([wealth_share], [gini_coeff,var_ln_wealth])


    return wealth_moments
