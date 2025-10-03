import aiohttp
import json
from loguru import logger
from web3 import Web3
from src.config import RelayData, RPC


relaydata = RelayData()
rpc = RPC()


async def bridge_eth_to_sol(eth_wallet, sol_wallet, amount: float, origin_currency: str):

    if origin_currency == relaydata.token_eth:
        origin = "ETH(Base)"
        amount = int(amount * 10**9)
    else: 
        origin = "USDC(Base)"
        amount = int(amount * 10**6)


    w3_base = Web3(Web3.HTTPProvider(rpc.base_rpc))

    user = eth_wallet.public_key            # EVM адрес отправителя (ETH L1 / Base)
    recipient = sol_wallet.public_key       # Solana адрес получателя

    async with aiohttp.ClientSession() as session:
        logger.info(f"Calculation of {origin} to obtain SOL")
        payload = {
            "user": user,
            "originChainId": relaydata.chain_base,
            "destinationChainId": relaydata.chain_sol,
            "originCurrency": origin_currency,  # ETH/USDC на Base
            "destinationCurrency": relaydata.token_sol,  # SOL на Solana
            "amount": str(amount),  
            "tradeType": "EXACT_INPUT",
            "recipient": recipient
        }
        quote = await get_quote(session, payload)
        if not quote:
            logger.error(f"Unable to get Quote {origin} -> SOL.")
            return

        confirm = input("Confirm bridge? (y/n): ")
        if confirm.lower() != "y":
            logger.info("Bridge cancelled.")
            input("\nPress Enter to Continue...")
            return

        steps = quote.get("steps", [])

        logger.success("Bridge подготовлен. Возвращаем steps_data для исполнения.")

        return steps, eth_wallet, w3_base


async def get_quote(session, payload: dict):
    logger.info(f"Запрос к Relay")
    async with session.post(f"{relaydata.relay_api}/quote", json=payload) as resp:
        quote = await resp.json()
    if "error" in quote or "message" in quote:
        logger.error(f"Error while getting QUOTE: {quote}")
        return None
    return quote


def extract_amounts(q: dict):
    try:
        details = q.get("quote", q).get("details", {})
        amount_in = details.get("currencyIn", {}).get("amount")                # строка-число в минимальных единицах
        amount_in_fmt = details.get("currencyIn", {}).get("amountFormatted")   # читабельная строка
        amount_out = details.get("currencyOut", {}).get("amount")
        amount_out_fmt = details.get("currencyOut", {}).get("amountFormatted")
        symbol_out = details.get("currencyOut", {}).get("currency", {}).get("symbol")
        return amount_in, amount_in_fmt, amount_out, amount_out_fmt, symbol_out
    except Exception as e:
        logger.error(f"Unable to unparse quote: {e}")
        return None, None, None, None, None