import time
import json
import datetime
import sys
from web3 import Web3


# Smart Contract Configuration
# 0x97ce7eD95567ee1D760610FA69303ea18f87a2E4
ETH_PRIVATE_KEY = open('private.key', 'rt').read()
ETH_CHAIN_ID = 1
ETH_GAS_LIMIT = 150000  # Gas limit for transaction

ABI = json.loads(open('abi_wildbtc.json', 'rt').read())


CHAIN_DETAILS = {
    "eth": {
        'chain_id': 1,
        "chain_id_hex": hex(1),
        'abi': ABI,
        'abi_small': ABI,
        'chain_name': "ETH",
        "contract_address": Web3.to_checksum_address("0xa7c8ddf41ac11a82dc959bb7999c6831e08d7c15"),
        "rpc_url": "https://ethereum-rpc.publicnode.com",
        "max_token_id": 10,
        'currency': 'ETH',
        "mint_price": 1_0000000000, #0.00000001
    },
}

CHAIN_IDS = {CHAIN_DETAILS[x]['chain_id']: x for x in CHAIN_DETAILS}
for x in CHAIN_DETAILS:
    CHAIN_DETAILS[x]['web3'] = Web3(Web3.HTTPProvider(CHAIN_DETAILS[x]['rpc_url']))
    CHAIN_DETAILS[x]['contract'] = CHAIN_DETAILS[x]['web3'].eth.contract(
        address=CHAIN_DETAILS[x]['contract_address'], abi=CHAIN_DETAILS[x]['abi'])

CHAINS = [
    {"name": "eth", "label": "ETH"},
]



def get_balance(address, chain='eth'):
    try:
        w3 = CHAIN_DETAILS[chain]['web3']
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return balance_eth
    except:
        return "error getting balance"


def get_min_gas_fee_last_hour(gas_fee, gas_fees={}):
    min_ = 8_000_000_000
    now = int(time.time())
    gas_fees[now] = gas_fee
    to_delete = []
    for r in gas_fees:
        if r < now - 1800:
            to_delete += [r]
        elif gas_fees[r] < min_:
            min_ = gas_fees[r]

    for r in to_delete:
        del gas_fees[r]

    return min_    


def call_smart_contract_mint(chain='eth'):
    """Call the mint smart contract function"""
    w3 = CHAIN_DETAILS[chain]['web3']
    contract = CHAIN_DETAILS[chain]['contract']
    account = w3.eth.account.from_key(ETH_PRIVATE_KEY)
    gas_fee = get_gas_price("eth")
    print(f"{gas_fee=}")
    min_gas_fee_last_hour = get_min_gas_fee_last_hour(gas_fee)
    print(f"{min_gas_fee_last_hour=}")

    if min_gas_fee_last_hour > 100_000_000:
        print("sleeping 5 minutes")
        time.sleep(5 * 60)
        return "gas fee too big", "gas fees"

    gas_fee = 40_000_000

    if min_gas_fee_last_hour > 10_000_000:
        gas_fee = 20_000_000
    if min_gas_fee_last_hour > 15_000_000:
        gas_fee = 25_000_000
    if min_gas_fee_last_hour > 20_000_000:
        gas_fee = 30_000_000
    if min_gas_fee_last_hour > 25_000_000:
        gas_fee = 32_000_000
    if min_gas_fee_last_hour > 30_000_000:
        gas_fee = 35_000_000
    if min_gas_fee_last_hour > 35_000_000:
        gas_fee = 38_000_000
    if min_gas_fee_last_hour > 40_000_000:
        gas_fee = 40_000_000
    # if min_gas_fee_last_hour > 45_000_000:
    #    gas_fee = 50_000_000
    # if min_gas_fee_last_hour > 50_000_000:
    #     gas_fee = 55_000_000
    # if min_gas_fee_last_hour > 55_000_000:
    #    gas_fee = 60_000_000

    print(f"{gas_fee=} after it was updated")

    
    # Build transaction
    transaction = contract.functions.mint().build_transaction({
        'chainId': CHAIN_DETAILS[chain]['chain_id'],
        'gas': ETH_GAS_LIMIT,
        'maxFeePerGas': gas_fee,  # For EIP-1559
        'maxPriorityFeePerGas': 100000,
        'nonce': w3.eth.get_transaction_count(account.address),
        'type': 2  # EIP-1559 transaction
    })
    
    signed_txn = account.sign_transaction(transaction)

    print(f"{signed_txn=}")
    print(f"{transaction=}")

    try:
        txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    except Exception as e:
        print(repr(e))
        return "error send", "already known"
    try:
        receipt = w3.eth.wait_for_transaction_receipt(txn_hash, timeout=120)
    except Exception as e:
        print(repr(e))
        return txn_hash.hex(), "timeout error probably"
    
    return txn_hash.hex(), receipt.status


def get_gas_price(chain='eth'):
    """
    Get current gas price in wei.
    """
    w3 = CHAIN_DETAILS[chain]['web3']
    try:
        fee_data = w3.eth.fee_history(1, 'latest', reward_percentiles=[25, 75])
        fee = min(fee_data['baseFeePerGas'])
        return fee
    except Exception as e:
        print(repr(e))
        return None


def send_transaction_to_mint():
    account_address = '0x97ce7eD95567ee1D760610FA69303ea18f87a2E4'
    chain = "eth"

    balance = get_balance(account_address)
    print(f"{balance=}")
    if 'error getting balance' == balance:
        time.sleep(60)
        return None
    if balance < 0.000005:
        print(f"balance too low: {balance=}")
        sys.stdout.flush()
        time.sleep(60*60)
        return None
    w3 = CHAIN_DETAILS[chain]['web3']
    contract = CHAIN_DETAILS[chain]['contract']
    nr_transactions = w3.eth.get_transaction_count(account_address)
    print(f"{nr_transactions=}")

    time_until_next_mint = contract.functions.timeUntilNextMint().call()
    print(f"{time_until_next_mint=}")
    if time_until_next_mint:
        print(f"sleeping {time_until_next_mint=} seconds")
        sys.stdout.flush()
        time.sleep(time_until_next_mint + 5)

    a, b = call_smart_contract_mint()
    print(a, b)



if __name__ == '__main__':
    while True:
        print()
        print(datetime.datetime.now())
        try:
            send_transaction_to_mint()
        except Exception as e:
            print(repr(e))
            time.sleep(60*3)
        time.sleep(60)
    





