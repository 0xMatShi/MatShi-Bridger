from sqlalchemy import select
from database.model.models import Wallets
from interface.output import show_menu


async def select_recipient(session) -> Wallets:
    """Выбираем кошелек-донора с балансом > 0."""
    result = await session.execute(select(Wallets).where(Wallets.Type == "SOL"))
    wallets = result.scalars().all()

    for w in wallets:
        choices = [
            {
                "name": f"{w.name} ({w.public_key})", 
                "value": w.public_key
            }
        ]

        recipient = await show_menu(
            message="Select recipient-wallet:",
            choices=choices,
        )

        return recipient