import os
import requests
import csv
import time
from datetime import datetime
import threading

# Constants
RPC_ENDPOINT = "https://sui-rpc.publicnode.com"
DEX_SCREENER_API_URL = "https://api.dexscreener.com/tokens/v1/sui/"
WALLET_ADDRESS = "0x357a12335528ee125422430624e0251f18d3ee0f55d5911e56b3da1c3eeb06fc"
REPORTS_FOLDER = "reports"

# Loading animation
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

def get_sui_tokens(wallet_address: str):
    """Fetch all tokens held by a Sui wallet."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getAllBalances",
        "params": [wallet_address]
    }

    try:
        response = requests.post(RPC_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json().get('result', [])
    except requests.RequestException as e:
        print(f"Request error in get_sui_tokens: {e}")
        return []

def get_token_metadata(coin_type: str):
    """Fetch metadata for a given token."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getCoinMetadata",
        "params": [coin_type]
    }

    try:
        response = requests.post(RPC_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json().get('result', {})
    except requests.RequestException as e:
        print(f"Request error in get_token_metadata: {e}")
        return {}

def get_token_price(coin_type: str):
    """Fetch the USD price of a token from Dexscreener."""
    try:
        response = requests.get(DEX_SCREENER_API_URL + coin_type)
        response.raise_for_status()

        data = response.json()
        if data and isinstance(data, list):
            return float(data[0].get('priceUsd', 0.0))
    except requests.RequestException as e:
        print(f"Request error in get_token_price: {e}")

    return 0.0

def export_to_csv(data: list, filename: str):
    """Export the results to a CSV file."""
    try:
        # Sort data by the total value column
        data = sorted(data, key=lambda x: float(x['Total Value (USD)']), reverse=True)

        # Ensure the reports directory exists
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

            # Add a total row
            writer.writerow({})
            writer.writerow({})
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

    # Get all tokens for the wallet
    tokens = get_sui_tokens(WALLET_ADDRESS)

    # Prepare data for CSV
    results = []
    for token in tokens:
        coin_type = token.get('coinType')
        raw_balance = int(token.get('totalBalance', 0))


        # Fetch metadata and price
        metadata = get_token_metadata(coin_type)
        decimals = metadata.get('decimals', 9)
        symbol = metadata.get('symbol', 'UNKNOWN')
        name = metadata.get('name', 'Unknown Token')

        price_usd = get_token_price(coin_type)

        # Adjust balance and calculate total value
        balance = raw_balance / (10 ** decimals)
        total_value = balance * price_usd

        # Add to results
        results.append({
            "Token Name": name,
            "Symbol": symbol,
            "Address": coin_type,
            "Balance": f"{balance:.6f}",
            "Price (USD)": f"{price_usd:.6f}",
            "Total Value (USD)": f"{total_value:.6f}"
        })

    # Stop loading animation and persist message
    loading = False
    loading_thread.join()

    # CSV creation message
    print("\nCreating CSV file...")

    # Export data to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{WALLET_ADDRESS}_Sui_{timestamp}.csv"
    export_to_csv(results, filename)

    print("Done!")

if __name__ == "__main__":
    main()
