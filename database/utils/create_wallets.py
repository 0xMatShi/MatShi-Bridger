from loguru import logger
from database.model.engine import SessionFactory
from database.model.models import Wallets
from solders.keypair import Keypair
from eth_account import Account
from interface.output import show_menu


async def create_wallet():
    wallet_type = await show_menu(
        message="\nSelect type of wallet: ", 
        choices=[
            "SOL",
            "ETH",
            "Exit"
        ]
    )
    
    if wallet_type == "SOL":
        kp = Keypair()
        public_key = str(kp.pubkey())
        private_key = str(kp)

    elif wallet_type == "ETH":
        acct = Account.create()
        public_key = str(acct.address)
        private_key = str(acct.key.hex())

    else:
        return

    name = input("Enter a name for wallet: ")
    if not name:
        logger.warning("Creation canceled")
        return

    async with SessionFactory() as session:
        async with session.begin():
            wallet = Wallets(
                Type=wallet_type,
                name=name,
                public_key=public_key,
                private_key=private_key,
            )
            session.add(wallet)
        await session.commit()

    logger.info(f"Created {wallet_type.upper()} wallet {name}")
    logger.info(f"Public: {public_key}")

    return