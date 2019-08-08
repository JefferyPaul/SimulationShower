import pandas as pd
from datetime import *
from Simulation import *
import os
from pyecharts.charts import Line, Grid, Page
from pyecharts import options as opts
from pyecharts.render import make_snapshot
from pyecharts.globals import ThemeType
from tools import get_round_pos


"""
	for Simulation Preview
"""


def set_a_trader_simulation(path_trader_folder):
	path_RAS, path_Trades, path_Pnls = [""] * 3
	if os.path.isfile(os.path.join(path_trader_folder, 'RawArbSignals.csv')):
		path_RAS = os.path.join(path_trader_folder, 'RawArbSignals.csv')
	if os.path.isfile(os.path.join(path_trader_folder, 'Trades.csv')):
		path_Trades = os.path.join(path_trader_folder, 'Trades.csv')
	if os.path.isfile(os.path.join(path_trader_folder, 'TraderPnls.csv')):
		path_Pnls = os.path.join(path_trader_folder, 'TraderPnls.csv')

	trader_name = ' - '.join(str(path_trader_folder).split('\\')[-2:])
	trader_simulation_obj = Simulation(name=trader_name)
	trader_simulation_obj.files_set_data(
		file_RAS=path_RAS,
		file_Trades=path_Trades,
		file_Pnl=path_Pnls
	)
	return trader_simulation_obj


def draw_pnl(trader_sim_obj) -> Grid:
	# 【1】 画Returns
	trader_name = trader_sim_obj.name
	df_Pnl = pd.DataFrame(trader_sim_obj.Data.Pnl)
	df_Pnl = df_Pnl.sort_values(by='Date')
	df_Pnl['cumsum'] = df_Pnl['Returns'].cumsum()
	x_list = df_Pnl['Date'].dt.date.to_list()
	y_list = df_Pnl['cumsum'].to_list()

	line_returns = (
		Line()
		.add_xaxis(x_list)
		.add_yaxis(series_name=trader_name, y_axis=y_list)
		.set_global_opts(
			title_opts=opts.TitleOpts(title='Returns', pos_top='10%'),
			legend_opts=opts.LegendOpts(pos_top='0%'),
			datazoom_opts=opts.DataZoomOpts(is_show=True, xaxis_index=[0, 1], pos_top='60%'),
			xaxis_opts=opts.AxisOpts(
				splitline_opts=opts.SplitLineOpts(is_show=True),
				is_scale=True,
			),
			yaxis_opts=opts.AxisOpts(is_scale=True),
		)
		.set_series_opts(
			label_opts='False',
			markpoint_opts=opts.MarkPointOpts(
				data=[
					opts.MarkPointItem(type_='max', symbol='circle'),
				]
			),
		)
	)

	# 【2】 画MDD
	df_Pnl['cummax'] = df_Pnl['cumsum'].cummax()
	df_Pnl['drawDown'] = df_Pnl['cumsum'] - df_Pnl['cummax']
	x_list = df_Pnl['Date'].dt.date.to_list()
	round_n = get_round_pos(df_Pnl['drawDown'])
	y_list = round(df_Pnl['drawDown'], round_n).to_list()

	line_mdd = (
		Line()
		.add_xaxis(x_list)
		.add_yaxis(
			series_name=trader_name,
			y_axis=y_list,
		)
		.set_global_opts(
			title_opts=opts.TitleOpts(title='MDD', pos_top='75%'),
			legend_opts=opts.LegendOpts(is_show=False),
			datazoom_opts=opts.DataZoomOpts(is_show=False, xaxis_index=[0, 1]),
			xaxis_opts=opts.AxisOpts(
				is_scale=True,
				splitline_opts=opts.SplitLineOpts(is_show=True)
			),
			yaxis_opts=opts.AxisOpts(
				# max_=0,
				# min_=y_min - abs((y_max - y_min)) * 0.1 ,
				is_scale=True,
				splitline_opts=opts.SplitLineOpts(is_show=True,)
			),
		)
		.set_series_opts(
			label_opts='False',
			markpoint_opts=opts.MarkPointOpts(
				data=[
					# opts.MarkPointItem(type_='max', symbol='roundRect'),
					opts.MarkPointItem(type_='min', symbol='circle'),
				]
			),
		)
	)

	# 组合gird
	grid = (
		Grid(init_opts=opts.InitOpts(width='1200px', height='800px'))
		.add(line_returns, grid_opts=opts.GridOpts(pos_bottom='40%'))
		.add(line_mdd, grid_opts=opts.GridOpts(pos_top='65%', pos_bottom='5%'))
	)
	return grid


