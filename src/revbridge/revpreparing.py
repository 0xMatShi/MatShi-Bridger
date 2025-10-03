import aiohttp
import json
from loguru import logger
from web3 import Web3
from src.config import RelayData, RPC


relaydata = RelayData()
rpc = RPC()


async def bridge_sol_to_usdc(sol_wallet, eth_wallet, amount_sol: float, dest_currency: str):
    user = sol_wallet.public_key        # Solana-адрес отправителя
    recipient = eth_wallet.public_key     # EVM-адрес получателя на Base

    if dest_currency == relaydata.token_eth:
        dest = "ETH(Base)"
    else:
        dest = "USDC(Base)"

    async with aiohttp.ClientSession() as session:
        # === Quote: SOL(Solana) -> USDC(Base) ===
        logger.info(f"Calculation of SOL(Solana) -> {dest}.")
        payload = {
            "user": user,
            "originChainId": relaydata.chain_sol,
            "destinationChainId": relaydata.chain_base,
            "originCurrency": relaydata.token_sol, 
            "destinationCurrency": dest_currency,
            "amount": str(int(amount_sol * 10**9)),
            "tradeType": "EXACT_INPUT",
            "recipient": recipient
        }

        quote = await get_quote(session, payload)
        if not quote:
            logger.error(f"Unable to get Quote (SOL→{dest}).")
            return

        # Извлекаем полезные данные
        amount_in, amount_in_fmt, amount_out, amount_out_fmt, symbol_out = extract_amounts(quote)
        if not amount_out:
            logger.error(f"Failed to extract {dest} from quote.")
            return

        logger.info(f"From {amount_sol} SOL You will get {amount_out_fmt} {dest}.")

        confirm = input("Confirm bridge? (y/n): ")
        if confirm.lower() != "y":
            logger.info("Bridge cancelled.")
            input("\nPress Enter to Continue...")
            return

        steps = quote.get("steps", [])
        for step in steps:
            for item in step.get("items", []):
                step_data = item.get("data", {})
                logger.success("Bridge is ready. Returning step_data for execution..")
                return step_data


async def get_quote(session, payload: dict):
    logger.info(f"Запрос к Relay")
    async with session.post(f"{relaydata.relay_api}/quote", json=payload) as resp:
        quote = await resp.json()
    if "error" in quote or "message" in quote:
        logger.error(f"Ошибка при получении QUOTE: {quote}")
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
        logger.error(f"Не удалось распарсить quote: {e}")
        return None, None, None, None, None