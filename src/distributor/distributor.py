import base58
import aiohttp
import os
from loguru import logger
from database.model.engine import SessionFactory
from src.config import RPC
from src.distributor.select_donor import select_donor
from src.distributor.select_recipient import select_recipient
from src.transaction import send_sol
from solders.keypair import Keypair


rpc = RPC()

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


async def get_balance(session, pubkey: str) -> float:
    """Асинхронный запрос баланса через Solana RPC"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [pubkey]
    }

    try:
        async with session.post(rpc.sol_rpc, json=payload) as resp:
            data = await resp.json()
            lamports = data.get("result", {}).get("value", 0)
            return lamports / 1_000_000_000
    except Exception as e:
        return f"Ошибка: {e}"


async def distribute_sol():
    """Основная функция распределения SOL."""
    async with SessionFactory() as session:
        donor = await select_donor(session)
        donor_kp = Keypair.from_bytes(base58.b58decode(donor.private_key))
        async with aiohttp.ClientSession() as http:
            donor_balance = await get_balance(http, donor.public_key)

        recipient_address = await select_recipient(session)
        async with aiohttp.ClientSession() as http:
            recipient_balance = await get_balance(http, recipient_address)

        raw_amount = input("Enter the amount (e.g., 0.1 or 99%): ").strip()
        if raw_amount.endswith("%"):
            percent = float(raw_amount[:-1])
            amount = donor_balance * (percent / 100)
        else:
            amount = float(raw_amount)

        lamports = int(amount * 1e9)

        clear_console()
        logger.info(f"Sender-wallet balance: {donor_balance:.4f} SOL")
        logger.info(f"Recitient-wallet balance: {recipient_balance:.4f} SOL")
        logger.info(f"{amount:.4f} SOL will be transferred to {recipient_address}")

        confirm = input("Confirm transfer? (y/n): ")
        if confirm.lower() != "y":
            logger.info("Distribution cancelled.")
            input("\nPress Enter to Continue...")
            return
        
        clear_console()
        result = await send_sol(donor_kp, recipient_address, lamports)

        if result:
            logger.success(f"{recipient_address} successfully received {amount}")
            input("\nPress Enter to continue...")

        else:
            logger.error("Prorgram was stopped while error")
            input("\nPress Enter to continue...")





