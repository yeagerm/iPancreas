import argparse
from bs4 import BeautifulSoup
import csv

def main():

	parser = argparse.ArgumentParser(description='Process the input arguments.')
	parser.add_argument('-y', '--year', action = 'store', type=int, dest = "year", help='Restrict data transfer to specified.')

	args = parser.parse_args()

	soup = BeautifulSoup("<Patient><SensorReadings></SensorReadings></Patient>", "xml")

	to_insert = []

	if not args.year:
		file_name = '../raw/all_dexcom.xml'
		with open('../raw/all_dexcom.csv') as f:
			rdr = csv.reader(f)
			rdr.next()
			for row in rdr:
				r = BeautifulSoup("<Sensor/>", 'xml')
				reading = r.Sensor
				reading['DisplayTime'] = row[0]
				reading['Value'] = row[1]
				to_insert.append(reading)
	else:
		file_name = '../raw/' + str(args.year) + '_dexcom.xml'
		with open('../raw/all_dexcom.csv') as f:
			rdr = csv.reader(f)
			rdr.next()
			for row in rdr:
				r = BeautifulSoup("<Sensor/>", 'xml')
				reading = r.Sensor
				if row[0].find(str(args.year)) != -1:
					reading['DisplayTime'] = row[0]
					reading['Value'] = row[1]
					to_insert.append(reading)


	to_insert.reverse()

	for tag in to_insert:
		soup.SensorReadings.insert(0, tag)

	with open(file_name, 'w') as o:
		print >> o, soup.prettify()

if __name__ == '__main__':
	main()