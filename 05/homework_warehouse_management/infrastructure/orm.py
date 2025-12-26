from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ProductORM(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

class OrderORM(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)


order_product_associations = Table(
    "order_product_associations",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id")),
    Column("product_id", ForeignKey("products.id")),
)

OrderORM.products = relationship("ProductORM", secondary=order_product_associations)
