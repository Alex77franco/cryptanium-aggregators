import os
import requests
import csv
from datetime import datetime
from dotenv import load_dotenv
import time
import threading

load_dotenv()

MINA_ACCOUNT_API_URL = "https://api.minaexplorer.com/accounts/"
REPORTS_FOLDER = "reports"
API_KEY = os.getenv("MINA_API_KEY")
WALLET_ADDRESS = "B62qjTJPtZ8sPeLyaCQMHebSYj2GPwGvhnTeR2gr8jUEYSsGFxADXEH"

loading = True

def show_loading(message):
    """Show a loading animation in the terminal."""
    global loading
    dots = 0
    while loading:
        print(f"\r{message}{'.' * (dots % 4)}", end='', flush=True)
        dots += 1
        time.sleep(0.5)
    print(f"\r{message}...", end='', flush=True)


def safe_float(value, default=0.0):
    """Convert a value to float safely, with a default fallback."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def fetch_account_data(wallet_address):
    """Fetch account balance data for the given wallet."""
    headers = {
        "accept": "application/json",
        "x-api-key": API_KEY
    }

    try:
        response = requests.get(f"{MINA_ACCOUNT_API_URL}{wallet_address}", headers=headers)
        response.raise_for_status()
        return response.json().get('account', {})
    except requests.RequestException as e:
        print(f"Error fetching account data for {wallet_address}: {e}")
        return {}


def fetch_mina_price():
    """Fetch the current price of MINA in USD."""
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=mina-protocol&vs_currencies=usd'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return safe_float(data['mina-protocol']['usd'])
    except requests.RequestException as e:
        print(f"Error fetching MINA price: {e}")
        return 0.0


def get_wallet_balance(account_data, mina_price):
    """Extract and calculate balances from account data."""
    total_balance = safe_float(account_data.get('balance', {}).get('total'))
    current_staked_balance = safe_float(account_data.get('epochStakingAccount', [{}])[0].get('balance', 0))
    next_staked_balance = safe_float(account_data.get('nextEpochStakingAccount', [{}])[0].get('balance', 0))

    return {
        "Wallet Address": account_data.get('publicKey'),
        "MINA Price (USD)": f"{mina_price:.4f}",
        "Total Balance (MINA)": f"{total_balance:.6f}",
        "Total Value (USD)": f"{total_balance * mina_price:.4f}",
        "Current Staked (MINA)": f"{current_staked_balance:.6f}",
        "Next Epoch Staking Allocation (MINA)": f"{next_staked_balance:.6f}"
    }


def export_to_csv(data, filename):
    """Export the results to a CSV file."""
    try:
        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = [
                'Wallet Address', 'MINA Price (USD)', 'Total Balance (MINA)', 'Total Value (USD)',
                'Current Staked (MINA)', 'Next Epoch Staking Allocation (MINA)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            writer.writerow(data)

        print(f"\nData successfully exported to {file_path}")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")


def main():
    global loading

    print("Running...")
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    mina_price = fetch_mina_price()
    account_data = fetch_account_data(WALLET_ADDRESS)

    loading = False
    loading_thread.join()

    if account_data:
        balance_data = get_wallet_balance(account_data, mina_price)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"MINA_Wallet_{timestamp}.csv"
        export_to_csv(balance_data, filename)

    print("Done!")


if __name__ == "__main__":
    main()
