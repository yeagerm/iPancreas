from bs4 import BeautifulSoup, Tag, NavigableString
from dexcom_g4_importer import G4Reader as G4
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

    def __init__(self, name, d):
        """Initializes a Log object."""
        
        self.file_base = "events/" + name + "_events"

        self.soup = BeautifulSoup("<data date-time-format='iso8601'></data>", "xml")

        self.data = self.soup.data

        self.dates = d

    def add_event(self, event):
        """Inserts a new event in the XML logbook file."""

        self.data.insert(0, event)

    def print_XML(self):
        """Print XML to daily-batched files."""

        events = self.data.findAll('event')

        xmls = []

        soups = []

        for day in self.dates:
            xmls.append(open(self.file_base+str(self.dates.index(day))+'.xml', 'w'))
            soup = BeautifulSoup("<data date-time-format='iso8601'></data>", "xml")
            soups.append(soup)

        for day in self.dates:
            i = self.dates.index(day)
            for event in events:
                if self.get_date(event['start']) == day:
                    soups[i].data.insert(0, event)

        for soup in soups:
            if soup.data.event:
                i = soups.index(soup)
                print >> xmls[i], soup.prettify()

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

        # TODO: figure out other exceptions to standard Python abbreviations in YFD timestamps
        t_str = t_str.replace("Sept", "Sep")
        
        # t_str format is e.g., April 12, 2012, 4:10 p.m.
        if t_str.find(":") != -1:
            return datetime.datetime.strptime(t_str.replace(".",""), "%b %d, %Y, %I:%M %p")
        # t_str format contains "noon": Oct 16, 2012, noon
        elif t_str.find("noon") != -1:
            t_str = t_str.replace("noon", "12:00 p.m.")
            return datetime.datetime.strptime(t_str.replace(".",""), "%b %d, %Y, %I:%M %p")
        # sometimes minutes left off: e.g., Oct. 4, 2012, 9 p.m.
        else:
            return datetime.datetime.strptime(t_str.replace(".",""), "%b %d, %Y, %I %p")

    def format_time(self, t):
        """Return properly-formatted timestamp."""

        # new_t_str format should be e.g., 2012-01-01 00:00:00
        return t.strftime("%Y-%m-%d %H:%M:%S")

    def event(self, row, t, n, log):
        """Return an Event object."""

        return Event(row[0], row[1], row[2], t, row[4], n, log)

    def parse_yfd(self, carb_log, event_log, ex_log, hypo_log, bolus_log):
        """Extract and write to file data from a your.FlowingData tab-delim .csv file."""

        for row in self.reader:
            if row[3] != "action_time":
                t = self.get_timestamp(row[3])
                new_t_str = self.format_time(t)
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
                e = self.event(row, new_t_str, 0, event_log)
                e.create_event()
            elif row[0] == 'mild_hypo' or row[0] == 'severe_hypo':
                e = self.event(row, new_t_str, 15, hypo_log)
                e.create_event()
            elif row[0] == 'meal_bolus' or row[0] == 'correction_bolus':
                e = self.event(row, new_t_str, 240, bolus_log)
                e.create_event()
            elif row[0] == 'done_run':
                run_end = new_t_str
            elif row[0] == 'ran':
                r = Run(row[1], row[2], new_t_str, run_end)
                r.create_event()
                ex_log.add_event(r.event)

        carb_log.print_XML()
        event_log.print_XML()
        ex_log.print_XML()
        hypo_log.print_XML()
        bolus_log.print_XML()

