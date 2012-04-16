from churn_data import Dexcom
import argparse

def main():

    parser = argparse.ArgumentParser(description='Process the input files.')
    parser.add_argument('-d', '--dexcom', action = 'store', dest = "dex_name", help='name of Dexcom xml file')
    args = parser.parse_args()

    d = Dexcom(args.dex_name)

    d.stats()

if __name__ == "__main__":
    main()
