from sqlalchemy import select
from database.model.models import Wallets
from interface.output import show_menu
from solders.keypair import Keypair
import base58


async def select_donor(session) -> Wallets:
    """Выбираем кошелек-донора с балансом > 0."""
    result = await session.execute(select(Wallets).where(Wallets.Type == "SOL"))
    wallets = result.scalars().all()

    for w in wallets:
        choices = [
            {
                "name": f"{w.name} ({w.public_key})", 
                "value": w
            }
        ]

        donor = await show_menu(
            message="Select sender-wallet:",
            choices=choices,
        )

        return donor