class Event():

    def __init__(self, cat, count , desc, t, tag, duration, log):

        self.type = cat

        self.count = count

        self.content = desc

        self.time = t

        self.duration = duration

        self.hashtag = tag

        self.event = None

        self.log = log

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
        elif self.type == "mild_hypo":
            return "Mild hypoglycemia: %s mg/dL." %(self.count)
        elif self.type == "severe_hypo":
            return "Severe hypoglycemia: %s mg/dL." %(self.count)
        elif self.type == "meal_bolus":
            return "Meal bolus: %s units of insulin." %(self.count)
        elif self.type == "correction_bolus":
            return "Correction bolus: %s units of insulin. Tag(s): %s." %(self.count, self.hashtag)

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
        elif self.type == "mild_hypo" or self.type == "severe_hypo":
            return "Hypoglycemia"
        elif self.type == "meal_bolus" or self.type == "correction_bolus":
            return "Bolus"

    def create_event(self):
        """Package content of generic Event object as a Timeline-compliant XML event."""

        soup = BeautifulSoup("<event/>", "xml")

        self.event = soup.event

        if self.duration != 0:
            self.event['end'] = self.get_end()

        self.event['start'] = self.time

        self.event['title'] = self.get_type()

        self.event.string = self.get_event_string()

        self.log_event()

    def log_event(self):
        self.log.add_event(self.event)

    def get_end(self):
        """Return properly-formatted timestamp of end of event, given its duration and start time."""

        t = datetime.datetime.strptime(self.time, "%Y-%m-%d %H:%M:%S")
        stop_t = t + datetime.timedelta(0,0,0,0,self.duration)
        if stop_t.day != t.day:
            time = datetime.datetime(stop_t.year,stop_t.month,stop_t.day,0,0,0)
            delta = stop_t - time
            delta_min = delta.seconds/60
            t_str = time.strftime("%Y-%m-%d %H:%M:%S")
            e = Event(self.type, self.count, self.content, t_str, self.hashtag, delta_min, self.log)
            e.create_event()
            e.log_event()
            stop_t = datetime.datetime(t.year,t.month,t.day,23,59,59)
        return stop_t.strftime("%Y-%m-%d %H:%M:%S")

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

        soup = BeautifulSoup("<event/>", "xml")

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

        soup = BeautifulSoup("<event/>", "xml")

        self.event = soup.event

        self.event['start'] = self.start

        self.event['end'] = self.end

        self.event['title'] = "Carbs: %d" %int(float(self.grams))

        self.event.string = "%sAte:%s %s.%s%sConfidence level of carb count:%s %s" %(OI, CLI, self.content, BREAK, OI, CLI, self.get_confidence())

