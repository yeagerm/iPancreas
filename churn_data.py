from BeautifulSoup import BeautifulStoneSoup, Tag, NavigableString
from BeautifulSoup import BeautifulSoup as BS
import argparse
import datetime
import sys
import re
import csv
import numpy

# escaped HTML to open italics
OI = "&lt;i&gt;"

# escaped HTML to close italics
CLI = "&lt;/i&gt;"

# escaped HTML line break
BREAK = "&lt;br/&gt;"

class Log():
    """A Timeline-compliant XML data structure for diabetes logbook data."""

    def __init__(self):
        """Initializes a Log object."""
        
        self.file_base = "events/events"

        self.soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")

        self.data = self.soup.data

        self.days = 0

        self.dates = []

    def add_event(self, event):
        """Inserts a new event in the XML logbook file."""

        self.data.insert(0, event)

    def print_XML(self):
        """Print XML to daily-batched files."""

        events = self.data.findAll('event')

        xml_out = open(self.file_base+'0.xml', 'w')

        last_day = self.get_date(events[0]['start'])

        self.dates.append(self.get_date(events[0]['start']))

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
                self.dates.append(self.get_date(event['start']))
                day_data.insert(0,event)

        print >> xml_out, soup.prettify()

    def get_date(self, str):
        """Return date from Timeline-compliant XML event start attribute."""

        return datetime.datetime.strptime(str[:10], "%Y-%m-%d")

    def endpoints(self):
        """Print daily-batched files of endpoints."""

        count = 0

        for day in self.dates:
            out = open('endpoints/endpoints'+str(count)+'.txt','w')
            print >> out, str(day) + ",25\n" + str(day.date()) + " 12:00:00,50\n" + str(day.date()) + " 23:59:59,25"
            count += 1

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
                # new_t_str format should be e.g., 2012-01-01 00:00:00
                new_t_str = t.strftime("%Y-%m-%d %H:%M:%S")
                end = t + datetime.timedelta(0,5400)
                if end.day != t.day:
                    t2 = datetime.datetime(t.year, t.month,t.day+1,0,0)
                    t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
                    end_str = end.strftime("%Y-%m-%d %H:%M:%S")
                    c2 = Carbs(row[1], row[2], t2_str, end_str, row[4])
                    c2.create_event()
                    log.add_event(c2.event)
                    end = datetime.datetime(t.year,t.month,t.day,23,59)
                end_str = end.strftime("%Y-%m-%d %H:%M:%S")
                c = Carbs(row[1], row[2], new_t_str, end_str, row[4])
                c.create_event()
                log.add_event(c.event)

        log.print_XML()

class Carbs():

    def __init__(self, g, desc, s, e, conf):

        self.grams = g

        self.content = desc

        self.start = s

        self.end = e

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

        self.event['start'] = self.start

        self.event['end'] = self.end

        self.event['title'] = "Carbs: %d" %int(float(self.grams))

        self.event.string = "%sAte:%s %s.%s%sConfidence level of carb count:%s %s" %(OI, CLI, self.content, BREAK, OI, CLI, self.get_confidence())

