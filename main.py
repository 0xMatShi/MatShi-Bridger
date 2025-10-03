from loguru import logger
from InquirerPy import inquirer
import os
import sys
import urllib3
import logging
import asyncio
from database.utils.create_table import create_db
from process import start


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


async def main():
    # Loading Logs configuration
    configuration()
    clear_console()

    create = input("Are you want to create tables in DataBase? (y/n): ")
    if not create:
        pass
    else: 
        await create_db()
        logger.info("DataBase was succsessfully created!")
        pass
    
    await start()


log_format = (
    "<light-blue>[</light-blue><yellow>{time:HH:mm:ss}</yellow><light-blue>]</light-blue> | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}:{line}</cyan> | "
    "<level>{message}</level>"
)

def configuration():
    urllib3.disable_warnings()
    logger.remove()

    # Disable primp and web3 logging
    logging.getLogger("primp").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)

    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format,
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 month",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
        level="INFO",
    )


if __name__ == "__main__":
    asyncio.run(main())