import pytest

from domain.models import Product
from domain.repositories import OrderRepository, ProductRepository
from domain.services import WarehouseService


class InMemoryProductRepository(ProductRepository):
    def __init__(self):
        self._items = []
        self._next_id = 1

    def add(self, product: Product) -> Product:
        product.id = self._next_id
        self._next_id += 1
        self._items.append(product)
        return product

    def get(self, product_id: int) -> Product:
        return next(item for item in self._items if item.id == product_id)

    def list(self):
        return list(self._items)


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._items = []
        self._next_id = 1

    def add(self, order):
        order.id = self._next_id
        self._next_id += 1
        self._items.append(order)
        return order

    def get(self, order_id: int):
        return next(item for item in self._items if item.id == order_id)

    def list(self):
        return list(self._items)


def test_create_product_assigns_id():
    service = WarehouseService(InMemoryProductRepository(), InMemoryOrderRepository())
    product = service.create_product(name="apple", quantity=10, price=5.0)
    assert product.id == 1


def test_create_order_requires_products():
    service = WarehouseService(InMemoryProductRepository(), InMemoryOrderRepository())
    with pytest.raises(ValueError):
        service.create_order([])


def test_create_order_persists_products():
    product_repo = InMemoryProductRepository()
    order_repo = InMemoryOrderRepository()
    service = WarehouseService(product_repo, order_repo)
    product = service.create_product(name="banana", quantity=2, price=3.0)
    order = service.create_order([product])
    assert order.id == 1
    assert order.products[0].id == product.id


def test_product_validation():
    with pytest.raises(ValueError):
        Product(id=None, name="", quantity=1, price=1.0)
