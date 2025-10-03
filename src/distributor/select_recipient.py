from sqlalchemy import select
from database.model.models import DevWallet, BuyerGroup, BuyerWallet
from interface.output import show_menu
from loguru import logger

async def select_recipient(session) -> str:
    """Выбор конкретного получателя (dev или buyer)."""
    mode = await show_menu(
        message="Select wallet type :",
        choices=[
            {"name": "DevWallet", "value": "dev"}, 
            {"name": "BuyerWallet", "value": "buyer"}
            ],
    )


    if mode == "dev":
        result = await session.execute(select(DevWallet))
        wallets = result.scalars().all()
        if not wallets:
            logger.warning("There are no Dev-Wallets in the database.")
            input("\nPress Enter to continue...")
            return
        
        choices = [
            {"name": f"{w.name} ({w.public_key})", "value": w.public_key}
            for w in wallets
        ]

        recipient = await show_menu(
            message="Select Dev-wallet:",
            choices=choices,
        )
        return recipient
    
    elif mode == "buyer":
        result = await session.execute(select(BuyerGroup))
        groups = result.scalars().all()
        if not groups:
            logger.warning("There are no Buyer-Wallets Groups in the database.")
            input("\nPress Enter to continue...")
            return
        
        group_choices = [f"{g.name} (ID: {g.id})" for g in groups]
        selected_group = await show_menu(
            message="Select group:",
            choices=group_choices,
        )
        group = groups[group_choices.index(selected_group)]

        result = await session.execute(
            select(BuyerWallet).where(BuyerWallet.group_id == group.id)
            )
        wallets = result.scalars().all()

        if not wallets:
            logger.warning(f"The group '{group.name}' have no wallets.")
            input("\nPress Enter to continue...")
            return

        wallet_choices = [
            {
                "name": f"{w.number}. ({w.public_key})", 
                "value": w.public_key
            } 
            for w in wallets
        ]

        recipient = await show_menu(
            message=f"Select wallet from group '{group.name}':",
            choices=wallet_choices,
        )

        return recipient
    
    else:
        raise ValueError("Unknown mode")