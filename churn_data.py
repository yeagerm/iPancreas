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

    def __init__(self, name):
        """Initializes a Log object."""
        
        self.file_base = "events/" + name + "_events"

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

        self.dates.append(last_day)

        soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")

        day_data = soup.data

        # REDO!
        for event in events:
            if self.get_date(event['start']) == last_day:
                day_data.insert(0, event)
            else:
                print >> xml_out, soup.prettify()
                soup = BeautifulStoneSoup("<data date-time-format='iso8601'></data>")
                day_data = soup.data
                self.days += 1
                last_day = self.get_date(event['start'])
                prev = self.dates[-1].date()
                if (last_day.date() - prev) > datetime.timedelta(1):
                    diff = (last_day.date() - prev).days
                    while diff > 1:
                        self.days += 1
                        xml_out = open(self.file_base+str(self.days)+'.xml', 'w')
                        print >> xml_out, ""
                        diff = diff - 1
                else:
                    day_data.insert(0,event)
                xml_out = open(self.file_base+str(self.days)+'.xml', 'w')
                self.dates.append(self.get_date(event['start']))

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

    def get_timestamp(self, t_str):
        """Return time from YFD time string."""

        # t_str format is e.g., April 12, 2012, 4:10 p.m.
        return datetime.datetime.strptime(t_str.replace(".",""), "%B %d, %Y, %I:%M %p")

    def format_time(self, t):
        """Return properly-formatted timestamp."""

        # new_t_str format should be e.g., 2012-01-01 00:00:00
        return t.strftime("%Y-%m-%d %H:%M:%S")

    def event(self, row, t):
        """Return an Event object."""

        return Event(row[0], row[1], row[2], t, row[4])

    def parse_yfd(self, carb_log, event_log, ex_log, hypo_log, bolus_log):
        """Extract and write to file data from a your.FlowingData tab-delim .csv file."""

        for row in self.reader:
            try:
                t = self.get_timestamp(row[3])
                new_t_str = self.format_time(t)
            except ValueError:
                pass
            if row[0] == 'carbs':
                # TODO: don't hardcode this 5400 seconds (= 90 minutes) for carb overlay time
                end = t + datetime.timedelta(0,5400)
                if end.day != t.day:
                    try:
                        t2 = datetime.datetime(t.year, t.month,t.day+1,0,0)
                    except ValueError:
                        t2 = datetime.datetime(t.year, t.month+1,1,0,0)
                    t2_str = self.format_time(t2)
                    end_str = self.format_time(end)
                    c2 = Carbs(row[1], row[2], t2_str, end_str, row[4])
                    c2.create_event()
                    carb_log.add_event(c2.event)
                    end = datetime.datetime(t.year,t.month,t.day,23,59)
                end_str = self.format_time(end)
                c = Carbs(row[1], row[2], new_t_str, end_str, row[4])
                c.create_event()
                carb_log.add_event(c.event)
            elif row[0] == 'ate' or row[0] == 'gnite' or row[0] == 'gmorn' or row[0] == 'symlin' or row[0] == 'coffee':
                e = self.event(row, new_t_str)
                e.create_event()
                event_log.add_event(e.event)
            elif row[0] == 'ran':
                #TODO: don't hardcode time estimate of 12 minutes out of the house per mile
                secs = int(float(row[1])) * 12 * 60
                end = t + datetime.timedelta(0,secs)
                end_str = self.format_time(end)
                r = Run(row[1], row[2], new_t_str, end_str)
                r.create_event()
                ex_log.add_event(r.event)

        carb_log.print_XML()
        event_log.print_XML()
        ex_log.print_XML()

class Event():

    def __init__(self, cat, count , desc, t, tag):

        self.type = cat

        self.count = count

        self.content = desc

        self.time = t

        self.hashtag = tag

        self.event = None

    def get_event_string(self):
        """Return string describing event in plain English."""

        if self.type == "ate":
            return "%sAte:%s %s." %(OI, CLI, self.content)
        elif self.type == "gnite":
            return "This is when I went to sleep."
        elif self.type == "gmorn":
            return "This is when I woke up."
        elif self.type == "symlin":
            return "%sInjected:%s %s units of Symlin." %(OI, CLI, self.count)
        elif self.type == "coffee":
            return "%sDrank:%s %s cup(s) of coffee." %(OI, CLI, self.count)
        elif self.type == "basal_rate_change":
            return "Changed basal rate to %s units per 24 hours." %(self.count)
        elif self.type == "ketones":
            return "Urinalysis showed %s ketones." %(self.content)

    def get_type(self):
        """Return string translating event type into human-readable string."""

        if self.type == "ate":
            return "Low-carb meal/snack"
        elif self.type == "gnite":
            return "Bedtime"
        elif self.type == "gmorn":
            return "Waketime"
        elif self.type == "symlin":
            return "Symlin injection"
        elif self.type == "coffee":
            return "Coffee"

    def create_event(self):
        """Package content of generic Event object as a Timeline-compliant XML event."""

        soup = BeautifulStoneSoup("<event/>")

        self.event = soup.event

        self.event['start'] = self.time

        self.event['title'] = self.get_type()

        self.event.string = self.get_event_string()

