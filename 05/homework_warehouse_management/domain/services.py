from typing import List
from .models import Product, Order
from .repositories import ProductRepository, OrderRepository

class WarehouseService:
    def __init__(self, product_repo: ProductRepository, order_repo: OrderRepository):
        self.product_repo = product_repo
        self.order_repo = order_repo

    def create_product(self, name: str, quantity: int, price: float) -> Product:
        product = Product(id=None, name=name, quantity=quantity, price=price)
        return self.product_repo.add(product)

    def create_order(self, products: List[Product]) -> Order:
        if not products:
            raise ValueError("order must contain products")
        order = Order(id=None, products=products)
        return self.order_repo.add(order)
