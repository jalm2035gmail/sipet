from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_, desc, asc, case
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.orders.models import Order, OrderItem
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reviews.models import (
    ProductReview,
    ReviewAnalytics,
    ReviewMedia,
    ReviewReport,
    ReviewVote,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

# ...existing code from user request pasted here...
