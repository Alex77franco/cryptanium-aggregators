import os
import requests
import csv
import threading
from datetime import datetime
import time

BALANCE_API_URL = "https://lcd.injective.network/cosmos/bank/v1beta1/balances/"
METADATA_API_URL = "https://sentry.exchange.grpc-web.injective.network/api/exchange/meta/v1/tokenMetadata"
DEX_SCREENER_API_URL = "https://api.dexscreener.com/tokens/v1/injective/"
WALLET_ADDRESS = "inj1ukryjeq858umfds09jfmkd9csmjpuns7n3540f"
REPORTS_FOLDER = "reports"

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

def fetch_token_metadata(token_denom):
    """Fetch metadata for a given token using the Injective metadata API."""
    try:
        response = requests.get(f"{METADATA_API_URL}?denoms={token_denom}")
        response.raise_for_status()
        data = response.json()

        if 'tokens' in data and data['tokens']:
            token_data = data['tokens'][0]
            return {
                "name": token_data.get('name', 'Unknown'),
                "symbol": token_data.get('symbol', 'UNKNOWN'),
                "decimals": token_data.get('decimals', 6)
            }
    except requests.RequestException as e:
        print(f"Error fetching metadata for {token_denom}: {e}")

    return {"name": "Unknown", "symbol": "UNKNOWN", "decimals": 6}

def fetch_token_price(token_denom):
    """Fetch the USD price of a token using Dexscreener."""
    try:
        formatted_denom = token_denom.replace("/", "-")
        print(f"Formatted denom: {formatted_denom}")

        response = requests.get(f"{DEX_SCREENER_API_URL}{formatted_denom}")
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            return float(data[0].get('priceUsd', 0.0))
        else:
            print(f"No price data found for {formatted_denom}")
    except requests.RequestException as e:
        print(f"Error fetching price for {token_denom}: {e}")

    return 0.0

def get_account_balances(wallet_address):
    """Fetch account balances and complete token information for a given Injective wallet."""
    try:
        response = requests.get(BALANCE_API_URL + wallet_address)
        response.raise_for_status()
        data = response.json()

        balances = data.get('balances', [])
        if not balances:
            print("No tokens found for this account.")
            return []

        results = []
        for token in balances:
            denom = token.get('denom', 'Unknown')
            raw_amount = float(token.get('amount', 0))

            metadata = fetch_token_metadata(denom)
            price_usd = fetch_token_price(denom)
            decimals = metadata['decimals']
            name = metadata['name']
            symbol = metadata['symbol']

            adjusted_balance = raw_amount / (10 ** decimals)
            total_value = adjusted_balance * price_usd

            results.append({
                "Token Name": name,
                "Symbol": symbol,
                "Address": denom,
                "Balance": f"{adjusted_balance:.10f}",
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
            fieldnames = ['Token Name', 'Symbol', 'Address', 'Balance', 'Price (USD)', 'Total Value (USD)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)


            writer.writeheader()
            total_value_sum = 0.0

            for row in data:
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            writer.writerow({})
            writer.writerow({
                "Token Name": "TOTAL",
                "Symbol": "",
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

    token_data = get_account_balances(WALLET_ADDRESS)

    loading = False
    loading_thread.join()

    if token_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{WALLET_ADDRESS}_Injective_{timestamp}.csv"
        export_to_csv(token_data, filename)

    print("Done!")

if __name__ == "__main__":
    main()
