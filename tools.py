import pandas as pd
import numpy as np


def get_round_pos(df_series, plus=4):
	try:
		ave = df_series.mean()
	except:
		ave = np.mean(df_series)
	if ave < 0:
		str_ave = str(ave)
		n = 0
		for i in list(str_ave.split('.')[-1]):
			if i != '0':
				break
			n += 1
		round_n = n + 1 + plus
		return round_n
	else:
		str_ave = str(ave)
		n = -len(str_ave.split('.')[0])
		round_n = n + 2 + plus
		return round_n
