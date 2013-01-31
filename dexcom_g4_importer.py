from bs4 import BeautifulSoup
import csv

class G4Reader():
	"""Replicates the functionality of Dexcom.get_readings() in churn_data."""

	def __init__(self, dex):

		self.rdr = dex

		self.readings = self.get_readings()

	def get_readings(self):

		readings = []

		self.rdr.next()

		for row in self.rdr:
			soup = BeautifulSoup("<Sensor></Sensor>", "xml")
			reading = soup.Sensor
			reading['DisplayTime'] = row[3]
			reading['Value'] = row[4]
			if reading['Value'] == "Low":
				reading['Value'] = 39
			elif reading['Value'] == "High":
				reading['Value'] = 401
			readings.append(reading)

		return readings

		

	


