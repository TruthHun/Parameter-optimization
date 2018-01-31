# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals

import multiprocessing

import numpy as np
import pandas as pd
import talib
from gm.api import *

'''
基本思想：设定所需优化的参数数值范围及步长，将参数数值循环输入进策略，进行遍历回测，
        记录每次回测结果和参数，根据某种规则将回测结果排序，找到最好的参数。
1、定义策略函数
2、多进程循环输入参数数值
3、获取回测报告，生成DataFrame格式
4、排序
本程序以双均线策略为例，优化两均线长短周期参数。
'''


# 原策略中的参数定义语句需要删除！
def init(context):
    context.sec_id = 'SHSE.600000'
    subscribe(symbols=context.sec_id, frequency='1d', count=31, wait_group=True)


def on_bar(context, bars):
    close = context.data(symbol=context.sec_id, frequency='1d', count=31, fields='close')['close'].values
    MA_short = talib.MA(close, timeperiod=context.short)
    MA_long = talib.MA(close, timeperiod=context.long)
    position = context.account().position(symbol=context.sec_id, side=PositionSide_Long)
    if not position and not position:
        if MA_short[-1] > MA_long[-1] and MA_short[-2] < MA_long[-2]:
            order_target_percent(symbol=context.sec_id, percent=0.8, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
    elif position:
        if MA_short[-1] < MA_long[-1] and MA_short[-2] > MA_long[-2]:
            order_target_percent(symbol=context.sec_id, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)


# 获取每次回测的报告数据
def on_backtest_finished(context, indicator):
    data = [indicator['pnl_ratio'], indicator['pnl_ratio_annual'], indicator['sharp_ratio'], indicator['max_drawdown'],
            context.short, context.long]
    # 将回测报告加入全局list，以便记录
    context.list.append(data)


def run_strategy(short, long, a_list):
    from gm.model.storage import context
    # 用context传入参数
    context.short = short
    context.long = long
    # a_list一定要传入
    context.list = a_list
    '''
        strategy_id策略ID,由系统生成
        filename文件名,请与本文件名保持一致
        mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
        token绑定计算机的ID,可在系统设置-密钥管理中生成
        backtest_start_time回测开始时间
        backtest_end_time回测结束时间
        backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
        backtest_initial_cash回测初始资金
        backtest_commission_ratio回测佣金比例
        backtest_slippage_ratio回测滑点比例
    '''
    run(strategy_id='strategy_id',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='token_id',
        backtest_start_time='2017-05-01 08:00:00',
        backtest_end_time='2017-10-01 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=50000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)


if __name__ == '__main__':
    # 生成全局list
    manager = multiprocessing.Manager()
    a_list = manager.list()
    # 循环输入参数数值回测
    for short in range(5, 10, 2):
        for long in range(10, 21, 5):
            process = multiprocessing.Process(target=run_strategy, args=(short, long, a_list))
            process.start()
            process.join()
    # 回测报告转化成DataFrame格式
    a_list = np.array(a_list)
    final = pd.DataFrame(a_list,
                         columns=['pnl_ratio', 'pnl_ratio_annual', 'sharp_ratio', 'max_drawdown', 'short', 'long'])
    # 回测报告排序
    final = final.sort_values(axis=0, ascending=False, by='pnl_ratio')
    print(final)