class Dexcom():

    def __init__(self, xml_name):

        self.file_base = "dex/dex"

        self.xml_file = open(xml_name, 'rU')

        self.stats_writer = csv.writer(open(xml_name.replace('.xml', '_stats.csv'), 'w'))

        self.bubble_writer = csv.writer(open(xml_name.replace('.xml', '_bubble.csv'), 'w'))

        self.readings = self.get_readings()

    def get_date(self, reading):
        """Return the date from a Dexcom XML object representing a single BG reading."""

        return datetime.datetime.strptime(reading['displaytime'][:10], "%Y-%m-%d")

    def get_time(self, reading):
        """Return the hour of the day as a 24-hr clock integer from a Dexcom XML object representing a single BG reading."""

        t = datetime.datetime.strptime(reading['displaytime'][:-4], "%Y-%m-%d %H:%M:%S")

        return t.hour

    def get_date_str(self, reading):
        """Return a string of the date from a Dexcom XML object representing a single BG reading."""

        return reading['displaytime'][:10]

    def get_readings(self):
        """Return array of XML objects each representing a blood glucose reading."""

        xsoup = BeautifulStoneSoup(self.xml_file, selfClosingTags=['Meter','Sensor'])
        return xsoup.findAll('sensor')

    def stats(self):
        """Write to a single .csv file various per-day statistics from Dexcom data."""

        last_day = self.get_date(self.readings[0])
        count = 0

        days = {}
        days[count] = ([],[],[],[],self.get_date_str(self.readings[0]))

        for reading in self.readings:
            if self.get_date(reading) == last_day:
                days[count][0].append(int(reading['value']))
                if int(reading['value']) <= 65:
                    days[count][1].append(int(reading['value']))
                elif int(reading['value']) > 65 and int(reading['value']) <= 140:
                    days[count][2].append(int(reading['value']))
                elif int(reading['value']) > 140:
                    days[count][3].append(int(reading['value']))
                else:
                    print "I can't classify this BG reading: %s!" %reading['value']
            else:
                count += 1
                days[count] = ([int(reading['value'])],[],[],[],self.get_date_str(reading))
                if int(reading['value']) <= 65:
                    days[count][1].append(int(reading['value']))
                elif int(reading['value']) > 65 and int(reading['value']) <= 140:
                    days[count][2].append(int(reading['value']))
                elif int(reading['value']) > 140:
                    days[count][3].append(int(reading['value']))
                else:
                    print "I can't classify this BG reading: %s!" %reading['value']
                last_day = self.get_date(reading)

        header = ['date', 'average', 'standard_deviation', 'percentage_low', 'percentage_target', 'percentage_high']

        self.stats_writer.writerow(header)

        for day in days.values():
            ave = int(round(numpy.average(day[0])))
            std = int(round(numpy.std(day[0])))
            low = float(len(day[1]))/float(len(day[0])) * 100
            target = float(len(day[2]))/float(len(day[0]))*100
            high = float(len(day[3]))/float(len(day[0]))*100
            self.stats_writer.writerow([day[4],ave,std,low,target,high])

    def bubble_chart(self):
        """Export .csv that can be uploaded to Google Docs to make a bubble chart."""

        header = ['id', 'time_of_day', 'blood_glucose', 'low_carb', 'freq']

        self.bubble_writer.writerow(header)

        eleven = [{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]

        twelve = [{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]

        bins = [40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420]

        for reading in self.readings:
            hour = self.get_time(reading)
            bg = int(reading['value'])
            for bin in bins:
                if bg < bin and bg > last_bin:
                    bg = bin
                    break
                elif bg < bin and bin == 40:
                    bg = bin
                    break
                last_bin = bin

            if self.get_date_str(reading)[:4] == "2012":
                try:
                    twelve[hour][bg] += 1
                except KeyError:
                    twelve[hour][bg] = 1
            else:
                try:
                    eleven[hour][bg] += 1
                except KeyError:
                    eleven[hour][bg] = 1

        count = 0

        for dct in twelve:
            for val in dct:
                group = self.get_class(val)
                self.bubble_writer.writerow(['', count, val, group, dct[val]])
            count += 1

        count = 0

        for dct in eleven:
            for val in dct:
                group = self.get_class(val)
                self.bubble_writer.writerow(['', count, val, group, dct[val]])
            count += 1

    def get_class(self, bg):
        """Return class descriptor of BG bin."""

        low = ['low',40,60]

        perfect = ['perfect',80,100,120]

        target = ['target',140]

        high = ['high',160,180]

        too_high = ['too_high',200,220,240]

        hyper = ['hyper',260,280,300,320,340,360,380,400,420]

        lst = [low, perfect, target, high, too_high, hyper]

        for l in lst:
            if bg in l:
                return l[0]

    def logbook(self):
        """Write to daily-batched files data from a Dexcom .xml output file."""

        xml_out = open(self.file_base+'0.txt', 'w')
        last_day = self.get_date(self.readings[0])
        count = 0

        for reading in self.readings:
            if self.get_date(reading) == last_day:
                print >> xml_out, reading['displaytime'][:-4] + "," + reading['value']
            else:
                count += 1
                last_day = self.get_date(reading)
                xml_out = open(self.file_base+str(count)+'.txt','w')
                print >> xml_out, reading['displaytime'][:-4] + "," + reading['value']

class Ping():

    def __init__(self, csv_name):

        self.file_base = "ping/ping"

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
                my_date = dt.isoformat().replace("T", " ")
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

    body['onload'] = "onLoad(%d);" %(log.days+1)

    out = open("logbook.html", 'w')

    print >> out, soup.prettify()
            
def main():
    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    parser.add_argument('-p', '--ping', action = 'store', dest = "ping_name", help='name of OneTouch Ping csv file')
    parser.add_argument('-y', '--yfd', action = 'store', dest = "yfd_name", help='name of your.FlowingData csv file')

    args = parser.parse_args()

    p = Ping(args.ping_name)

    p.parse_ping()

    d = Dexcom(args.dex_name)

    d.logbook()

    l = Log()

    yfd = YFD(args.yfd_name)

    yfd.parse_yfd(l)

    insert_num_days(l)

    l.endpoints()

if __name__=="__main__":
    main()
