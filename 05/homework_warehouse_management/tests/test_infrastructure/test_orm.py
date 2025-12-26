from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.models import Order, Product
from infrastructure.orm import Base
from infrastructure.repositories import SqlAlchemyOrderRepository, SqlAlchemyProductRepository


def test_repositories_work_with_sqlalchemy():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    product_repo = SqlAlchemyProductRepository(session)
    order_repo = SqlAlchemyOrderRepository(session)

    product = Product(id=None, name="milk", quantity=3, price=2.5)
    product_repo.add(product)
    session.commit()

    stored = product_repo.get(product.id)
    assert stored.name == "milk"

    order = Order(id=None, products=[product])
    order_repo.add(order)
    session.commit()

    stored_order = order_repo.get(order.id)
    assert stored_order.products[0].id == product.id
