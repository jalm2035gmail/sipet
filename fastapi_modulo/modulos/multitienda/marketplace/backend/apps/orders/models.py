
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product, ProductVariant
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    guest_email = Column(String(255), nullable=True)
    billing_address = Column(JSON)
    shipping_address = Column(JSON, nullable=True)
    status = Column(String(20), default='pending', index=True)
    payment_status = Column(String(20), default='pending')
    subtotal = Column(Numeric(12,2))
    tax_amount = Column(Numeric(12,2), default=0)
    shipping_total = Column(Numeric(12,2), default=0)
    discount_amount = Column(Numeric(12,2), default=0)
    total = Column(Numeric(12,2))
    payment_method = Column(String(50))
    payment_transaction_id = Column(String(100), default='')
    shipping_method = Column(String(50), default='')
    customer_note = Column(String, default='')
    private_note = Column(String, default='')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    customer = relationship('User')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    shipping_groups = relationship('ShippingGroup', back_populates='order', cascade='all, delete-orphan')
    payments = relationship('Payment', back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    variant_id = Column(Integer, ForeignKey('product_variants.id'), nullable=True)
    product_name = Column(String(200))
    product_sku = Column(String(50), default='')
    price = Column(Numeric(10,2))
    compare_price = Column(Numeric(10,2), nullable=True)
    quantity = Column(Integer)
    total = Column(Numeric(10,2))
    item_status = Column(String(20), default='pending')
    platform_commission = Column(Numeric(10,2), default=0)
    vendor_amount = Column(Numeric(10,2), default=0)

    order = relationship('Order', back_populates='items')
    vendor = relationship('VendorStore')
    product = relationship('Product')
    variant = relationship('ProductVariant')

class ShippingGroup(Base):
    __tablename__ = 'shipping_groups'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    shipping_method = Column(String(50))
    shipping_cost = Column(Numeric(10,2), default=0)
    tracking_number = Column(String(100), default='')
    tracking_url = Column(String(255), default='')
    status = Column(String(20), default='pending')

    order = relationship('Order', back_populates='shipping_groups')
    vendor = relationship('VendorStore')

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    payment_method = Column(String(50))
    transaction_id = Column(String(100), unique=True)
    amount = Column(Numeric(10,2))
    status = Column(String(20))
    payment_details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship('Order', back_populates='payments')
