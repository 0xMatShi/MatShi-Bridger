import os
from loguru import logger
from database.model.engine import SessionFactory
from sqlalchemy import select, delete, update
from interface.output import show_menu
from database.model.models import Wallets


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


async def wallets_editor():
    while True:
        clear_console()
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
            await edit_wallet(choice)
        elif choice == "ETH":
            clear_console()
            await edit_wallet(choice)
        else:
            return
        

async def edit_wallet(chain: str):
    async with SessionFactory() as session:
        wallet = await select_wallet(session, chain)
        if not wallet:
            return

        while True:
            clear_console()
            print(f"\n{chain.upper()}-Wallet '{wallet.name}':\n")
            print(f"Public Key: {wallet.public_key}")
            print(f"Private Key: {wallet.private_key}")

            choice = await show_menu(
                message="\nSelect action: ",
                choices=[
                    "Edit Name",
                    "Delete This Wallet",
                    "Exit"
                ]
            )

            if choice == "Edit Name":
                new_name = input("Enter a new name: ").strip()
                if new_name:
                    await session.execute(
                        update(Wallets).where(Wallets.id == wallet.id).values(name=new_name)
                    )
                    await session.commit()
                    wallet.name = new_name
                    logger.info("Name has been changed")
                    input("\nPress Enter to continue...")

            elif choice == "Delete This Wallet":
                confirm = input("Delete this wallet? (y/n): ").strip().lower()
                if confirm == "y":
                    await session.execute(delete(Wallets).where(Wallets.id == wallet.id))
                    await session.commit()
                    logger.warning("Wallet has been deleted")
                    input("\nPress Enter to Continue...")
                    return

            else:
                return
            

async def select_wallet(session, chain: str):
    async with SessionFactory() as session:
        result = await session.execute(select(Wallets).where(Wallets.Type == chain.upper()))
        wallets = result.scalars().all()

    if not wallets:
        logger.warning(f"There are no {chain.upper()}-Wallets in the database.")
        input("\nPress Enter ot continue...")
        return None

    choices = [f"{w.Type.upper()} | {w.name} ({w.public_key})" for w in wallets]
    choice = await show_menu(
        message=f"\nSelect {chain.upper()} wallet: ", 
        choices=choices
    )
    return wallets[choices.index(choice)]