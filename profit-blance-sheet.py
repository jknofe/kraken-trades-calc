#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   trend class
#
from decimal import Decimal
def decimal_from_value(value):
    return Decimal(value)
from pprint import pprint as pprint
import pandas as pd

trades = {}
MyAssetBalance = {}
# jojo
# deposits = {'XXBTZEUR': {'vol': 0.0251259900 + 0.0002869227, 'cost': 791.5076200000001},
#             'EURO': {'vol': 10000, 'cost': 10000}}
deposits = {'XXBTZEUR': {'price': Decimal("31145.8869"), 'cost': Decimal("791.5076200000001"), 'fee': Decimal("0.0"), 'vol': Decimal("0.02541291")}}
deposits = {'XXBTZEUR': {'price': Decimal("28665.80000"), 'cost': Decimal("791.5076200000001"), 'fee': Decimal("0.0"), 'vol': Decimal("0.02541291")}}
# ben
# deposits = {'XXBTZEUR': {'vol': 0.01459457 + 0.00002331 + 0.00000004, 'cost': 500.0},
#             'EURO': {'vol': 2500, 'cost': 2500}}

assets_of_interest = ['XXBTZEUR', 'XETHZEUR', 'ADAEUR', 'XDGEUR']
# assets_of_interest = ['XETHZEUR']
asset_swaps = ['XETHXXBT', 'XXDGXXBT']


class Order:
    def __init__(self, name, pair, date, price, cost, fee, vol, swap=None):
        self.name = name
        self.pair = pair
        self.date = date
        self.price = Decimal(price)
        self.cost = Decimal(cost)
        self.fee = Decimal(fee)
        self.volume = Decimal(vol)
        self.swap = swap

    def __str__(self):
        if self.swap:
            return "name: {}, pair: {}, date: {}\nprice: {}, cost: {}, fee: {}, volume: {}\n[swap_from:\n{}\n]".format(self.name, self.pair, self.date, self.price, self.cost, self.fee, self.volume, self.swap)
        else:
            return "name: {}, pair: {}, date: {}\nprice: {:.2f}, cost: {:.2f}, fee: {}, volume: {:.12f}".format(self.name, self.pair, self.date, self.price, self.cost, self.fee, self.volume,)


class AssetBalanceSheet():
    """ Balance sheet for one asset type"""

    def __init__(self, name):
        self.name = name
        self.pods = []
        self.sells = {}

    def get_highest_priced_order_ids(self):
        """
            we need to know which order had the highest price we bought into,
            as soon as we are going to sell we sell to highest priced assets first to make a low possible profit
        """
        if len(self.pods) > 0:
            pod_indices = []
            max_price = max(pod.price for pod in self.pods)
            for pod in self.pods:
                if pod.price == max_price:
                    pod_indices.append(self.pods.index(pod))
            return pod_indices
        else:
            return None

    def get_mean_price(self):
        mean_price = None
        if len(self.pods) > 0:
            cost = Decimal(0)
            volume = Decimal(0)
            for pod in self.pods:
                cost += (pod.volume * pod.price)
                volume += pod.volume
            mean_price = Decimal(cost / volume)
        else:
            mean_price = "None"
        return mean_price

    def calc_profit(self, vol, buy_price, sell_price):
        cost_buy = vol * buy_price
        cost_sell = vol * sell_price
        fees = Decimal(0)
        profit = cost_sell - cost_buy - fees
        return profit

    def add_buy_order(self, Order):
        """ all buy orders are considered as a separated pod of this asset """
        self.pods.append(Order)

    def sell_asset(self, Order):
        """ to sell a asset we are going to sell everything in a top-down manner,
            we start with the highest price we have bought in, then try to empty this pod.
            if this pod in empty we are going to empty the next lower one
        """
        # create a new dict entry for this sell
        self.sells[Order.name] = {'sell_order': Order, 'buy_orders': {}}
        #
        volume_to_sell = Order.volume
        while volume_to_sell > 0:
            # get the first of the highest priced pods we have
            try:
                index = self.get_highest_priced_order_ids()[0]
            except:
                print('###### ERROR #####')
                print(Order)
                pprint(self.pods)
                exit()
            volume_left_in_pod = self.pods[index].volume - volume_to_sell
            # print(volume_left_in_pod)
            # print("DEBUG: pod_id: {} pod_vol: {:.10f} - sell_vol: {:.10f} - left: {:.10f}".format(index, self.pods[index].volume, volume_to_sell, volume_left_in_pod))
            self.sells[Order.name]['buy_orders'][self.pods[index].name] = {}
            pod_used_dict = self.sells[Order.name]['buy_orders'][self.pods[index].name]
            if 'profit' not in pod_used_dict.keys():
                pod_used_dict['profit'] = Decimal(0)
            if volume_left_in_pod == Decimal(0.0):
                # sell volume will empty this pod completely
                # print("sell FIST perfectly")
                profit = self.calc_profit(volume_to_sell, self.pods[index].price, Order.price)
                volume_to_sell = Decimal(0)
                self.pods.pop(index)
                # break
            elif volume_left_in_pod < Decimal(0.0):
                profit = self.calc_profit(self.pods[index].volume, self.pods[index].price, Order.price)
                # this pod is empty after this sell and can be removed
                self.pods.pop(index)
                volume_to_sell = Decimal(-1) * volume_left_in_pod
                # print("SELL splits! left to sell: {}".format(volume_to_sell))
            else:
                profit = self.calc_profit(volume_to_sell, self.pods[index].price, Order.price)
                # there is something left in this pod, update this pods volume and break the loop
                self.pods[index].volume = volume_left_in_pod
                # print("sell FITS but pod is not empty")
                volume_to_sell = Decimal(0)
                # break
            pod_used_dict['profit'] = pod_used_dict['profit'] + profit
        # pprint(self.sells)
        order_profit = Decimal(0)
        for item in self.sells[Order.name]['buy_orders'].keys():
            order_profit += self.sells[Order.name]['buy_orders'][item]['profit']
        # print(order_profit)
        # preprocessin if it was a swap, if so we do not have a loss, we just book the volume out at a zero profit
        if Order.swap is not None:
            print("SWAP!!!")
            for item in self.sells[Order.name]['buy_orders'].keys():
                self.sells[Order.name]['buy_orders'][item]['profit'] = Decimal(0)
        return order_profit


