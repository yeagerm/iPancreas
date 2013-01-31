import argparse
import csv

from churn_data import Dexcom
from dexcom_g4_importer import G4Reader as G4

def main():

    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    args = parser.parse_args()

    d = Dexcom(args.dex_name)

    if args.dex_name.find('.xml') != -1:
        d.file = open(args.dex_name, 'rU')
        d.readings = d.get_readings()
        d.ext = '.xml'
    else:
        platinum = G4(csv.reader(open(args.dex_name, 'rb'), delimiter='\t', quoting = csv.QUOTE_NONE))
        d.readings = platinum.readings
        d.ext = '.csv'

    d._make_stats_files()

    d.stats()
    d.day_csv()
    d.bubble_chart()
    d.time_heatmap()
    d.day_heatmap()

if __name__ == "__main__":
    main()
