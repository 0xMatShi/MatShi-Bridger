import os
from loguru import logger
from interface.output import show_logo, show_menu
from database.utils.create_wallets import create_wallet
from database.utils.check_balance import balance_checker
from database.utils.edit_wallets import wallets_editor
from src.bridge.bridge import start_bridge
from src.revbridge.revbridge import start_rev_bridge
from src.distributor.distributor import distribute_sol
from src.collector.collector import collect_sol
from src.config import RelayData

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

relaydata = RelayData()

async def start():
    while True:
        show_logo()
        choice = await show_menu(
            message="Main Menu:\n", 
            choices=[
                "Start Bridge via relay.link",
                "Transfer SOL",
                "Create Wallets",
                "Edit Wallets",
                "Check Balance",
                "Exit"
            ]
        )

        if choice == "Start Bridge via relay.link":
            clear_console()
            bridge_direction = await show_menu(
                message="Which direction do you want?",
                choices=[
                    "USDC(Base) -> SOL",
                    "ETH(Base) -> SOL",
                    "SOL -> USDC(Base)",
                    "SOL -> ETH(Base)"
                ]
            )
            if bridge_direction == "USDC(Base) -> SOL":
                clear_console()
                await start_bridge(relaydata.token_usdc_base)
            elif bridge_direction == "ETH(Base) -> SOL":
                clear_console()
                await start_bridge(relaydata.token_eth)
            elif bridge_direction == "SOL -> USDC(Base)":
                clear_console()
                await start_rev_bridge(relaydata.token_usdc_base)
            else:
                await start_rev_bridge(relaydata.token_eth)
        elif choice == "Transfer SOL":
            clear_console()
            direction = await show_menu(
                message="Which direction do you want?",
                choices=[
                    "Bridger -> Deployer",
                    "Deployer -> Bridger"
                ]
            )
            if direction == "Bridger -> Deployer":
                clear_console()
                await distribute_sol()
            else: 
                clear_console()
                await collect_sol()
        elif choice == "Create Wallets":
            clear_console()
            await create_wallet()
        elif choice == "Edit Wallets":
            clear_console()
            await wallets_editor()
        elif choice == "Check Balance":
            clear_console()
            await balance_checker()
        else:
            logger.info("Exiting the program...")
            return