import os
import requests
import csv
import threading
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

PIKESPEAK_API_URL = "https://api.pikespeak.ai/account/wealth/"
ACCOUNT_ID = "cfdf371346821425cffe9ddd42cd0645c44d8837d614fc884a712a8662e50cfa"
REPORTS_FOLDER = "reports"
API_KEY = os.getenv("PIKESPEAK_API_KEY")

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

def get_account_balances(account_id):
    """Fetch all token balances for a given NEAR account using the Pikespeak API."""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{PIKESPEAK_API_URL}{account_id}", headers=headers)
        response.raise_for_status()
        data = response.json()

        balances = data.get('balance', [])
        if not balances:
            print("No tokens found for this account.")
            return []

        results = []
        for token in balances:
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('contract', 'Unknown')
            balance = safe_float(token.get('amount', 0))
            price_usd = safe_float(token.get('tokenPrice'))
            total_value = safe_float(token.get('usdValue'))

            results.append({
                "Symbol": symbol,
                "Address": address,
                "Balance": f"{balance:.6f}",
                "Price (USD)": f"{price_usd:.6f}",
                "Total Value (USD)": f"{total_value:.6f}"
            })

        return results
    except requests.RequestException as e:
        print(f"Error fetching balances: {e}")
        return []

def export_to_csv(data, filename):
    """Export the results to a CSV file."""
    try:
        data = sorted(data, key=lambda x: float(x['Total Value (USD)']), reverse=True)

        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = ['Symbol', 'Address', 'Balance', 'Price (USD)', 'Total Value (USD)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            total_value_sum = 0.0

            for row in data:
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            writer.writerow({})
            writer.writerow({
                "Symbol": "TOTAL",
                "Address": "",
                "Balance": "",
                "Price (USD)": "",
                "Total Value (USD)": f"{total_value_sum:.6f}"
            })

        print(f"\nData successfully exported to {file_path}")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")

def main():
    global loading

    print("Running...")
    
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    token_data = get_account_balances(ACCOUNT_ID)

    loading = False
    loading_thread.join()

    if token_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ACCOUNT_ID}_NEAR_{timestamp}.csv"
        export_to_csv(token_data, filename)

    print("Done!")

if __name__ == "__main__":
    main()