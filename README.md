# Cryptanium aggregators

## Tokens

| CHAIN NAME     | RPC ENDPOINT  | RPC METHOD | PRICE FEED API URL   |
| :------------- | :------------------------------------------ | :-------------------------------------- | :----------------------------------------------------------------- |
| Solana  | https://api.mainnet-beta.solana.com | getBalance | https://api.dexscreener.com/tokens/v1/solana/                 |
| SUI | https://sui-rpc.publicnode.com | suix_getAllBalances | https://api.dexscreener.com/tokens/v1/sui/
| INJ  | https://injective-rest.publicnode.com | /cosmos/bank/v1beta1/balances/ | https://api.dexscreener.com/latest/dex/tokens/inj  |
| Atom  | https://docs-demo.cosmos-mainnet.quiknode.pro | /cosmos/staking/v1beta1/delegations/ | https://api.dexscreener.com/tokens/v1/bsc/0x0Eb3a705fc54725037CC9e008bDede697f62F335  |
| Near  | https://rpc.mainnet.near.org | - | https://api.pikespeak.ai/account/wealth/  |
| TAO  | https://api.taostats.io/api/account/latest/v1 | - | https://api.taostats.io/api/price/latest/v1?asset=tao  |
| Mina  | https://api.minaexplorer.com | /accounts/ | https://api.coingecko.com/api/v3/simple/price?ids=mina-protocol&vs_currencies=usd  |
| DYDX  | https://dydx-rest.publicnode.com | /cosmos/bank/v1beta1/balances/ | https://api.dexscreener.com/latest/dex/tokens/0x92D6C1e31e14520e676a687F0a93788B716BEff5 |
| NIBI  | https://nibiru-rest.publicnode.com | /cosmos/bank/v1beta1/balances/ | https://api.coingecko.com/api/v3/simple/price?ids=nibiru&vs_currencies=usd  |

## Introduction

For each network there is an aggregator designed to fetch, process, and export data related to the tokens  held in a specific wallet.

## Fetching Wallet Tokens and Metadata

By sending a POST request to the RPC endpoint to fetch all tokens held by the specified wallet, and metadata (e.g., name, symbol, decimals) for a specific token.

## Fetching Token Price

By sending a GET request to the DexScreener API to fetch the USD price of a token.

## Exporting Data to CSV:

- Sorts the token data by total value in descending order.
- Creates a CSV file in the `reports` directory.
- Writes the token data (name, symbol, address, balance, price, and total value) to the CSV file.
- Adds a "TOTAL" row at the end, summing up the total value of all tokens.


## Setup

```bash
python3 -m venv path/to/env
```

```bash
pip3 install -r requirements.txt
```

## Run

Run the desired aggreagtor, solana here:

```bash
bin/python3 solana.py
```

