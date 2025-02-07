import os
import requests
import csv
import threading
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

TAO_PRICE_API_URL = "https://api.taostats.io/api/price/latest/v1?asset=tao"
ACCOUNT_BALANCE_API_URL = "https://api.taostats.io/api/account/latest/v1"
REPORTS_FOLDER = "reports"
API_KEY = os.getenv("TAO_API_KEY")

WALLETS = [
    "5EcYxFfwKLKogdKkGdz88ZFh2J6TqpygRGdRqHWADii9vzYb",
    "5Fqxv8Ba3GG6BHWMeUScGHt39ddJmafAnGkuxxCRXicSYVWY",
    "5DMxfUJfhSskQnSkzJnFJQns1Ej2FbZLAFjfs5mSTjccLkx8"
]

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

def fetch_tao_price():
    """Fetch the current price of TAO in USD."""
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    try:
        response = requests.get(TAO_PRICE_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])
        if data:
            return safe_float(data[0].get('price'))
        return 0.0
    except requests.RequestException as e:
        print(f"Error fetching TAO price: {e}")
        return 0.0

def fetch_account_data(wallet_address):
    """Fetch account balance data for a given wallet."""
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    try:
        response = requests.get(f"{ACCOUNT_BALANCE_API_URL}?address={wallet_address}", headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])
        if data:
            return data[0]
        return {}
    except requests.RequestException as e:
        print(f"Error fetching account data for {wallet_address}: {e}")
        return {}

def get_wallet_balances(wallets, tao_price):
    """Fetch and prepare balance data for multiple wallets."""
    results = []
    for wallet in wallets:
        account_data = fetch_account_data(wallet)
        if not account_data:
            continue

        available_balance = safe_float(account_data.get('balance_free')) / 1e9
        staked_balance = safe_float(account_data.get('balance_staked')) / 1e9
        total_balance = safe_float(account_data.get('balance_total')) / 1e9

        available_value = available_balance * tao_price
        staked_value = staked_balance * tao_price
        total_value = total_balance * tao_price

        results.append({
            "Wallet Address": wallet,
            "Available Balance (TAO)": f"{available_balance:.6f}",
            "Available Value (USD)": f"{available_value:.6f}",
            "Staked Balance (TAO)": f"{staked_balance:.6f}",
            "Staked Value (USD)": f"{staked_value:.6f}",
            "Total Balance (TAO)": f"{total_balance:.6f}",
            "Total Value (USD)": f"{total_value:.6f}"
        })

    return results

def export_to_csv(data, filename, tao_price):
    """Export the results to a CSV file."""
    try:
        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = [
                'Wallet Address', 'Available Balance (TAO)', 'Available Value (USD)',
                'Staked Balance (TAO)', 'Staked Value (USD)', 'Total Balance (TAO)', 'Total Value (USD)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            total_available_value = 0.0
            total_staked_value = 0.0
            total_value_sum = 0.0


            for row in data:
                total_available_value += float(row['Available Value (USD)'])
                total_staked_value += float(row['Staked Value (USD)'])
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            writer.writerow({})
            writer.writerow({
                "Wallet Address": "Total",
                "Available Balance (TAO)": "",
                "Available Value (USD)": f"{total_available_value:.6f}",
                "Staked Balance (TAO)": "",
                "Staked Value (USD)": f"{total_staked_value:.6f}",
                "Total Balance (TAO)": "",
                "Total Value (USD)": f"{total_value_sum:.6f}"
            })
            writer.writerow({})
            writer.writerow({
                "Wallet Address": "Price of TAO(USD)",
                "Available Balance (TAO)": f"{tao_price:.6f}",
            })

        print(f"\nData successfully exported to {file_path}")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")

def main():
    global loading

    print("Running...")
    
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    tao_price = fetch_tao_price()

    token_data = get_wallet_balances(WALLETS, tao_price)

    loading = False
    loading_thread.join()

    if token_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TAO_Wallets_{timestamp}.csv"
        export_to_csv(token_data, filename, tao_price)

    print("Done!")

if __name__ == "__main__":
    main()
