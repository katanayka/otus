from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Product:
    id: Optional[int]
    name: str
    quantity: int
    price: float

    def __post_init__(self):
        if not self.name:
            raise ValueError("name is required")
        if self.quantity < 0:
            raise ValueError("quantity must be non-negative")
        if self.price < 0:
            raise ValueError("price must be non-negative")

@dataclass
class Order:
    id: Optional[int]
    products: List[Product] = field(default_factory=list)

    def add_product(self, product: Product):
        self.products.append(product)

    def total_price(self) -> float:
        return sum(product.price for product in self.products)