def draw_band_and_trades(trader_sim_obj) -> Grid:
	def band1(x):
		l = list(x)
		l.sort()
		m = sum(l[1:3]) / 2
		l2 = [i for i in l if (i > m * 0.95) * (i < m * 1.05)]
		return max(l2)

	def band2(x):
		l = list(x)
		l.sort()
		m = sum(l[1:3]) / 2
		l2 = [i for i in l if (i > m * 0.95) * (i < m * 1.05)]
		return min(l2)

	# 【1】 Band
	trader_name = trader_sim_obj.name
	# 拿数据
	df_band = pd.DataFrame(trader_sim_obj.Data.Band)
	df_band.set_index(keys='DateTime', drop=True, inplace=True)
	df_bar = pd.DataFrame(trader_sim_obj.Data.Bar)
	# 转换 计算 BarPx
	df_bar_open_pv = df_bar.pivot_table(values='Open', index='DateTime', columns='ticker', aggfunc='mean')
	ticker1 = df_bar[df_bar['tickerNum'] == '1']['ticker'].to_list()[-1]
	ticker2 = df_bar[df_bar['tickerNum'] == '2']['ticker'].to_list()[-1]
	df_bar_open_pv['px'] = df_bar_open_pv[ticker1] / df_bar_open_pv[ticker2]
	# 筛选Band  合并 Band和BarPx
	df_band_px = pd.concat([df_band, df_bar_open_pv[['px']]], axis=1)
	df_band_px['Band1'] = df_band_px[['BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']].apply(func=band1, axis=1)
	df_band_px['Band2'] = df_band_px[['BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']].apply(func=band2, axis=1)
	df_band_px = df_band_px[['Band1', 'Band2', 'px']]
	round_n = get_round_pos(df_band_px['px'])
	df_band_px['px'] = round(df_band_px['px'], round_n)

	x_list = df_band_px.index.to_list()

	line_band = (
		Line()
		.add_xaxis(xaxis_data=x_list)
		.add_yaxis(
			series_name='Band1',
			y_axis=df_band_px['Band1'].to_list(),
		)
		.add_yaxis(
			series_name='Band2',
			y_axis=df_band_px['Band2'].to_list(),
		)
		.add_yaxis(
			series_name='BarPx',
			y_axis=df_band_px['px'].to_list(),
		)
		.set_global_opts(
			title_opts=opts.TitleOpts(title='Band', pos_top='10%'),
			legend_opts=opts.LegendOpts(pos_top='5%'),
			datazoom_opts=opts.DataZoomOpts(is_show=True, xaxis_index=[0, 1, 2], pos_top='50%'),
			yaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True,)),
			xaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True,)),
			# yaxis_opts=opts.AxisOpts(
			# 	max_=y_max+abs((y_max-y_min))*0.15,
			# 	min_=y_min-abs((y_max-y_min))*0.15
			# )
		)
	)

	# 【2】 画Trades
	# 数据
	df_position = pd.DataFrame()
	df_trades = pd.DataFrame(trader_sim_obj.Data.Trades)
	list_ticker = df_trades['Ticker'].unique().tolist()

	# 用trades 计算 position
	# 使用的方法比较复杂，
	#       能处理 对有跨交易日持仓的情况；
	#       用于显示持仓，而不是成交，因为只是成交的话无法对成交盈亏有所了然
	ticker_position = {}
	for ticker_i in list_ticker[0]:
		ticker_position[ticker_i] = {'Buy': [0], 'Sell': [0], 'netPos': [0]}
		df_i_trades = df_trades[df_trades['Ticker'] == ticker_i]
		df_i_trades = df_i_trades[['DateTime', 'Direction', 'OffsetFlag', 'TradedPrice', 'TradedVolume']]
		df_i_trades.sort_values(by='DateTime', inplace=True)
		l_data = df_i_trades[['OffsetFlag', 'Direction', 'TradedVolume']].to_dict('record')
		for d in l_data:
			offset_flag = d['OffsetFlag']
			direction = d['Direction']
			traded_volume = d['TradedVolume']
			tv = ((offset_flag == 'Open') * 2 - 1) * traded_volume
			td = ['Sell', 'Buy'][
				int(({'Buy': 1, 'Sell': -1}[direction] * ((offset_flag == 'Open') * 2 - 1)) / 2 + 0.5)]

			volume0 = {}
			volume0['Buy'] = ticker_position[ticker_i]['Buy'][-1]
			volume0['Sell'] = ticker_position[ticker_i]['Sell'][-1]
			volume0['netPos'] = ticker_position[ticker_i]['netPos'][-1]
			if volume0 == 0 and tv < 0:
				ticker_position[ticker_i]['Buy'].append(volume0['Buy'] )
				ticker_position[ticker_i]['Sell'].append(volume0['Sell'])
				ticker_position[ticker_i]['netPos'].append(volume0['netPos'])
			else:
				for bs in ['Buy', 'Sell']:
					if bs == td:
						ticker_position[ticker_i][bs].append(volume0[bs]+tv)
					else:
						ticker_position[ticker_i][bs].append(volume0[bs])
				ticker_position[ticker_i]['netPos'].append(
					ticker_position[ticker_i]['Buy'][-1] - ticker_position[ticker_i]['Sell'][-1]
				)
		# print(df_position, ticker_position[ticker_i])
		df_position[ticker_i] = ticker_position[ticker_i]['netPos'][1:]

	# position 数据处理， 规整index轴
	df_position['DateTime'] = df_trades['DateTime']
	df_position.drop_duplicates(subset='DateTime', keep='last', inplace=True)
	df_position.set_index('DateTime', inplace=True, drop=True)
	df_position_all = df_position.reindex(index=df_band_px.index.to_list(), method='ffill')
	df_position_all.fillna(value=0, inplace=True)
	x = df_position_all.index.to_list()

	# 画图
	# 仅显示 某一个 ticker的 trades和px
	# TODO arb（pair成交）的情况，用arbPx图，也是一个图啊
	i_ticker = df_position_all.columns.to_list()[0]

	y_trades = df_position_all[i_ticker].to_list()
	line_trades = (
		Line()
		.add_xaxis(x)
		.add_yaxis(
			series_name=i_ticker,
			y_axis=y_trades,
			yaxis_index=0,
		)
		.set_global_opts(
			title_opts=opts.TitleOpts(title='Trades', pos_top='65%'),
			legend_opts=opts.LegendOpts(pos_top='60%'),
			datazoom_opts=opts.DataZoomOpts(is_show=False, xaxis_index=[0, 1, 2]),
			yaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True,)),
			xaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True,)),
		)
	)

	# ticker 的bar px
	df_ticker_i_px = pd.DataFrame(df_bar.loc[df_bar['ticker'] == i_ticker, ['DateTime', 'Open']])
	df_ticker_i_px.set_index(keys='DateTime', drop=True, inplace=True)
	df_ticker_i_px = df_ticker_i_px.reindex(index=df_band_px.index.to_list(), method='ffill')
	y_px_open = df_ticker_i_px['Open'].to_list()
	line_ticker_px = (
		Line()
		.add_xaxis(x)
		.add_yaxis(
			"价格",
			y_px_open,
			yaxis_index=1,
		)
		.set_global_opts(
			title_opts=opts.TitleOpts(title='Px-Open', pos_top='65%', pos_right='0%'),
			legend_opts=opts.LegendOpts(pos_top='63%'),
			datazoom_opts=opts.DataZoomOpts(is_show=False, xaxis_index=[0, 1, 2]),
			# yaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True, )),
			xaxis_opts=opts.AxisOpts(is_scale=True),
			yaxis_opts=opts.AxisOpts(position='right', is_scale=True, name='Px'),
		)
	)

	# 组合gird
	grid = (
		Grid(init_opts=opts.InitOpts(width='1200px', height='800px'))
		.add(line_band, grid_opts=opts.GridOpts(pos_top='5%', pos_bottom='50%'))
		.add(line_trades, grid_opts=opts.GridOpts(pos_top='55%', pos_bottom='5%'))
		.add(line_ticker_px, grid_opts=opts.GridOpts(pos_top='55%', pos_bottom='5%'))
	)
	return grid


