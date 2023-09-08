import argparse
from dotenv import load_dotenv
import os

from cointegration.cointegration import cointegrate
from trading.backtest_trading import BackTrader
from trading.live_trading import LiveTrader

DEFAULT_POSISTION = 50000.00

def main():
    parser = argparse.ArgumentParser()
    program_arg = parser.add_mutually_exclusive_group(required=True)

    # Program type
    program_arg.add_argument(
        "--live",
        help="Run the live trading algorithm",
        action="store_true"
    )
    program_arg.add_argument(
        "--backtest",
        help="Run the backtesting algorithm",
        action="store_true"
    )

    # Config for training data -- used for initalizing algorithm
    parser.add_argument(
        "--traindata",
        help="Path to the training data",
        type=str
    )

    # Config for backtesting
    parser.add_argument(
        "--testdata",
        help="Path to the backtesting data",
        type=str
    )
    parser.add_argument(
        "--initial_amount",
        help="Initial cash position for backtesting",
        type=float
    )

    # Config for live trading
    program_arg.add_argument(
        "--credentials",
        help="Path to Alpaca credentials",
        type=str
    )

    args = parser.parse_args()

    if args.live and not args.credentials:
        parser.error("You must provide Alpaca credentials for live trading")

    if args.traindata:
        data_path = args.traindata
    else:
        print("Training data path not provided; using sample directory")
        data_path = "fc-statarb/cointegration/sample_data"

    files = os.listdir(data_path)
    csv_files = [file for file in files if file.endswith('.csv')]
    state_dict = cointegrate(csv_files)

    if not state_dict['passes_adf']:
        print("The spread is not stationary; use at your own risk")

    if args.live:
        try:
            load_dotenv(args.credentials)

            creds = [
                os.getenv('APCA-API-KEY-ID'),
                os.getenv('APCA-API-SECRET-KEY')
            ]
        
        except FileNotFoundError:
            raise Exception('Credentials does not exist at filepath')

        else:
            LiveTrader(creds, state_dict).run()

    elif args.backtest:
        if args.testdata:
            train_path = args.testdata
        else:
            print("No testing data path provided; using sample data -- may result in biased results")
            train_path = data_path

        initial_amount = args.initial_amount if args.initial_amount else DEFAULT_POSISTION
        BackTrader(state_dict).run(train_path, initial_amount)

    else:
        raise ValueError("Unknown arguments")
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
