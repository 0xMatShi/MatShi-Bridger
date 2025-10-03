from database.model.engine import BaseSQLAlchemyModel
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Wallets(BaseSQLAlchemyModel):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Type: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key: Mapped[str] = mapped_column(String(255), nullable=False)
    private_key: Mapped[str] = mapped_column(String(255), nullable=False)


class DevWallet(BaseSQLAlchemyModel):
    __tablename__ = "dev_wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key: Mapped[str] = mapped_column(String(255), nullable=False)
    private_key: Mapped[str] = mapped_column(String(255), nullable=False)


class BuyerGroup(BaseSQLAlchemyModel):
    __tablename__ = "buyer_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    wallets: Mapped[list["BuyerWallet"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class BuyerWallet(BaseSQLAlchemyModel):
    __tablename__ = "buyer_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("buyer_groups.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    public_key: Mapped[str] = mapped_column(String, nullable=False)
    private_key: Mapped[str] = mapped_column(String, nullable=False)

    group: Mapped["BuyerGroup"] = relationship(back_populates="wallets")