class Dexcom():

    def __init__(self, filename):

        self.file_base = "dex/dex"

        if filename.find('.xml') != -1:
            self.file = open(filename, 'rU')
            self.readings = self.get_readings()
            self.ext = '.xml'
        else:
            platinum = G4(filename)
            self.readings = platinum.readings
            self.ext = '.csv'

        #TODO: remove [4:], which is a temp hack to get rid of the 'raw/' at the beginning of the filename string
        self.stats_writer = csv.writer(open('to-R/' + filename[4:].replace(self.ext, '_stats.csv'), 'w'))

        self.day_writer = csv.writer(open('to-R/' + filename[4:].replace(self.ext,'_day.csv'), 'w'))

        self.bubble_writer = csv.writer(open('to-R/' + filename[4:].replace(self.ext, '_bubble.csv'), 'w'))

        self.day_heat_writer = csv.writer(open('to-R/' + filename[4:].replace(self.ext,'_day_heatmap.csv'), 'w'))

        self.time_heat_writer = csv.writer(open('to-R/' + filename[4:].replace(self.ext, '_time_heatmap.csv'), 'w'))

    def get_date(self, reading):
        """Return the date from a Dexcom XML object representing a single BG reading."""

        return datetime.datetime.strptime(reading['DisplayTime'][:10], "%Y-%m-%d")

    def get_time(self, reading):
        """Return the hour of the day as a 24-hr clock integer from a Dexcom XML object representing a single BG reading."""

        if reading['DisplayTime'][-4].find('.') != -1:
            # old Dexcom files have %H:%M:%S.xxx
            t = datetime.datetime.strptime(reading['DisplayTime'][:-4], "%Y-%m-%d %H:%M:%S")
        else:
            # new Dexcom files stop at seconds
            t = datetime.datetime.strptime(reading['DisplayTime'], "%Y-%m-%d %H:%M:%S")
        return t.hour

    def get_date_str(self, reading):
        """Return a string of the date from a Dexcom XML object representing a single BG reading."""

        return reading['DisplayTime'][:10]

    def get_readings(self):
        """Return array of XML objects each representing a blood glucose reading."""

        xsoup = BeautifulSoup(self.file, "xml")
        return xsoup.findAll('Sensor')

    def stats(self):
        """Write to a single .csv file various per-day statistics from Dexcom data."""

        last_day = self.get_date(self.readings[0])
        count = 0

        days = {}
        days[count] = ([],[],[],[],self.get_date_str(self.readings[0]))

        for reading in self.readings:
            if self.get_date(reading) == last_day:
                days[count][0].append(int(reading['Value']))
                if int(reading['Value']) <= 65:
                    days[count][1].append(int(reading['Value']))
                elif int(reading['Value']) > 65 and int(reading['Value']) <= 140:
                    days[count][2].append(int(reading['Value']))
                elif int(reading['Value']) > 140:
                    days[count][3].append(int(reading['Value']))
                else:
                    print "I can't classify this BG reading: %s!" %reading['Value']
            else:
                count += 1
                days[count] = ([int(reading['Value'])],[],[],[],self.get_date_str(reading))
                if int(reading['Value']) <= 65:
                    days[count][1].append(int(reading['Value']))
                elif int(reading['Value']) > 65 and int(reading['Value']) <= 140:
                    days[count][2].append(int(reading['Value']))
                elif int(reading['Value']) > 140:
                    days[count][3].append(int(reading['Value']))
                else:
                    print "I can't classify this BG reading: %s!" %reading['Value']
                last_day = self.get_date(reading)

        header = ['date', 'year', 'average', 'standard_deviation', 'percentage_low', 'percentage_target', 'percentage_high']

        self.stats_writer.writerow(header)

        for day in days.values():
            ave = int(round(numpy.average(day[0])))
            std = int(round(numpy.std(day[0])))
            low = float(len(day[1]))/float(len(day[0])) * 100
            target = float(len(day[2]))/float(len(day[0]))*100
            high = float(len(day[3]))/float(len(day[0]))*100
            self.stats_writer.writerow([day[4],day[4][:4],ave,std,low,target,high])

    def day_csv(self):
        """Export .csv that can be made into day boxplots directly in R."""

        header = ["timestamp","reading","weekday"]

        self.day_writer.writerow(header)

        for reading in self.readings:
            weekday = self.get_date(reading).weekday()
            bg = int(reading['Value'])
            time = reading['DisplayTime']
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
            bg = int(reading['Value'])
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
            bg = int(reading['Value'])
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
            bg = int(reading['Value'])
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
        days = [last_day]

        for reading in self.readings:
            # for old Dexcom .xml exports
            if reading['DisplayTime'].find('.') != -1:
                print_time = reading['DisplayTime'][:-4]
            # for new Dexcom .csv exports
            else:
                print_time = reading['DisplayTime']

            if self.get_date(reading) == last_day:
                print >> xml_out, print_time + "," + reading['Value']
            else:
                count += 1
                last_day += datetime.timedelta(days=1)
                new_reading_date = self.get_date(reading)
                if last_day == new_reading_date:
                    xml_out = open(self.file_base+str(count)+'.txt','w')
                    days.append(last_day)
                else:
                    while last_day != new_reading_date:
                        count += 1
                        xml_out = open(self.file_base+str(count)+'.txt','w')
                        days.append(last_day)
                        last_day += datetime.timedelta(days=1)
                
                print >> xml_out, reading['DisplayTime'][:-4] + "," + reading['Value']

        return days

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

def insert_num_days(n):
    """Insert the number of days of data into logbook.html where required."""

    soup = BeautifulSoup(open("logbook.html",'rU'))

    body = soup.body

    body['onload'] = "onLoad(%d);" %(n)

    out = open("logbook.html", 'w')

    print >> out, soup.prettify()
            
def main():
    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    parser.add_argument('-p', '--ping', action = 'store', dest = "ping_name", help='name of OneTouch Ping csv file')
    parser.add_argument('-y', '--yfd', action = 'store', dest = "yfd_name", help='name of your.FlowingData csv file')
    parser.add_argument('-n', '--days', action = 'store', type=int, dest = "days", default=0, help='number of days of data you would like processed, starting from the beginning of the file')

    args = parser.parse_args()

    p = Ping(args.ping_name)

    p.parse_ping()

    d = Dexcom(args.dex_name)

    if args.days != 0:
        tmp = d.logbook()
        days = tmp[:args.days]
    else:
        days = d.logbook()

    carb_log = Log("carb", days)

    event_log = Log("", days)

    ex_log = Log("ex", days)

    hypo_log = Log("hypo", days)

    bolus_log = Log("bolus", days)

    yfd = YFD(args.yfd_name)

    yfd.parse_yfd(carb_log, event_log, ex_log, hypo_log, bolus_log)

    insert_num_days(len(days))

    carb_log.endpoints()

if __name__=="__main__":
    main()
