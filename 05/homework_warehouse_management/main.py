from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.services import WarehouseService
from infrastructure.orm import Base
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SESSION_FACTORY = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def main():
    uow = SqlAlchemyUnitOfWork(SESSION_FACTORY)
    with uow:
        warehouse_service = WarehouseService(uow.product_repo, uow.order_repo)
        new_product = warehouse_service.create_product(name="test1", quantity=1, price=100)
        print(f"create product: {new_product}")

if __name__ == "__main__":
    main()
