import os
import aiohttp
from loguru import logger
from sqlalchemy import select
from database.model.engine import SessionFactory
from database.model.models import Wallets
from interface.output import show_menu
from src.config import RPC


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

rpc = RPC()

async def balance_checker():
    while True:
        clear_console()  # убираем баннер при входе
        choice = await show_menu(
            message="\nSelect chain: ", 
            choices=[
                "SOL",
                "ETH",
                "Exit"
            ]
        )

        if choice == "SOL":
            clear_console()
            await check_wallets(choice)
        elif choice == "ETH":
            clear_console()
            await check_wallets(choice)
        else:
            return


async def check_wallets(chain: str):
    async with SessionFactory() as session:
        result = await session.execute(select(Wallets).where(Wallets.Type == chain.upper()))
        wallets = result.scalars().all()

    if not wallets:
        logger.warning(f"There are no {chain.upper()}-Wallets in the database.")
        input("\nPress Enter to continue...")
        return
    
    choices = [f"{w.Type.upper()} | {w.name} ({w.public_key})" for w in wallets]
    choice = await show_menu(
        message=f"\nSelect {chain.upper()} wallet: ",
        choices=choices
    )
    
    wallet = wallets[choices.index(choice)]

    async with aiohttp.ClientSession() as http:
        balance = await get_balance(http, wallet.public_key, chain=chain)

    logger.info(f"Balance '{wallet.name}' ({wallet.public_key}): {balance:.6f} {chain.upper()}")
    input("\nPress Enter to continue...")


async def get_balance(session: aiohttp.ClientSession, address: str, chain: str, token: str = None) -> float:
    if chain == "SOL":
        url = rpc.sol_rpc
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address],
        }
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
        lamports = data.get("result", {}).get("value", 0)
        return lamports / 1_000_000_000  # SOL

    elif chain == "ETH":
        if not token:
            url = rpc.base_rpc
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBalance",
                "params": [address, "latest"],
            }
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
            wei = int(data.get("result", "0x0"), 16)
            return wei / 10**18  # ETH

        # Если токен указан (например, USDC на Base)
        else:
            url = rpc.base_rpc
            # balanceOf(address) -> 0x70a08231 + 64 hex chars адреса
            method_sig = "0x70a08231"
            addr_hex = address.lower().replace("0x", "").zfill(64)
            data_field = method_sig + addr_hex

            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [
                    {
                        "to": token,   # адрес контракта USDC (relaydata.token_usdc_base)
                        "data": data_field
                    },
                    "latest"
                ],
            }
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
            raw = int(data.get("result", "0x0"), 16)
            return raw / 10**6  # USDC имеет 6 знаков после запятой


    else:
        raise ValueError(f"Unsupported chain: {chain}")
