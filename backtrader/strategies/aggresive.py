from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds


class AggresiveStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.current_cross = bool

        # Adding Indicators
        self.stochastic = bt.indicators.StochasticFull(
            self.datas[0])
        self.rsi = bt.indicators.RSI(
            self.datas[0])
        self.macd = bt.indicators.MACD(
            self.datas[0])
        line1 = self.macd.lines.macd
        line2 = self.macd.lines.signal

        self.crossover = bt.indicators.CrossOver(
            line1, line2)
        self.crossdown = bt.indicators.CrossDown(
            line1, line2)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.order:
            return

        # Strategy using Indicators:
        # Stochastic for detecting overbought/oversold positions
        # RSI For Trend Confirmation
        # MACD to trigger signal (crosses above signal line)
        if not self.position:

            # Set Flags for crossover, true if MACD crossed signal line, false if not
            if(self.crossover.lines.crossover[0] > 0):
                self.current_cross = True
            if(self.crossover.lines.crossover[0] < 0):
                self.current_cross = False

            # Entry Signal
            # 1. If Stochastic K and D lines both oversold
            # 2. Use RSI to confirm uptrend by checking it is above middle line (50)
            # 3. Wait for MACD to cross signal line, if stochastic hasn't reached overbought

            if(self.current_cross == True):
                if self.stochastic.lines.percK[0] <= 30 and self.stochastic.lines.percD[0] <= 30:
                    print('passed 2')
                    print(self.rsi.lines.rsi[0])
                    # If RSI over middle line, means it is in an uptrend
                    if(self.rsi.lines.rsi[0] > 40):
                        print('passed 3')
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        self.order = self.buy()

            # Sell Signal
            # 1. If K and D lines are overbought
            # 2. use RSI to confirm downtrend, checking below middle line
            # 3. MACD line cross below signal line, k and d lines haven't reached oversold

            # Exit Strategy
            # 1. If you have buy Positions: Stop loss below nearest swing low. Profit target 1.5 times
            #    the stop loss.
            # 2. Sell Positions: Stop loss above nearest swing high. Profit target at 1.5 times
            #    the stop loss
if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(AggresiveStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(
        modpath, '/Users/alfredopzr/Desktop/Coinbase-Python/Coinbase-Python/datas/nvda-1999-2014.txt')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2010, 1, 13),
        # Do not pass values before this date
        todate=datetime.datetime(2010, 9, 13),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer, percents=95)

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