class CryptoAsset:

    def __init__(self, name):
        self.name = name
        self.vol_add = Decimal(0)
        self.vol = Decimal(0)
        self.vol_sum_buy = Decimal(0)
        self.vol_sum_sell = Decimal(0)
        self.cost = Decimal(0)
        self.cost_sum_buy = Decimal(0)
        self.cost_sum_sell = Decimal(0)
        self.mean_price = Decimal(0)

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
    trades_df = pd.read_csv(infile, converters={'price': decimal_from_value, 'cost': decimal_from_value, 'fee': decimal_from_value, 'vol': decimal_from_value})


for pair in trades_df['pair']:
    trades[pair] = CryptoAsset(pair)
    MyAssetBalance[pair] = AssetBalanceSheet(pair)

pprint(trades.keys())

for pair in trades.keys():
    trades[pair].vol_sum_buy = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'buy')]['vol'].sum()
    trades[pair].cost_sum_buy = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'buy')]['cost'].sum()

    trades[pair].vol_sum_sell = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'sell')]['vol'].sum()
    trades[pair].cost_sum_sell = trades_df.loc[(trades_df['pair'] == pair) & (trades_df['type'] == 'sell')]['cost'].sum()

# all asset swaps create additional volume
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
        my_order = Order('initial deposit', pair, '2021-01-01', deposits[pair]['price'], deposits[pair]['cost'], deposits[pair]['fee'], deposits[pair]['vol'])
        print(my_order)
        MyAssetBalance[pair].add_buy_order(my_order)


print('\nAccount balance:')
for pair in trades.keys():
    if pair in assets_of_interest:
        print("{0:>12}: {1:.7f}".format(trades[pair].name, trades[pair].get_vol()))

for index, row in trades_df.iterrows():
    pair = row['pair']
    my_order = Order(row['txid'], row['pair'], row['time'], row['price'], row['cost'], row['fee'], row['vol'])
    # process byu orders
    if row['type'] == 'buy':
        if pair == 'XETHXXBT':
            virtual_sell_order = Order('virtual_sell_XXBTZEUR', 'XXBTZEUR', my_order.date, Decimal(0), Decimal(0), Decimal(0), my_order.cost, my_order)
            virtual_cost = Decimal(-1) * MyAssetBalance['XXBTZEUR'].sell_asset(virtual_sell_order)
            virtual_price = virtual_cost / my_order.volume
            virtual_fee = 0
            swap_order = Order(my_order.name, 'XETHZEUR', my_order.date, virtual_price, virtual_cost, virtual_fee, my_order.cost, my_order)
            MyAssetBalance['XETHZEUR'].add_buy_order(swap_order)
        else:
            MyAssetBalance[pair].add_buy_order(my_order)
    # process sell orders
    elif row['type'] == 'sell':
        # doge to bitcoins
        if pair == 'XXDGXXBT':
            virtual_sell_order = Order('virtual_sell_XDGEUR', 'XDGEUR', my_order.date, Decimal(0), Decimal(0), Decimal(0), my_order.volume, my_order)
            virtual_cost = Decimal(-1) * MyAssetBalance['XDGEUR'].sell_asset(virtual_sell_order)
            virtual_price = virtual_cost / my_order.cost
            virtual_fee = 0
            swap_order = Order(my_order.name, 'XXBTZEUR', my_order.date, virtual_price, virtual_cost, virtual_fee, my_order.cost, my_order)
            MyAssetBalance['XXBTZEUR'].add_buy_order(swap_order)
        else:
            MyAssetBalance[pair].sell_asset(my_order)
    else:
        # skip, errors t.b.d
        pass

print("AssetBalanceSheet:\n==================\n")
for pair in assets_of_interest:
    profit = 0
    for sell_order in MyAssetBalance[pair].sells.keys():
        for buy_order in MyAssetBalance[pair].sells[sell_order]['buy_orders'].keys():
            profit += MyAssetBalance[pair].sells[sell_order]['buy_orders'][buy_order]['profit']
    print("{}: {:.2f} with mean_price: {}".format(pair, profit, MyAssetBalance[pair].get_mean_price()))

print("\n\n")
for pod in MyAssetBalance['XXBTZEUR'].pods:
    print(pod)
    print("\n")

for order_name in MyAssetBalance['XXBTZEUR'].sells.keys():
    pprint(MyAssetBalance['XXBTZEUR'].sells[order_name])
    print("\n")
exit()