class Run():

    def __init__(self, miles, cat, s, e):

        self.miles = miles

        self.pace = cat

        self.start = s

        self.end = e

        self.event = None

    def get_pace(self):
        """Return string translating pace category into human-readable string."""

        if self.pace == "slow":
            return "Greater than 10:15 minutes/mile pace."
        elif self.pace == "sub1015":
            return "Between 10:00 and 10:15 minutes/mile pace."
        elif self.pace == "sub10":
            return "Between 9:45 and 10:00 minutes/mile pace."
        elif self.pace == "sub945":
            return "Between 9:30 and 9:45 minutes/mile pace."
        elif self.pace == "sub930":
            return "Under 9:30 minutes/mile pace."
        elif self.pace == "unknown":
            return "Pace unknown due to GPS error."
        else:
            return "Pace not recorded."

    def create_event(self):
        """Package content of Run object as a Timeline-compliant XML event."""

        soup = BeautifulStoneSoup("<event/>")

        self.event = soup.event

        self.event['start'] = self.start

        self.event['end'] = self.end

        self.event['title'] = "Exercise (running)"

        self.event.string = "%sRan:%s %s miles.%s%sPace:%s %s" %(OI,CLI,self.miles,BREAK,OI,CLI,self.get_pace())

class Carbs():

    def __init__(self, g, desc, s, e, conf):

        self.grams = g

        self.content = desc

        self.start = s

        self.end = e

        self.confidence = conf

        self.event = None

    def get_confidence(self):
        """Return string translating hashtag confidence into human-readable string."""

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

        self.day_writer = csv.writer(open(xml_name.replace('.xml','_day.csv'), 'w'))

        self.bubble_writer = csv.writer(open(xml_name.replace('.xml', '_bubble.csv'), 'w'))

        self.day_heat_writer = csv.writer(open(xml_name.replace('.xml','_day_heatmap.csv'), 'w'))

        self.time_heat_writer = csv.writer(open(xml_name.replace('.xml', '_time_heatmap.csv'), 'w'))

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

    def day_csv(self):
        """Export .csv that can be made into day boxplots directly in R."""

        header = ["timestamp","reading","weekday"]

        self.day_writer.writerow(header)

        for reading in self.readings:
            weekday = self.get_date(reading).weekday()
            bg = int(reading['value'])
            time = reading['displaytime']
            self.day_writer.writerow([time,bg,weekday])

    def day_heatmap(self):
        """Export .csv that can be made into a day-of-the-week heatmap directly in R."""

        header = ["","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        self.day_heat_writer.writerow(header)

        bins = range(50,420,10)

        bin_dicts = {}

        for bin in bins:
            bin_dicts[bin] = {}
            for i in range(7):
                bin_dicts[bin][i] = 0

        for reading in self.readings:
            weekday = self.get_date(reading).weekday()
            bg = int(reading['value'])
            for bin in bins:
                if bg < bin and bg > last_bin:
                    bg = bin
                    break
                elif bg < bin and bin == 50:
                    bg = bin
                    break
                last_bin = bin

            bin_dicts[bg][weekday] += 1

        kys = bin_dicts.keys()

        kys.sort()

        for k in kys:
            dct = bin_dicts[k]
            lst = [k]
            for day in dct:
                lst.append(dct[day])
            self.day_heat_writer.writerow(lst)

    def time_heatmap(self):
        """Export .csv that can be made into a time-of-day heatmap directly in R."""

        header = ["","midnight", "1 a.m.", "2 a.m.", "3 a.m.", "4 a.m.", "5 a.m.", "6 a.m.", "7 a.m.", "8 a.m.", "9 a.m.", "10 a.m.", "11 a.m.","noon", "1 p.m.", "2 p.m.", "3 p.m.", "4 p.m.", "5 p.m.", "6 p.m.", "7 p.m.", "8 p.m.", "9 p.m.", "10 p.m.", "11 p.m."]

        self.time_heat_writer.writerow(header)

        bins = range(50,420,10)

        bin_dicts = {}

        for bin in bins:
            bin_dicts[bin] = {}
            for i in range(24):
                bin_dicts[bin][i] = 0

        for reading in self.readings:
            hour = self.get_time(reading)
            bg = int(reading['value'])
            for bin in bins:
                if bg < bin and bg > last_bin:
                    bg = bin
                    break
                elif bg < bin and bin == 50:
                    bg = bin
                    break
                last_bin = bin

            bin_dicts[bg][hour] += 1

        kys = bin_dicts.keys()

        kys.sort()

        for k in kys:
            dct = bin_dicts[k]
            lst = [k]
            for hour in dct:
                lst.append(dct[hour])
            self.time_heat_writer.writerow(lst)

    def bubble_chart(self):
        """Export .csv that can be uploaded to Google Docs to make a bubble chart."""

        header = ['id', 'time_of_day', 'blood_glucose', 'group', 'freq']

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

    carb_log = Log("carb")

    event_log = Log("")

    ex_log = Log("ex")

    hypo_log = Log("hypo")

    bolus_log = Log("bolus")

    yfd = YFD(args.yfd_name)

    yfd.parse_yfd(carb_log, event_log, ex_log, hypo_log, bolus_log)

    insert_num_days(carb_log)

    carb_log.endpoints()

if __name__=="__main__":
    main()
