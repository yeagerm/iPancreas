import csv
import datetime

def main():

	output = csv.writer(open('../raw/all_dexcom.csv', 'w'))

	header = ['timestamp', 'blood_glucose']

	output.writerow(header)
	
	with open('../raw/receiver1.csv', 'rb') as f:
		rdr = csv.reader(f, delimiter = '\t', quoting = csv.QUOTE_NONE)
		rdr.next()
		
		for row in rdr:
			row_to_write = []
			pair = row[3].split('.')
			time = datetime.datetime.strptime(pair[0], "%Y-%m-%d %H:%M:%S")
			row_to_write.append(time.strftime("%Y-%m-%d %H:%M:%S"))
			row_to_write.append(row[4])
			output.writerow(row_to_write)

	with open('../raw/receiver2.csv', 'rb') as f:
		rdr = csv.reader(f, delimiter = '\t', quoting = csv.QUOTE_NONE)
		rdr.next()
		
		for row in rdr:
			row_to_write = []
			pair = row[3].split('.')
			time = datetime.datetime.strptime(pair[0], "%Y-%m-%d %H:%M:%S")
			row_to_write.append(time.strftime("%Y-%m-%d %H:%M:%S"))
			row_to_write.append(row[4])
			output.writerow(row_to_write)

	with open('../raw/receiver3.csv', 'rb') as f:
		rdr = csv.reader(f, delimiter = '\t', quoting = csv.QUOTE_NONE)
		rdr.next()
		
		for row in rdr:
			row_to_write = []
			pair = row[3].split('.')
			time = datetime.datetime.strptime(pair[0], "%Y-%m-%d %H:%M:%S")
			row_to_write.append(time.strftime("%Y-%m-%d %H:%M:%S"))
			row_to_write.append(row[4])
			output.writerow(row_to_write)
		
if __name__ == "__main__":
    main()