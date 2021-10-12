from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import math

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds


class GoldenCross(bt.Strategy):
    params = (('fast', 50), ('slow', 200),
              ('order_percentage', 0.95), ('ticker', 'SPY'))

    def __init__(self):
        self.fast_moving_average = bt.indicators.SMA(
            self.data.close, period=self.params.fast, plotname='50 Day Moving Average'
        )
        self.slow_moving_average = bt.indicators.SMA(
            self.data.close, period=self.params.slow, plotname='200 Day Moving Average'
        )

        self.crossover = bt.indicators.CrossOver(
            self.fast_moving_average, self.slow_moving_average)

    def next(self):
        # If position size is 0, we own 0 shares
        if self.position.size == 0:
            # Crossover is 1, so Golden Cross happened
            if self.crossover > 0:
                amount_to_invest = (
                    self.params.order_percentage * self.broker.cash)
                self.size = math.floor(amount_to_invest / self.data.close)

                print("Buy {} share of {} at {}".format(
                    self.size, self.params.ticker, self.data.close[0]))

                self.buy(size=self.size)
        if self.position.size > 0:
            if self.crossover < 0:
                print("Sell {} shares of {} at {}".format(
                    self.size, self.params.ticker, self.data.close[0]))
                self.close()


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(GoldenCross)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(
        modpath, '/Users/alfredopzr/Desktop/Coinbase-Python/Coinbase-Python/datas/SPY.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 3),
        # Do not pass values before this date
        todate=datetime.datetime(2021, 9, 13),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.AllInSizer, percents=95)

    # Set the commission
    cerebro.broker.setcommission(commission=0.00)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the result
    cerebro.plot()
