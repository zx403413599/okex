import sys
import numpy as np
import time
import arrow
from talib import SMA
import json
import logging
from okexapi.FutureAPI import Future
from base import *


class Ma(Base):

    def __init__(self,
            api_key,
            secret_key,
            url,
            symbol, 
            kline_size, # kline size, 15min
            kline_num, # number of klines to get
            amount_ratio, # percentage of available coins
            bbo, # 1: market price, 0: use given price
            fast, # fast kline period, 5
            slow, # slow kline period, 20
            interval,
            band_width,
            least_amount,
            logger = None):

        super(Ma, self).__init__(api_key, secret_key, url, logger)
        self.symbol = symbol
        idx = symbol.index('_')
        self.coin = symbol[:idx]
        self.currency = symbol[idx + 1:]
        self.kline_size = kline_size
        self.kline_num = kline_num
        self.amount_ratio = amount_ratio
        self.bbo = bbo
        self.fast = fast
        self.slow = slow
        self.interval = interval
        self.band_width = band_width
        self.least_amount = least_amount


    def get_amount(self, coin):

        return self.get_available(coin)

    def ma_cross(self, fast_ma, slow_ma):
        # stable version
        if fast_ma[-3] < slow_ma[-3] and fast_ma[-2] >= slow_ma[-2]:
            return 'gold'
        elif fast_ma[-3] > slow_ma[-3] and fast_ma[-2] <= slow_ma[-2]:
            return 'dead'
        else:
            return 'nothing'

    def run_forever(self):

        while True:
            usdt_available = self.get_available('usdt')
            coin_available = self.get_available(self.coin)

            self.logger.info('position: usdt = %s, %s = %s' % (usdt_available, self.coin, coin_available))

            kline = self.get_kline(self.symbol, self.kline_size, self.kline_num)

            close = np.array([kline[i][4] for i in range(self.kline_num)])

            fast_ma = tb.SMA(close, self.fast)
            slow_ma = tb.SMA(close, self.slow)
            slow_upper = slow_ma + self.band_width
            slow_lower = slow_ma - self.band_width

            last = kline[-1][4]
            self.logger.info('last: ' + str(last))
          
            cross_with_upper = self.ma_cross(fast_ma, slow_upper)
            cross_with_lower = self.ma_cross(fast_ma, slow_lower)
            cross_with_slow = self.ma_cross(fast_ma, slow_ma)

            if cross_with_upper == 'gold' and coin_available < self.least_amount:
                self.logger.info('golden cross with upper bond')
                amount = self.get_amount()
                self.buy(self.symbol, last, amount, self.bbo)
                self.logger.info('buy at: %f, amount: %d' % (last, amount))

            if cross_with_slow == 'dead' and coin_available > self.least_amount:
                self.logger.info('dead cross with slow ma')
                self.sell(self.symbol, last, coin_available, self.bbo)
                self.logger.info('sell at: %f, amount: %d' % (last, coin_available))

            time.sleep(self.interval)


if __name__ == '__main__':

    config_path = sys.argv[1]

    f = open(config_path, encoding = 'utf-8')
    config = json.load(f)

    api_key = config['api_key']
    secret_key = config['secret_key']
    url = config['url']

    symbol = config['symbol']
    kline_size = config['kline_size']
    kline_num = config['kline_num']
    amount_ratio = config['amount_ratio']
    slow = config['slow']
    fast = config['fast']
    interval = config['interval']

    bbo = config['bbo']
    leverage = config['leverage']
    stop_loss = config['stop_loss']
    band_width = config['band_width']
    least_amount = config['least_amount']

    logger = get_logger()

    ma_bot = Ma(api_key,
            secret_key,
            url,
            symbol,
            kline_size,
            kline_num,
            amount_ratio,
            bbo,
            leverage,
            fast,
            slow,
            interval,
            stop_loss,
            band_width,
            least_amount,
            logger = logger)

    ma_bot.run_forever()


