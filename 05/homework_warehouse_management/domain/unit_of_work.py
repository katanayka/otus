from abc import ABC, abstractmethod
from .repositories import OrderRepository, ProductRepository

class UnitOfWork(ABC):
    product_repo: ProductRepository
    order_repo: OrderRepository

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exception_type, exception_value, traceback):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
