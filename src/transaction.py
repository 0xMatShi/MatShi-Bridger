import base58
import aiohttp
from src.config import RPC
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig
from solders.commitment_config import CommitmentLevel
from solders.hash import Hash
from loguru import logger


rpc = RPC()


async def _make_recent_blockhash(hash_str: str) -> Hash:
    """
    Попытки безопасно конвертировать блокхэш-строку (base58) в solders.hash.Hash,
    поддерживая несколько возможных API классов Hash.
    """
    raw = base58.b58decode(hash_str)
    # Попробуем разные фабрики, если они есть в версии solders
    if hasattr(Hash, "from_string"):
        try:
            return Hash.from_string(hash_str)
        except Exception:
            pass
    if hasattr(Hash, "from_bytes"):
        try:
            return Hash.from_bytes(raw)
        except Exception:   
            pass
    # fallback — конструктор, если принимает bytes
    try:
        return Hash(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to create Hash from blockhash: {e}")


async def send_sol(sender: Keypair, recipient: str, lamports: int) -> bool:
    """
    Отправляет amount_sol SOL с Keypair sender на адрес recipient (строка).
    Возвращает True при успехе, False при ошибке.
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
            # 2) Инструкция system transfer
            ix = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=Pubkey.from_string(recipient),
                    lamports=lamports
                )
            )

            # 3) Сформировать MessageV0
            msg = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=[ix],
                recent_blockhash=recent_blockhash,
                address_lookup_table_accounts=[]
            )

            # 4) Подписать VersionedTransaction
            tx = VersionedTransaction(msg, [sender])

            # 5) Отправить в RPC
            config = RpcSendTransactionConfig(preflight_commitment=CommitmentLevel.Confirmed)
        
            async with session.post(
                rpc.sol_rpc,
                headers={"Content-Type": "application/json"},
                data=SendVersionedTransaction(tx, config).to_json()
            ) as rpc_resp:
                rpc_json = await rpc_resp.json()

            if "result" in rpc_json and rpc_json["result"]:
                logger.info(f"SEND SOL tx: https://solscan.io/tx/{rpc_json['result']}")
                return True
            else:
                err = rpc_json.get("error", rpc_json)
                logger.error(f"Sending error: {err}")
                return False

        except Exception as e:
            logger.error(f"Error sending: {e}")
            return False