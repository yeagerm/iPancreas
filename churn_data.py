from BeautifulSoup import BeautifulStoneSoup, Tag, NavigableString
from BeautifulSoup import BeautifulSoup as BS
import argparse
import datetime
import sys
import re
import csv

# escaped HTML to open italics
OI = "&lt;i&gt;"

# escaped HTML to close italics
CLI = "&lt;/i&gt;"

# escaped HTML line break
BREAK = "&lt;br/&gt;"

class Log():
    """A Timeline-compliant XML data structure for diabetes logbook data."""

    def __init__(self, out):
        """Initializes a Log object."""
        
        self.file_base = "events"

        self.soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")

        self.data = self.soup.data

        self.days = 0

    def add_event(self, event):
        """Inserts a new event in the XML logbook file."""

        self.data.insert(0, event)

    def print_XML(self):
        """Print XML to daily-batched files."""

        events = self.data.findAll('event')

        xml_out = open(self.file_base+'0.xml', 'w')

        last_day = self.get_date(events[0]['start'])

        soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")

        day_data = soup.data

        for event in events:
            if self.get_date(event['start']) == last_day:
                day_data.insert(0, event)
            else:
                print >> xml_out, soup.prettify()
                soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")
                day_data = soup.data
                self.days += 1
                xml_out = open(self.file_base+str(self.days)+'.xml', 'w')
                last_day = self.get_date(event['start'])
                day_data.insert(0,event)

        print >> xml_out, soup.prettify()

    def get_date(self, str):
        """Return date from Timeline-compliant XML event start attribute."""

        return datetime.datetime.strptime(str[:10], "%Y-%m-%d")

class YFD():

    def __init__(self, csv_name):

        self.reader = csv.reader(open(csv_name, 'rb'), delimiter='\t')

    def parse_yfd(self, log):
        """Extract and write to file data from a your.FlowingData tab-delim .csv file."""

        for row in self.reader:
            if row[0] == 'carbs':
                # t_str format is e.g., April 12, 2012, 4:10 p.m.
                t_str = row[3].replace(".","")
                t = datetime.datetime.strptime(t_str, "%B %d, %Y, %I:%M %p")
                # new_t_str format should be e.g., 2012-01-01 00:00:00-05:00
                new_t_str = t.strftime("%Y-%m-%d %H:%M:%S")
                # TODO: remove hard-coded timezone offset!
                new_t_str = new_t_str + "-05:00"
                c = Carbs(row[1], row[2], new_t_str, row[4])
                c.create_event()
                log.add_event(c.event)

        log.print_XML()

class Carbs():

    def __init__(self, g, desc, t, conf):

        self.grams = g

        self.content = desc

        self.time = t

        self.confidence = conf

        self.event = None

    def get_confidence(self):
        """Return string translating hastag confidence into human-readable string."""

        if self.confidence == "nutrition_facts":
            return "Based on nutrition facts label."
        elif self.confidence == "guesstimating":
            return "Guesstimated from rules-of-thumb, prior experience, or nutrition facts without precise portion measurement."
        elif self.confidence == "no_clue":
            return "Very uncertain guessing, often occurs when eating out."
        else:
            return "Unknown."

    def create_event(self):
        """Package content of Carbs object as a Timeline-compliant XML event."""

        soup = BeautifulStoneSoup("<event/>")

        self.event = soup.event

        self.event['start'] = self.time

        self.event['title'] = "Carbs: %d" %int(float(self.grams))

        self.event.string = "%sAte:%s %s.%s%sConfidence level of carb count:%s %s" %(OI, CLI, self.content, BREAK, OI, CLI, self.get_confidence())

class Dexcom():

    def __init__(self, xml_name):

        self.file_base = "dex"

        self.xml_file = open(xml_name, 'rU')

    def get_date(self, reading):
        """Return the date from a Dexcom XML object representing a single BG reading."""

        return datetime.datetime.strptime(reading['displaytime'][:10], "%Y-%m-%d")

    def parse_dexcom(self):
        """Extract and write to daily-batched files data from a Dexcom .xml output file."""

        xml_out = open(self.file_base+'0.txt', 'w')
        xsoup = BeautifulStoneSoup(self.xml_file, selfClosingTags=['Meter','Sensor'])
        readings = xsoup.findAll('sensor')

        last_day = self.get_date(readings[0])
        count = 0

        for reading in readings:
            if self.get_date(reading) == last_day:
                print >> xml_out, reading['displaytime'][:-4] + "," + reading['value']
            else:
                count += 1
                last_day = self.get_date(reading)
                xml_out = open(self.file_base+str(count)+'.txt','w')
                print >> xml_out, reading['displaytime'][:-4] + "," + reading['value']

class Ping():

    def __init__(self, csv_name):

        self.file_base = "ping"

        self.reader = csv.reader(open(csv_name, 'rb'))

    def get_date(self, str):

        return datetime.datetime.strptime(str[:10], "%Y-%m-%d")

    def parse_ping(self):
        """Extract and write to daily-batched files data from a OneTouch Ping .csv output file."""

        clock = re.compile("(\d+):(\d\d)")

        readings = []

        for row in self.reader:
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
                readings.append(my_date + "," + str(int(value)))

        csv_out = open(self.file_base + '0.txt', 'w')

        last_day = self.get_date(readings[0])
        count = 0

        for reading in readings:
            if self.get_date(reading) == last_day:
                print >> csv_out, reading
            else:
                count += 1
                last_day = self.get_date(reading)
                csv_out = open(self.file_base+str(count)+'.txt', 'w'    )
                print >> csv_out, reading

def insert_num_days(log):
    """Insert the number of days of data into logbook.html where required."""

    soup = BS(open("logbook.html",'rU'))

    body = soup.body

    body['onload'] = "onLoad(%d);" %log.days

    out = open("logbook.html", 'w')

    print >> out, soup.prettify()
            
def main():
    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    parser.add_argument('-p', '--ping', action = 'store', dest = "ping_name", help='name of OneTouch Ping csv file')
    parser.add_argument('-y', '--yfd', action = 'store', dest = "yfd_name", help='name of your.FlowingData csv file')
    parser.add_argument('-o', '--output', action = 'store', dest = "out_name", help='name/path of output XML file')

    args = parser.parse_args()

    d = Dexcom(args.dex_name)

    d.parse_dexcom()

    p = Ping(args.ping_name)

    p.parse_ping()

    l = Log(args.out_name)

    yfd = YFD(args.yfd_name)

    yfd.parse_yfd(l)

    insert_num_days(l)

if __name__=="__main__":
    main()
