from BeautifulSoup import BeautifulStoneSoup, Tag, NavigableString
import argparse
import datetime
import sys
import re
import csv

class Log():
    """A Timeline-compliant XML data structure for diabetes logbook data."""

    def __init__(self, out):
        """Initializes a Log object."""
        
        self.out_file = out

        self.soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")

    def add_event(self, event):
        """Inserts a new event in the XML logbook file."""

        self.soup.insert(0, event)

def parse_dexcom(xml_name):
    xml_file = open(xml_name, 'rU')
    xml_out = open(xml_name.replace('.xml','.txt'), 'w')
    xsoup = BeautifulStoneSoup(xml_file, selfClosingTags=['Meter','Sensor'])
    readings = xsoup.findAll('sensor')
    for reading in readings:
        print >> xml_out, reading['displaytime'][:-4] + "," + reading['value']

def parse_ping(csv_name):
    csv_file = open(csv_name, 'rb')
    csv_out = open(csv_name.replace('.csv', '.txt'), 'w')
    reader = csv.reader(csv_file)
    clock = re.compile("(\d+):(\d\d)")
    for row in reader:
        if "Meter" in row:
            day_string = row[0]
            day_parts = day_string.split("/")
            year = "20" + day_parts[2]
            time_string = row[1]
            time = clock.match(row[1])
            hour = time.group(1)
            minutes = time.group(2)
            if "PM" in time_string and hour != "12":
                hour = int(hour) + 12
            if "AM" in time_string and hour == "12":
                hour = 0
            dt = datetime.datetime(int(year), int(day_parts[0]), int(day_parts[1]), int(hour), int(minutes))
            my_date = dt.isoformat().replace("T", " ") + "-05:00"
            value = float(row[2])
            print >> csv_out, my_date + "," + str(int(value))

# TODO: add a method that will put the proper value of days in the onLoad(days) command in logbook.html
            
def main():
    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    parser.add_argument('-p', '--ping', action = 'store', dest = "ping_name", help='name of OneTouch Ping csv file')

    args = parser.parse_args()

    parse_dexcom(args.dex_name)

    # later make this a for loop and make argparser accept more than one csv
    parse_ping(args.ping_name)

if __name__=="__main__":
    main()
