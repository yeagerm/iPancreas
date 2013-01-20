import csv
from rpy2.robjects.vectors import DataFrame
from rpy2.robjects.packages import importr
import rpy2.robjects.lib.ggplot2 as ggplot2

r_base = importr('base')

class DexcomCharts():
	"""Produces charts for Dexcom data via R."""

	def __init__(self, dex_name):

		self.dexcom_data = DataFrame.from_csvfile(dex_name)

	def summarize(self):
		"""Print R's summary of the data."""
		
		dexcom_summary = r_base.summary(self.dexcom_data.rx2('blood_glucose'))

		print
		print "Summary of Dexcom blood glucose data:"
		print

		for k, v in dexcom_summary.iteritems():
		   print("%s: %.3f\n" %(k, v))

def main():
	dc = DexcomCharts('raw/all_dexcom.csv')
	dc.summarize()

if __name__ == '__main__':
	main()