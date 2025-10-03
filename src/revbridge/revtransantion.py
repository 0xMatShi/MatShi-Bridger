import base58
import aiohttp
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.hash import Hash
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig
from solders.commitment_config import CommitmentLevel
from loguru import logger
from src.config import RPC
from src.transaction import _make_recent_blockhash


rpc = RPC()


async def execute_sol_bridge_step(sol_wallet: Keypair, step_data: dict):
    """
    Исполняет шаг deposit (инструкции Solana).
    step_data = item["data"] из quote.
    """
    async with aiohttp.ClientSession() as session:
        try:
            # 1) Получаем latest blockhash
            async with session.post(
                rpc.sol_rpc, 
                json={
                    "jsonrpc":"2.0",
                    "id":1,
                    "method":"getLatestBlockhash"
                }
            ) as resp:
                j = await resp.json()
                blockhash_str = j["result"]["value"]["blockhash"]

        except Exception as e:
            logger.error(f"Unable to obtain the latest blockhash: {e}")
            return False 
        
        try:
            recent_blockhash = await _make_recent_blockhash(blockhash_str)
        except Exception as e:
            logger.error(f"Conversion error blockhash -> Hash: {e}")
            return False

        try:
            # Получаем инструкции
            instructions = [parse_instruction(ix) for ix in step_data["instructions"]]
        
            # Формируем MessageV0
            msg = MessageV0.try_compile(
                payer=sol_wallet.pubkey(),
                instructions=instructions,
                recent_blockhash=recent_blockhash,
                address_lookup_table_accounts=[]
            )

            # Подписываем
            tx = VersionedTransaction(msg, [sol_wallet])

            # Отправляем
            config = RpcSendTransactionConfig(preflight_commitment=CommitmentLevel.Confirmed)
            async with session.post(
                rpc.sol_rpc,
                headers={"Content-Type": "application/json"},
                data=SendVersionedTransaction(tx, config).to_json()
            ) as rpc_resp:
                rpc_json = await rpc_resp.json()

            if "result" in rpc_json and rpc_json["result"]:
                sig = rpc_json["result"]
                logger.success(f"Bridge tx send: https://solscan.io/tx/{sig}")
                return True
            else:
                logger.error(f"Error while sending: {rpc_json}")
                return False

        except Exception as e:
            logger.error(f"Error during bridge-trans execution: {e}")
            return False


def parse_instruction(ix_json: dict) -> Instruction:
    """Парсинг одной инструкции из step-данных Relay."""
    program_id = Pubkey.from_string(ix_json["programId"])
    keys = [
        AccountMeta(
            pubkey=Pubkey.from_string(k["pubkey"]),
            is_signer=k["isSigner"],
            is_writable=k["isWritable"],
        )
        for k in ix_json.get("keys", [])
    ]

    # data у Relay всегда hex-строка
    data = bytes.fromhex(ix_json["data"]) if ix_json.get("data") else b""
    return Instruction(program_id, data, keys)


def flatten_instructions(instructions_raw):
    """Разворачивает вложенные списки инструкций в плоский список dict."""
    flat = []
    for ix in instructions_raw:
        if isinstance(ix, dict):
            flat.append(ix)
        elif isinstance(ix, list):
            flat.extend(flatten_instructions(ix))  # рекурсивно разворачиваем
        else:
            raise TypeError(f"Неизвестный тип инструкции: {type(ix)} → {ix}")
    return flat