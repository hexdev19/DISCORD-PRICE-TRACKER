from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductExtractionSchema(BaseModel):
	title: str = Field(description="Full product name")
	price: float = Field(description="Current selling price, no currency symbol")
	currency: str = Field(description="3-letter ISO currency code")
	in_stock: bool = Field(description="Whether product is purchasable now")
	image_url: str | None = Field(description="Main product image URL")
	store_name: str = Field(description="Name of the e-commerce store")


@dataclass(frozen=True)
class ScrapedProduct:
	title: str
	price: Decimal
	currency: str
	in_stock: bool
	image_url: str | None
	store_name: str
	source_url: str

	@classmethod
	def from_extraction(cls, data: ProductExtractionSchema, source_url: str) -> "ScrapedProduct":
		title = data.title.strip()
		if title == "":
			raise ValueError("title must not be empty")

		if data.price <= 0:
			raise ValueError("price must be greater than zero")

		return cls(
			title=title,
			price=Decimal(str(data.price)),
			currency=data.currency.strip().upper(),
			in_stock=data.in_stock,
			image_url=data.image_url,
			store_name=data.store_name.strip(),
			source_url=source_url,
		)
