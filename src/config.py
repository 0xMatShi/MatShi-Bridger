import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class RelayData():
    relay_api: str = os.getenv("RELAY_API")
    chain_eth: str = os.getenv("CHAIN_ETH")
    chain_base: str = os.getenv("CHAIN_BASE")
    chain_sol: str = os.getenv("CHAIN_SOL")
    token_eth: str = os.getenv("TOKEN_ETH")
    token_usdc_base: str = os.getenv("TOKEN_USDC_BASE")
    token_sol: str = os.getenv("TOKEN_SOL")

class RPC:
    sol_rpc: str = os.getenv("SOL_RPC")
    eth_rpc: str = os.getenv("ETH_RPC")
    base_rpc: str = os.getenv("BASE_RPC")

class DBConfig:
    user: str = os.getenv("DB_USER")
    password: str = os.getenv("DB_PASS")
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("DB_PORT")
    name: str = os.getenv("DB_NAME")
    db_url: str = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
