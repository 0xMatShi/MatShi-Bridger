# transaction.py
from loguru import logger
from web3 import Web3
from eth_account import Account


async def execute_steps(steps, eth_account, w3_base: Web3):

    evm_signer = Account.from_key(eth_account.private_key)
    for i, step in enumerate(steps, 1):
        for j, item in enumerate(step.get("items", []), 1):
            data = item.get("data")

            if not data:
                logger.warning(f"[Item {j}] No data for transaction, skipping.")
                continue
            
            result = await execute_evm_tx(data, evm_signer, w3_base)
            if result:
                return True
            else:
                return False

async def execute_evm_tx(data, account: Account, w3: Web3):
    try:
        to_raw = data.get("to")
        to_addr = Web3.to_checksum_address(to_raw) if to_raw else None  
        # Получаем nonce с адреса LocalAccount
        value = int(data.get("value", 0))  # всегда int в wei [web:86]
        gas_limit = int(data.get("gas", 300000))  # gas — только int [web:87]
        nonce = w3.eth.get_transaction_count(account.address)   # [web:23][web:39]

        # EIP-1559 поля; при желании можно подставлять стратегию/оценку
        base_gas_price = int(w3.eth.gas_price)  # int обязателен [web:23]
        max_fee = int(data.get("maxFeePerGas", base_gas_price))  # допускаем переопределение [web:23]
        max_priority = int(data.get("maxPriorityFeePerGas", max_fee // 2))  # переопределяемо [web:23]
        chain_id = int(w3.eth.chain_id) 

        tx = {
            "from": account.address,                 # помогает диагностике, не обязателен для raw send [web:23]
            "to": to_addr,
            "data": data.get("data", "0x") or "0x",
            "value": value,
            "nonce": nonce,
            "gas": gas_limit,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority,
            "chainId": chain_id,
        }

        logger.info(f"Signing the transaction: {tx}")
        signed = account.sign_transaction(tx)  # подписывает локально [web:21][web:23]
        # В web3.py атрибут — raw_transaction (snake_case)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)  # [web:23]
        logger.info(f"Tx sent: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)  # [web:23]
        logger.success(f"Tx confirmed: https://basescan.org/tx/0x{receipt.transactionHash.hex()}")

        return True

    except Exception as e:
        logger.error(f"[EVM] Ошибка при исполнении транзакции: {e}")
        return False