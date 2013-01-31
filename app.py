import cherrypy
# might not want to use a universal import like this
from churn_data import *

class App():
    @cherrypy.expose
    def index(self):
        return open('assets/html/index.html')

    def upload(self, dex, ping, yfd):

        d = Dexcom(dex.filename)

        if dex.filename.find(".xml") != -1:
            d = Dexcom(open(dex.file))
            d.readings = d.get_readings()
            d.ext = '.xml'
        else:
            platinum = G4(csv.reader(dex.file, delimiter='\t', quoting = csv.QUOTE_NONE))
            d.readings = platinum.readings
            d.ext = '.csv'

        p = Ping(csv.reader(ping.file))
        p.parse_ping()

        days = d.logbook()

        carb_log = Log("carb", days)

        event_log = Log("", days)

        ex_log = Log("ex", days)

        hypo_log = Log("hypo", days)

        bolus_log = Log("bolus", days)

        y = YFD(csv.reader(yfd.file, delimiter='\t'))
        y.parse_yfd(carb_log, event_log, ex_log, hypo_log, bolus_log)

        return open('assets/html/logbook.html')
    upload.exposed = True

if __name__ == '__main__':

    cherrypy.quickstart(App(), '/', 'app.conf')