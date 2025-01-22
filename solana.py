# wallet_tracker.py

import asyncio
import httpx
import datetime
import pytz
import cachetools.func
import json

# Set up necessary variables and cache
url = "https://api.mainnet-beta.solana.com"
headers = {"Content-Type": "application/json"}
wallet = "5Z7UwKzHbYfoJos5MZmLPbDpgkCbAayteirQT3aU5hRU"
local_tz = pytz.timezone("Europe/Moscow")  # Change to your timezone
cache = cachetools.func.TTLCache(maxsize=1000, ttl=600)
last_transactions = []


def lamports_to_sol(lamports):
    return lamports / 1_000_000_000.0


async def get_transaction_details(signature):
    if signature in cache:
        return cache[signature]
    payload_transaction_details = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
        ],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, json=payload_transaction_details, headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            cache[signature] = data  # Store the data in cache
            return data


async def sanitize_transactions(new_tx_signatures):
    # Process from oldest to newest
    for signature in reversed(new_tx_signatures):
        message = ""
        transaction_details = await get_transaction_details(signature)
        if transaction_details and "result" in transaction_details:
            transaction_info = transaction_details["result"]
            block_time = (
                datetime.datetime.fromtimestamp(
                    transaction_info["blockTime"], datetime.UTC
                )
                .replace(tzinfo=pytz.utc)
                .astimezone(local_tz)
                .strftime("%Y-%m-%d %H:%M:%S %Z")
                if "blockTime" in transaction_info
                else "Unknown Time"
            )
            # message_time = datetime.datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
            message += f"Signature: `{signature}`\n"

            for txn_detail in (
                transaction_info.get("transaction", {})
                .get("message", {})
                .get("instructions", [])
            ):
                if "parsed" in txn_detail:
                    info = txn_detail["parsed"]["info"]
                    print(info)
                    with open("solana.json", "a") as f:
                        json.dump(info, f)
                    txn_type = txn_detail["parsed"]["type"]
                    if txn_type == "transferChecked":
                        token = info["destination"]
                        amount = info["tokenAmount"]["amount"]
                        decimals = info["tokenAmount"]["decimals"]
                        message += (
                            f"Transaction Time: `{block_time}`\n"
                            f"Token: `{token}`\n"
                            f"Amount: `{amount}`\n"
                            f"Decimals: `{decimals}`\n"
                            f"Type: `{txn_type}`\n"
                        )
                        print(message)


async def start_periodic_task(wallet_address):
    global last_transactions
    try:
        while True:
            payload_transactions = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [wallet_address],
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload_transactions, headers=headers
                )

            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    new_signatures = [tx["signature"] for tx in data["result"]]
                    if not last_transactions:
                        new_tx_signatures = [
                            sig
                            for sig in new_signatures
                            if sig not in last_transactions
                        ]
                        await sanitize_transactions(new_tx_signatures)
                        # First run, initialize last_transactions
                        last_transactions = new_signatures
                    else:
                        # Find new transactions
                        new_tx_signatures = [
                            sig
                            for sig in new_signatures
                            if sig not in last_transactions
                        ]
                        if new_tx_signatures:
                            await sanitize_transactions(new_tx_signatures)
                            last_transactions = new_signatures
            else:
                message = f"Error: '{response.status_code}'\n"
                print(message)
            await asyncio.sleep(5)  # Check for new transactions every 5 seconds
    except:
        print(f"Tracking task for wallet {wallet_address} was cancelled.")
        # Clean up if necessary
        raise


async def main():
    while True:
        await start_periodic_task(wallet)


if __name__ == "__main__":
    asyncio.run(main())
