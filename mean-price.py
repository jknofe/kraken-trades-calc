#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   trend class
#
from pprint import pprint as pprint
import pandas as pd

trades = {}
# jojo
deposits = {'XXBTZEUR': {'vol': 0.02512599 + 0.00027999, 'cost': 791.5076200000001},
            'EURO': {'vol': 8000, 'cost': 8000}}
# ben
# deposits = {'XXBTZEUR': {'vol': 0.01459457 + 0.00002331 + 0.00000004, 'cost': 500.0},
#             'EURO': {'vol': 2500, 'cost': 2500}}

assets_of_interest = ['XXBTZEUR', 'XETHZEUR', 'ADAEUR', 'XDGEUR']
# assets_of_interest = ['XETHZEUR']
asset_swaps = ['XETHXXBT', 'XXDGXXBT']


class CryptoAsset:

    def __init__(self, name):
        self.name = name
        self.vol_add = 0
        self.vol = 0
        self.vol_sum_buy = 0
        self.vol_sum_sell = 0
        self.cost = 0
        self.cost_sum_buy = 0
        self.cost_sum_sell = 0
        self.mean_price = 0

    def add_vol(self, vol):
        self.vol_add = self.vol_add + vol

    def get_vol(self):
        return self.vol_add + self.vol_sum_buy - self.vol_sum_sell

    def get_mean_price(self):
        if self.cost > 0:
            mean_price = (self.cost / self.vol)
        else:
            mean_price = 0
        return mean_price


with open('trades.csv', mode='r') as infile:
    trades_df = pd.read_csv(infile)


for pair in trades_df['pair']:
    trades[pair] = CryptoAsset(pair)

pprint(trades.keys())

for pair in trades.keys():
    trades[pair].vol_sum_buy = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'buy')]['vol'].sum()
    trades[pair].cost_sum_buy = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'buy')]['cost'].sum()

    trades[pair].vol_sum_sell = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'sell')]['vol'].sum()
    trades[pair].cost_sum_sell = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'sell')]['cost'].sum()

# all asset swaps crate additional volume
for pair in trades.keys():
    if pair in asset_swaps:
        if pair == 'XETHXXBT':
            trades['XETHZEUR'].add_vol(trades[pair].vol_sum_buy)
            trades['XXBTZEUR'].add_vol(-1 * trades[pair].cost_sum_buy)
        if pair == 'XXDGXXBT':
            trades['XXBTZEUR'].add_vol(trades[pair].cost_sum_sell)
            trades['XDGEUR'].add_vol(-1 * trades[pair].vol_sum_sell)


for pair in deposits.keys():
    if pair in trades.keys():
        trades[pair].add_vol(deposits[pair]['vol'])

print('\nAccount balance:')
for pair in trades.keys():
    if pair in assets_of_interest:
        print("{0:>12}: {1:.7f}".format(trades[pair].name, trades[pair].get_vol()))


print('\n\n')
print('\nAccount mean price on each asset:\n')
mytrades = {}
for pair in trades_df['pair']:
    mytrades[pair] = CryptoAsset(pair)
    if pair in deposits.keys():
        mytrades[pair].vol = deposits[pair]['vol']
        mytrades[pair].cost = deposits[pair]['cost']

for index, row in trades_df.iterrows():
    pair = row['pair']
    if pair in asset_swaps:
        if pair == 'XETHXXBT':
            virtual_cost = mytrades['XXBTZEUR'].get_mean_price() * row['cost']
            mytrades['XXBTZEUR'].cost -= virtual_cost
            mytrades['XXBTZEUR'].vol -= row['cost'] + row['fee']
            mytrades['XETHZEUR'].cost += virtual_cost
            mytrades['XETHZEUR'].vol += row['vol']
        if pair == 'XXDGXXBT':
            virtual_cost = mytrades['XDGEUR'].get_mean_price() * row['vol']
            mytrades['XDGEUR'].cost -= virtual_cost
            mytrades['XDGEUR'].vol -= row['vol']
            mytrades['XXBTZEUR'].cost += virtual_cost
            mytrades['XXBTZEUR'].vol += row['cost'] - row['fee']
    else:
        if row['type'] == 'buy':
            mytrades[pair].vol += row['vol']
            mytrades[pair].cost += row['cost']
        if row['type'] == 'sell':
            mytrades[pair].vol -= row['vol']
            mytrades[pair].cost -= row['cost']

print("{0:>12} {1:>12} {2:>12} ".format('asset', 'volume', 'mean price'))
print("{0:>12} {1:>12} {2:>12} ".format('-----', '------', '----------'))
for pair in mytrades.keys():
    if pair in assets_of_interest:
        print("{0:>12} {1:>12.6f} {2:>12.2f}".format(mytrades[pair].name, mytrades[pair].vol, mytrades[pair].get_mean_price()))

total_cost = 0.0
for pair in mytrades.keys():
    if pair in assets_of_interest:
        total_cost += mytrades[pair].cost

print("\nAccount overall cost: {0:.2f}\n\n".format(total_cost))

print("{0:>12} {1:>12}".format('price', 'profit'))
print("{0:>12} {1:>12}".format('-----', '------'))
for pair in mytrades.keys():
    print(pair)
    for rais in range(-15, 50, 5):
        if pair in assets_of_interest:
            profit = (mytrades[pair].vol * (1 + rais / 100) * mytrades[pair].get_mean_price()) - (mytrades[pair].vol * mytrades[pair].get_mean_price())
            print("{0:>12.2f} {1:>12.2f}".format((1 + rais / 100)*mytrades[pair].get_mean_price(), profit))
