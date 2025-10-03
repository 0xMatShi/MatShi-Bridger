import aiohttp
import os
import base58
from loguru import logger
from sqlalchemy import select
from database.model.engine import SessionFactory
from database.model.models import Wallets
from interface.output import show_menu
from database.utils.check_balance import get_balance
from src.revbridge.revpreparing import bridge_sol_to_usdc
from src.revbridge.revtransantion import execute_sol_bridge_step
from solders.keypair import Keypair

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


async def start_rev_bridge(destinationCurrency: str):
    chains = ["SOL", "ETH"]
    for chain in chains:
        async with SessionFactory() as session:
            result = await session.execute(select(Wallets).where(Wallets.Type == chain))
            wallets = result.scalars().all()
        
        if not wallets:
            logger.warning(f"There are no {chain}-Wallets in DataBase.")
            input("\nPress Enter to continue...")
            return
        
        choices = [
            {
            "name": f"{w.name} {w.public_key}", 
            "value": w
            } for w in wallets
        ]
        wallet = await show_menu(
            message=f"Select {chain}-wallet: ", 
            choices=choices
        )
        

        if chain == "SOL":
            sol_wallet = wallet
            async with aiohttp.ClientSession() as http:
                balance_sol = await get_balance(http, sol_wallet.public_key, chain=chain)
                print(f"Balance: {balance_sol} SOL")
            raw_amount = input("Enter the amount (e.g., 0.1 or 99%): ").strip()
            if raw_amount.endswith("%"):
                percent = float(raw_amount[:-1])
                amount_sol = balance_sol * (percent / 100)
            else:
                amount_sol = float(raw_amount)
        if chain == "ETH":
            eth_wallet = wallet

    clear_console()
    step_data = await bridge_sol_to_usdc(sol_wallet, eth_wallet, amount_sol, destinationCurrency)

    sol_kp = Keypair.from_bytes(base58.b58decode(sol_wallet.private_key))

    result = await execute_sol_bridge_step(sol_kp, step_data)

    if result:
        logger.success(f"Successfully bridged {amount_sol} to {eth_wallet.public_key}")
        input("\nPress Enter to Continue...")
        return
    else:
        logger.error("Error while bridging. Program has stopped")
        input("\nPress Enter to Continue...")
        return