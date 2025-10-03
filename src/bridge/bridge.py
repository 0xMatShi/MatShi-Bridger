import os
import aiohttp
from loguru import logger
from sqlalchemy import select
from database.model.engine import SessionFactory
from database.model.models import Wallets
from interface.output import show_menu
from src.bridge.preparing import bridge_eth_to_sol
from src.bridge.transaction import execute_steps
from database.utils.check_balance import get_balance
from src.config import RelayData

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

relaydata = RelayData()

async def start_bridge(origin_currency: str):
    if origin_currency == relaydata.token_usdc_base:
        origin = "USDC(Base)"
    else: 
        origin = "ETH(Base)"

    chains = ["ETH", "SOL"]
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
        

        if chain == "ETH":
            eth_wallet = wallet
            if origin_currency == relaydata.token_usdc_base:
                async with aiohttp.ClientSession() as http:
                    balance = await get_balance(http, eth_wallet.public_key, chain=chain, token=origin_currency)
                    print(f"Balance: {balance} {origin}")
                    
                raw_input = input("Enter the amount (e.g., 0.1 or 25%): ")

                if raw_input.endswith("%"):
                    percent = float(raw_input.rstrip("%"))
                    if not 0 < percent <= 100:
                        raise ValueError
                    amount = balance * (percent / 100)

                else:
                    amount = float(raw_input)
            elif origin_currency == relaydata.token_eth:
                async with aiohttp.ClientSession() as http:
                    balance = await get_balance(http, eth_wallet.public_key, chain=chain)
                    print(f"Balance: {balance} {origin}")

                raw_input = input("Enter the amount (e.g., 0.1 or 25%): ")

                if raw_input.endswith("%"):
                    percent = float(raw_input.rstrip("%"))
                    if not 0 < percent <= 100:
                        raise ValueError
                    amount = balance * (percent / 100)

                else:
                    amount = float(raw_input)
        if chain == "SOL":
            sol_wallet = wallet

    clear_console()
    steps, eth_wallet, w3_base = await bridge_eth_to_sol(eth_wallet, sol_wallet, amount, origin_currency)

    result = await execute_steps(steps, eth_wallet, w3_base)

    if result:
        logger.success(f"Successfully bridged {amount} {origin} to {sol_wallet.public_key}")
        input("\nPress Enter to Continue...")
        return
    else:
        logger.error("Error while bridging. Program has stopped")
        input("\nPress Enter to Continue...")
        return
