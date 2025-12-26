from sqlalchemy.orm import Session

from domain.unit_of_work import UnitOfWork
from .repositories import SqlAlchemyOrderRepository, SqlAlchemyProductRepository

class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Session | None = None
        self.product_repo = None
        self.order_repo = None

    def __enter__(self):
        self.session = self._session_factory()
        self.product_repo = SqlAlchemyProductRepository(self.session)
        self.order_repo = SqlAlchemyOrderRepository(self.session)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type:
            self.rollback()
        else:
            self.commit()
        if self.session:
            self.session.close()

    def commit(self):
        if self.session:
            self.session.commit()

    def rollback(self):
        if self.session:
            self.session.rollback()
