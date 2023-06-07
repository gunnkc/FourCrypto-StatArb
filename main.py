import sys

from backtest_trading import BackTrader
from live_trading import LiveTrader

DEFAULT_POSISTION = 50000.00

if len(sys.argv) > 1:
    args = sys.argv[1:]
    print(args)
    
    if args[0] == '--live':
        try:
            dirpath = args[1]
        except IndexError:
            raise Exception('Unable to locate Alpaca credentials')
        
        try:
            creds = []
            with open(dirpath, 'r') as file:
                for count, line in enumerate(file):
                    if (count > 1):
                        break # Break if there's more than just API and Secret Key

                    creds.append(line) 
        
        except FileNotFoundError:
            raise Exception('Credentials does not exist at filepath')
        
        LiveTrader.run(creds)

    elif args[0] == '--backtest':
        try:
            dirpath = args[1]
        except IndexError:
            raise Exception('Unable to locate backtesting data')

        try:
            intial = float(args[2])
        except:
            intial = DEFAULT_POSISTION
            print(f'Intial cash position unavilable - using {DEFAULT_POSISTION}')
        
        BackTrader.run(dirpath, intial)