def draw_trader_preview(trader_folder_path) -> [Page, str]:
	sim_obj = set_a_trader_simulation(
		path_trader_folder=trader_folder_path
	)
	trader_name = sim_obj.name
	grid_pnl = draw_pnl(sim_obj)
	grid_band_trades = draw_band_and_trades(sim_obj)

	page = (
		Page()
			.add(grid_pnl)
			.add(grid_band_trades)
	)
	return page, trader_name


def strategy_simulation_trader_preview(path_root):
	if not os.path.isdir(path_root):
		print('Path Wrong: %s' % path_root)
		return
	path_output_folder = os.path.join(path_root, 'SimulationPreview')
	if not os.path.exists(path_output_folder):
		os.mkdir(path_output_folder)
	for i_name in os.listdir(path_root):
		path_trader_folder = os.path.join(path_root, i_name)
		if not os.path.isdir(path_trader_folder):
			continue
		if not(os.path.exists(os.path.join(path_trader_folder, 'RawArbSignals.csv')) &
		       os.path.exists(os.path.join(path_trader_folder, 'TraderPnls.csv'))):
			continue

		path_trader_output = os.path.join(path_output_folder, i_name)
		page, trader_name = draw_trader_preview(trader_folder_path=path_trader_folder)
		page.render('%s_%s.html' % (path_trader_output, trader_name))



# TODO 数据统计项展示


if __name__ == '__main__':
	r = 'F:\Data\SimulationData\sim_AP'
	strategy_simulation_trader_preview(path_root=r)

# TODO simulation-strategy 各trader returns
# TODO simulation-strategy 各trader 同pair比较

