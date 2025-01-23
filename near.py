
import requests
import json
import asyncio
import httpx
from dotenv import dotenv_values

config = dotenv_values(".env")
api_key = config.get("API_KEY")

# Replace with your NEAR wallet address
wallet_address = 'cfdf371346821425ce9ddd42cd0645c44d8837d614fc884a712a8662e50cfa'

# NEAR blockchain API endpoint
api_url = f'https://near.blockpi.network/v1/rpc/{api_key}'

headers = {"Content-Type": "application/json"}
payload_transaction_details = {
  "jsonrpc": "2.0",
  "id": "dontcare",
  "method": "query",
  "params": {
    "request_type": "view_account",
    "finality": "final",
    "account_id": "cfdf371346821425cffe9ddd42cd0645c44d8837d614fc884a712a8662e50cfa"
  }
}

# Function to fetch and process transactions
async def fetch_transactions(url):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, json=payload_transaction_details, headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            return data
    
        
        else:
            print(f"Error fetching transactions: {response.status_code}")
            return []



async def main():
    # Fetch transactions
    transactions = await fetch_transactions(api_url)

    # Write transactions to JSON file
    filename = f"{wallet_address}.json"
    with open(filename, 'w') as json_file:
        json.dump(transactions, json_file, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
