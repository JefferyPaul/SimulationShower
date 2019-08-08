import os
import pandas as pd
from tools import get_round_pos

"""
	SimulationData
		Band - ['DateTime'(DateTime), 'BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']
		Bar - ['DateTime', ‘Ticker', 'TickerNum'('1' or '2'), 'Open', 'High', 'Low', 'Close', 'Volume']
		Trades = ['DateTime', 'Ticker', 'Direction', 'OffsetFlag', 'TradedPrice', 'TradedVolume'(perInitX), 'Commission'(perInitX)]
		Pnl = ['Date', 'Returns']
"""


class SimulationData:
	def __init__(self):
		self._Band = pd.DataFrame()
		self._Bar = {}
		self._Trades = pd.DataFrame()
		self._Pnl = pd.DataFrame()
		self._InitX = None

	@property
	def Band(self):
		return self._Band

	@property
	def Bar(self):
		return self._Bar

	@property
	def Trades(self):
		return self._Trades

	@property
	def Pnl(self):
		return self._Pnl

	@property
	def InitX(self):
		if self._InitX:
			return self._InitX
		else:
			return 1000

	@Band.setter
	def Band(self, band):
		self._Band = band

	@Bar.setter
	def Bar(self, bar):
		self._Bar = bar

	@Trades.setter
	def Trades(self, trades):
		self._Trades = trades

	@Pnl.setter
	def Pnl(self, pnl):
		self._Pnl = pnl

	@InitX.setter
	def InitX(self, initX):
		self._InitX = initX


class Simulation:
	def __init__(self, name, data_type=None):
		self._name = name
		self._type = data_type
		self.Data = SimulationData()

	@property
	def name(self):
		return self._name

	def __str__(self):
		return '%s' % self.name

	def file_set_band(self, file_path):
		df = pd.read_csv(file_path)
		initX = df['InitX'].to_list()[-2]
		if not initX:
			self.Data.InitX = initX

		df['DateTime'] = df['Date'] + ' ' + df['Time']
		columns = ['DateTime', 'BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']
		try:
			df = df[columns]

			round_n = get_round_pos(df['BuyEntry'])
			df[['BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']] = \
				round(df[['BuyEntry', 'BuyExit', 'SellEntry', 'SellExit']], round_n)

			df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
			self.Data.Band = df
		except Exception:
			pass

	def file_set_bar(self, file_path):
		df = pd.read_csv(file_path)
		initX = df['InitX'].to_list()[-2]
		if not initX:
			self.Data.InitX = initX

		df['DateTime'] = df['Date'] + ' ' + df['Time']
		ticker1 = df['Ticker1'].to_list()[-1]
		ticker2 = df['Ticker2'].to_list()[-1]
		columns = [
			'DateTime',
			'Open1', 'High1', 'Low1', 'Close1', 'Volume1',
			'Open2', 'High2', 'Low2', 'Close2', 'Volume2'
		]
		try:
			df = df[columns]
			df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
			df_ticker1 = df[['DateTime', 'Open1', 'High1', 'Low1', 'Close1', 'Volume1']]
			df_ticker2 = df[['DateTime', 'Open2', 'High2', 'Low2', 'Close2', 'Volume2']]
			df_ticker1.columns = ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']
			df_ticker2.columns = ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']
			df_ticker1.loc[:, 'ticker'] = ticker1
			df_ticker1.loc[:, 'tickerNum'] = '1'
			df_ticker2.loc[:, 'ticker'] = ticker2
			df_ticker2.loc[:, 'tickerNum'] = '2'

			df_concat = pd.concat([df_ticker1, df_ticker2], axis=0)

			self.Data.Bar = df_concat
		except Exception:
			pass

	def file_set_trades(self, file_path):
		df = pd.read_csv(file_path)
		df['DateTime'] = df['Date'] + ' ' + df['Time']
		columns = ['DateTime', 'Ticker', 'Direction', 'OffsetFlag', 'TradedPrice', 'TradedVolume', 'Commission']
		try:
			df = df[columns]
			df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S')
			df['TradedVolume'] = round(df['TradedVolume'] / self.Data.InitX, 2)
			df['Commission'] = round(df['Commission'] / self.Data.InitX, 2)
			self.Data.Trades = df
		except Exception:
			pass

	def file_set_pnl(self, file_path):
		df = pd.read_csv(file_path)
		columns = ['Date', 'Pnl']
		try:
			df = df[columns]
			df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
			df['Returns'] = df['Pnl'] / 1000000 / self.Data.InitX

			round_n = get_round_pos(df['Returns'])
			df['Returns'] = round(df['Returns'], round_n)
			self.Data.Pnl = df[['Date', 'Returns']]
		except Exception:
			pass

	def files_set_data(self, file_RAS='', file_RS='', file_Trades='', file_Pnl=''):
		if file_RAS:
			self.file_set_band(file_RAS)
			self.file_set_bar(file_RAS)
		if file_Trades:
			self.file_set_trades(file_Trades)
		if file_Pnl:
			self.file_set_pnl(file_Pnl)
