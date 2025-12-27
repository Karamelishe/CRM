from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from ..models.models import OrderStatus, DiscountType


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: int
    stock: int = 0
    image: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    is_active: Optional[bool] = None


class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CouponBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: DiscountType
    value: float
    min_total: int = 0
    max_uses_per_user: int = 1
    global_limit: int = 100


class CouponCreate(CouponBase):
    active: bool = True


class Coupon(CouponBase):
    id: int
    times_used: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemCreate(CartItemBase):
    pass


class CartItem(CartItemBase):
    id: int
    created_at: datetime
    product: Product

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    id: int
    product: Product
    quantity: int
    unit_price: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    note: Optional[str] = None
    billing_email: Optional[str] = None
    coupon_code: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderStatusUpdate(BaseModel):
    from_status: OrderStatus
    to_status: OrderStatus
    comment: Optional[str] = None


class Order(BaseModel):
    id: int
    status: OrderStatus
    total_amount: int
    discount_applied: int
    coupon_code: Optional[str]
    lab_flag: Optional[str]
    note: Optional[str]
    billing_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class CartSummary(BaseModel):
    items: List[CartItem]
    subtotal: int
    discount: int = 0
    total: int = 0
    applied_coupon: Optional[str] = None


class CouponApplyRequest(BaseModel):
    code: str
    cart_total: int
    billing_email: Optional[str] = None
