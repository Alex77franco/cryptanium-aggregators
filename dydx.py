import os
import requests
import csv
from datetime import datetime
from dotenv import load_dotenv
import time
import threading

load_dotenv()

DYDX_REST_API_URL = "https://dydx-rest.publicnode.com"
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/0x92D6C1e31e14520e676a687F0a93788B716BEff5"
REPORTS_FOLDER = "reports"
WALLET_ADDRESS = "dydx1qmz8gw2ddh50x0nl4crejwr4vd67498racmrkl"

DECIMALS = 10**18
loading = True


def show_loading(message):
    global loading
    dots = 0
    while loading:
        print(f"\r{message}{'.' * (dots % 4)}", end='', flush=True)
        dots += 1
        time.sleep(0.5)
    print(f"\r{message}...", end='', flush=True)


def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def fetch_account_balances(wallet_address):
    try:
        response = requests.get(f"{DYDX_REST_API_URL}/cosmos/bank/v1beta1/balances/{wallet_address}")
        response.raise_for_status()
        return response.json().get('balances', [])
    except requests.RequestException as e:
        print(f"Error fetching balances: {e}")
        return []


def fetch_account_rewards(wallet_address):
    try:
        response = requests.get(f"{DYDX_REST_API_URL}/cosmos/distribution/v1beta1/delegators/{wallet_address}/rewards")
        response.raise_for_status()
        return response.json().get('total', [])
    except requests.RequestException as e:
        print(f"Error fetching rewards: {e}")
        return []


def fetch_account_delegations(wallet_address):
    try:
        response = requests.get(f"{DYDX_REST_API_URL}/cosmos/staking/v1beta1/delegations/{wallet_address}")
        response.raise_for_status()
        delegations = response.json().get('delegation_responses', [])
        if delegations:
            return delegations[0].get('balance', {}).get('amount', "0")
        return "0"
    except requests.RequestException as e:
        print(f"Error fetching delegations: {e}")
        return "0"


def fetch_dydx_price():
    """Fetch the current price of DYDX in USD from Dexscreener."""
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        data = response.json()

        for pair in data.get('pairs', []):
            if pair['pairAddress'].lower() == '0xe0cfa17aa9b8f930fd936633c0252d5cb745c2c3'.lower():
                return safe_float(pair['priceUsd'])

        print("Error: No matching pair found for the given address.")
        return 0.0
    except requests.RequestException as e:
        print(f"Error fetching DYDX price: {e}")
        return 0.0


def convert_to_dydx(value):
    """Convert raw token amount to dYdX amount with 18 decimals."""
    return safe_float(value) / DECIMALS


def get_wallet_balance_data():
    """Extract and calculate wallet balance data."""
    balances = fetch_account_balances(WALLET_ADDRESS)
    rewards = fetch_account_rewards(WALLET_ADDRESS)
    delegated_balance = fetch_account_delegations(WALLET_ADDRESS)
    dydx_price = fetch_dydx_price()

    spendable_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'adydx'), "0")
    reward_balance_raw = next((item['amount'] for item in rewards if item['denom'] == 'adydx'), "0")

    spendable_balance = convert_to_dydx(spendable_balance_raw)
    delegated_balance = convert_to_dydx(delegated_balance)
    reward_balance = convert_to_dydx(reward_balance_raw)

    spendable_balance_value = spendable_balance * dydx_price
    delegated_balance_value = delegated_balance * dydx_price
    reward_balance_value = reward_balance * dydx_price


    return {
        "Wallet Address": WALLET_ADDRESS,
        "dydx Price (USD)": f"{dydx_price:.4f}",
        "Spendable (dydx)": f"{spendable_balance:.6f}",
        "Spendable Value (USD)": f"{spendable_balance_value:.4f}",
        "Delegated (dydx)": f"{delegated_balance:.6f}",
        "Delegated Value (USD)": f"{delegated_balance_value:.4f}",
        "Reward (dydx)": f"{reward_balance:.6f}",
        "Reward Value (USD)": f"{reward_balance_value:.4f}"
    }


def export_to_csv(data, filename):
    """Export the results to a CSV file."""
    try:
        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = [
                'Wallet Address', 'dydx Price (USD)', 'Spendable (dydx)', 'Spendable Value (USD)',
                'Delegated (dydx)', 'Delegated Value (USD)', 'Reward (dydx)', 'Reward Value (USD)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            writer.writerow(data)

        print(f"\nData successfully exported to {file_path}")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")


def main():
    """Main function to execute the script."""
    global loading

    print("Running...")
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    wallet_data = get_wallet_balance_data()

    loading = False
    loading_thread.join()

    if wallet_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DYDX_Wallet_{timestamp}.csv"
        export_to_csv(wallet_data, filename)

    print("Done!")


if __name__ == "__main__":
    main()
