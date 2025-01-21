
import requests
import json

def get_balances(address):
    """
    Args:
        address: SUI wallet address.

    Returns:
        A dictionary containing the balances of different coins for the given address.
    """
    try:
        url = f"https://fullnode.mainnet.sui.io:443" 
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "suix_getAllCoins",
            "params": [address]
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        if "result" in data:
            return data["result"]
        else:
            print(f"Error: Unexpected response format from RPC API.")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching balances: {e}")
        return {}

if __name__ == "__main__":
    wallet_address = "0x357a12335528ee125422430624e0251f18d3ee0f55d5911e56b3da1c3eeb06fc"
    balances = get_balances(wallet_address)
    # Write transactions to JSON file
    with open('sui.json', 'w') as json_file:
        json.dump(balances, json_file, indent=4)
