from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from models import (
    Base, BusinessOwner, Product, Customer, Order, Cart, 
    Payment, Chatlog, BusinessSettings, engine, SessionLocal, slugify
)
from typing import Optional, List, Dict, Any
from datetime import datetime

# =============================================
# DATABASE INITIALIZATION
# =============================================

def create_main_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

def get_global_db():
    """Yield a DB session (for dependency injection in routes)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =============================================
# BUSINESS OWNER OPERATIONS
# =============================================

def create_business_owner(data: dict) -> str:
    """Add a new business owner to the database and return the slug."""
    db: Session = SessionLocal()
    try:
        slug = slugify(data["business_name"])
        owner = BusinessOwner(
            business_name=data["business_name"],
            email=data["email"],
            phone=data["phone"],
            password_hash=pbkdf2_sha256.hash(data["password"]),
            slug=slug
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        return slug
    finally:
        db.close()

def verify_login(email: str, password: str) -> Optional[BusinessOwner]:
    """Check if email/password match a business owner."""
    db: Session = SessionLocal()
    try:
        owner = db.query(BusinessOwner).filter_by(email=email).first()
        if owner and pbkdf2_sha256.verify(password, owner.password_hash):
            return owner
        return None
    finally:
        db.close()

def get_business_owner_by_slug(slug: str) -> Optional[BusinessOwner]:
    """Get business owner by slug."""
    db: Session = SessionLocal()
    try:
        return db.query(BusinessOwner).filter_by(slug=slug).first()
    finally:
        db.close()

def get_business_owner_by_id(owner_id: int) -> Optional[BusinessOwner]:
    """Get business owner by ID."""
    db: Session = SessionLocal()
    try:
        return db.query(BusinessOwner).filter_by(id=owner_id).first()
    finally:
        db.close()

def update_business_owner(owner_id: int, data: dict) -> Optional[BusinessOwner]:
    """Update business owner information."""
    db: Session = SessionLocal()
    try:
        owner = db.query(BusinessOwner).filter_by(id=owner_id).first()
        if owner:
            for key, value in data.items():
                if key == "password":
                    owner.password_hash = pbkdf2_sha256.hash(value)
                elif key == "business_name":
                    owner.business_name = value
                    owner.slug = slugify(value)
                elif hasattr(owner, key):
                    setattr(owner, key, value)
            db.commit()
            db.refresh(owner)
        return owner
    finally:
        db.close()

# =============================================
# PRODUCT OPERATIONS
# =============================================

def create_product(owner_id: int, data: dict) -> Optional[Product]:
    """Create a new product."""
    db: Session = SessionLocal()
    try:
        product = Product(
            owner_id=owner_id,
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            size=data.get("size"),
            stock=data.get("stock", 0),
            image_path=data.get("image_path")
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    finally:
        db.close()

def get_products_by_owner(owner_id: int, limit: int = 100, offset: int = 0) -> List[Product]:
    """Get all products for a business owner."""
    db: Session = SessionLocal()
    try:
        return db.query(Product).filter_by(owner_id=owner_id).offset(offset).limit(limit).all()
    finally:
        db.close()

def get_product_by_id(product_id: int, owner_id: int) -> Optional[Product]:
    """Get a specific product by ID and owner."""
    db: Session = SessionLocal()
    try:
        return db.query(Product).filter_by(id=product_id, owner_id=owner_id).first()
    finally:
        db.close()

def update_product(product_id: int, owner_id: int, data: dict) -> Optional[Product]:
    """Update product information."""
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter_by(id=product_id, owner_id=owner_id).first()
        if product:
            for key, value in data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            db.commit()
            db.refresh(product)
        return product
    finally:
        db.close()

def delete_product(product_id: int, owner_id: int) -> bool:
    """Delete a product."""
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter_by(id=product_id, owner_id=owner_id).first()
        if product:
            db.delete(product)
            db.commit()
            return True
        return False
    finally:
        db.close()

def update_product_stock(product_id: int, owner_id: int, quantity_change: int) -> Optional[Product]:
    """Update product stock (can be positive or negative)."""
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter_by(id=product_id, owner_id=owner_id).first()
        if product:
            product.stock += quantity_change
            if product.stock < 0:
                product.stock = 0
            db.commit()
            db.refresh(product)
        return product
    finally:
        db.close()

# =============================================
# CUSTOMER OPERATIONS
# =============================================

def create_or_get_customer(owner_id: int, phone: str, name: str = None) -> Customer:
    """Create a new customer or get existing one by phone."""
    db: Session = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(phone=phone, owner_id=owner_id).first()
        if not customer:
            customer = Customer(
                owner_id=owner_id,
                phone=phone,
                name=name
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        elif name and not customer.name:
            customer.name = name
            db.commit()
            db.refresh(customer)
        return customer
    finally:
        db.close()

def get_customers_by_owner(owner_id: int, limit: int = 100, offset: int = 0) -> List[Customer]:
    """Get all customers for a business owner."""
    db: Session = SessionLocal()
    try:
        return db.query(Customer).filter_by(owner_id=owner_id).offset(offset).limit(limit).all()
    finally:
        db.close()

def get_customer_by_phone(owner_id: int, phone: str) -> Optional[Customer]:
    """Get customer by phone number."""
    db: Session = SessionLocal()
    try:
        return db.query(Customer).filter_by(owner_id=owner_id, phone=phone).first()
    finally:
        db.close()

def update_customer(customer_id: int, owner_id: int, data: dict) -> Optional[Customer]:
    """Update customer information."""
    db: Session = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=customer_id, owner_id=owner_id).first()
        if customer:
            for key, value in data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            db.commit()
            db.refresh(customer)
        return customer
    finally:
        db.close()

# =============================================
# ORDER OPERATIONS
# =============================================

def create_order(data: dict) -> Optional[Order]:
    """Create a new order."""
    db: Session = SessionLocal()
    try:
        order = Order(
            owner_id=data["owner_id"],
            product_id=data["product_id"],
            customer_id=data["customer_id"],
            customer_phone=data["customer_phone"],
            quantity=data["quantity"],
            total_price=data["total_price"],
            status=data.get("status", "pending")
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    finally:
        db.close()

def get_orders_by_owner(owner_id: int, status: str = None, limit: int = 100, offset: int = 0) -> List[Order]:
    """Get orders for a business owner, optionally filtered by status."""
    db: Session = SessionLocal()
    try:
        query = db.query(Order).filter_by(owner_id=owner_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(desc(Order.created_at)).offset(offset).limit(limit).all()
    finally:
        db.close()

def get_orders_by_customer(owner_id: int, customer_phone: str, limit: int = 50) -> List[Order]:
    """Get orders for a specific customer."""
    db: Session = SessionLocal()
    try:
        return db.query(Order).filter_by(
            owner_id=owner_id, 
            customer_phone=customer_phone
        ).order_by(desc(Order.created_at)).limit(limit).all()
    finally:
        db.close()

def update_order_status(order_id: int, owner_id: int, status: str) -> Optional[Order]:
    """Update order status."""
    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter_by(id=order_id, owner_id=owner_id).first()
        if order:
            order.status = status
            db.commit()
            db.refresh(order)
        return order
    finally:
        db.close()

def get_order_by_id(order_id: int, owner_id: int) -> Optional[Order]:
    """Get a specific order by ID."""
    db: Session = SessionLocal()
    try:
        return db.query(Order).filter_by(id=order_id, owner_id=owner_id).first()
    finally:
        db.close()

# =============================================
# CART OPERATIONS
# =============================================

def create_or_update_cart(owner_id: int, customer_id: int, items: List[dict], 
                         delivery_fee: float = 0.0) -> Cart:
    """Create a new cart or update existing active cart."""
    db: Session = SessionLocal()
    try:
        # Get existing active cart
        cart = db.query(Cart).filter_by(
            owner_id=owner_id, 
            customer_id=customer_id, 
            status="active"
        ).first()
        
        # Calculate totals
        total_amount = sum(item.get("subtotal", 0) for item in items)
        final_total = total_amount + delivery_fee
        
        if cart:
            # Update existing cart
            cart.items = items
            cart.total_amount = total_amount
            cart.delivery_fee = delivery_fee
            cart.final_total = final_total
            cart.updated_at = datetime.utcnow()
        else:
            # Create new cart
            cart = Cart(
                owner_id=owner_id,
                customer_id=customer_id,
                items=items,
                total_amount=total_amount,
                delivery_fee=delivery_fee,
                final_total=final_total,
                status="active"
            )
            db.add(cart)
        
        db.commit()
        db.refresh(cart)
        return cart
    finally:
        db.close()

def get_active_cart(owner_id: int, customer_id: int) -> Optional[Cart]:
    """Get active cart for a customer."""
    db: Session = SessionLocal()
    try:
        return db.query(Cart).filter_by(
            owner_id=owner_id, 
            customer_id=customer_id, 
            status="active"
        ).first()
    finally:
        db.close()

def clear_cart(owner_id: int, customer_id: int) -> bool:
    """Clear/deactivate customer's cart."""
    db: Session = SessionLocal()
    try:
        cart = db.query(Cart).filter_by(
            owner_id=owner_id, 
            customer_id=customer_id, 
            status="active"
        ).first()
        if cart:
            cart.status = "completed"
            cart.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    finally:
        db.close()

# =============================================
# PAYMENT OPERATIONS
# =============================================

def create_payment(data: dict) -> Payment:
    """Create a new payment record."""
    db: Session = SessionLocal()
    try:
        payment = Payment(
            owner_id=data["owner_id"],
            order_id=data["order_id"],
            payment_reference=data.get("payment_reference"),
            amount=data["amount"],
            payment_method=data["payment_method"],
            status=data.get("status", "pending"),
            gateway_response=data.get("gateway_response")
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
    finally:
        db.close()

def update_payment_status(payment_id: int, owner_id: int, status: str, 
                         gateway_response: dict = None) -> Optional[Payment]:
    """Update payment status and gateway response."""
    db: Session = SessionLocal()
    try:
        payment = db.query(Payment).filter_by(id=payment_id, owner_id=owner_id).first()
        if payment:
            payment.status = status
            payment.updated_at = datetime.utcnow()
            if gateway_response:
                payment.gateway_response = gateway_response
            db.commit()
            db.refresh(payment)
        return payment
    finally:
        db.close()

def get_payments_by_owner(owner_id: int, status: str = None, limit: int = 100) -> List[Payment]:
    """Get payments for a business owner."""
    db: Session = SessionLocal()
    try:
        query = db.query(Payment).filter_by(owner_id=owner_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(desc(Payment.created_at)).limit(limit).all()
    finally:
        db.close()

# =============================================
# CHATLOG OPERATIONS
# =============================================

def create_chatlog(owner_id: int, customer_phone: str, message: str, 
                  message_type: str = "text", session_id: str = None) -> Chatlog:
    """Create a new chat log entry."""
    db: Session = SessionLocal()
    try:
        chatlog = Chatlog(
            owner_id=owner_id,
            customer_phone=customer_phone,
            message=message,
            message_type=message_type,
            session_id=session_id
        )
        db.add(chatlog)
        db.commit()
        db.refresh(chatlog)
        return chatlog
    finally:
        db.close()

def get_chatlogs_by_customer(owner_id: int, customer_phone: str, 
                           limit: int = 100, offset: int = 0) -> List[Chatlog]:
    """Get chat history for a specific customer."""
    db: Session = SessionLocal()
    try:
        return db.query(Chatlog).filter_by(
            owner_id=owner_id, 
            customer_phone=customer_phone
        ).order_by(desc(Chatlog.created_at)).offset(offset).limit(limit).all()
    finally:
        db.close()

def get_recent_chatlogs(owner_id: int, limit: int = 50) -> List[Chatlog]:
    """Get recent chat logs for a business owner."""
    db: Session = SessionLocal()
    try:
        return db.query(Chatlog).filter_by(owner_id=owner_id).order_by(
            desc(Chatlog.created_at)
        ).limit(limit).all()
    finally:
        db.close()

# =============================================
# BUSINESS SETTINGS OPERATIONS
# =============================================

def create_or_update_business_settings(owner_id: int, data: dict) -> BusinessSettings:
    """Create or update business settings."""
    db: Session = SessionLocal()
    try:
        settings = db.query(BusinessSettings).filter_by(owner_id=owner_id).first()
        
        if settings:
            # Update existing settings
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        else:
            # Create new settings
            settings = BusinessSettings(owner_id=owner_id, **data)
            db.add(settings)
        
        db.commit()
        db.refresh(settings)
        return settings
    finally:
        db.close()

def get_business_settings(owner_id: int) -> Optional[BusinessSettings]:
    """Get business settings for an owner."""
    db: Session = SessionLocal()
    try:
        return db.query(BusinessSettings).filter_by(owner_id=owner_id).first()
    finally:
        db.close()

# =============================================
# ANALYTICS AND REPORTING
# =============================================

def get_order_analytics(owner_id: int, days: int = 30) -> Dict[str, Any]:
    """Get order analytics for the last N days."""
    db: Session = SessionLocal()
    try:
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        orders = db.query(Order).filter(
            and_(Order.owner_id == owner_id, Order.created_at >= start_date)
        ).all()
        
        total_orders = len(orders)
        total_revenue = sum(order.total_price for order in orders)
        completed_orders = len([o for o in orders if o.status == "completed"])
        pending_orders = len([o for o in orders if o.status == "pending"])
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0
        }
    finally:
        db.close()

def get_top_products(owner_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top-selling products."""
    db: Session = SessionLocal()
    try:
        from sqlalchemy import func
        
        result = db.query(
            Product.id,
            Product.name,
            func.sum(Order.quantity).label('total_sold'),
            func.sum(Order.total_price).label('total_revenue')
        ).join(Order).filter(
            Product.owner_id == owner_id
        ).group_by(Product.id, Product.name).order_by(
            desc('total_sold')
        ).limit(limit).all()
        
        return [
            {
                "product_id": r.id,
                "product_name": r.name,
                "total_sold": r.total_sold,
                "total_revenue": r.total_revenue
            }
            for r in result
        ]
    finally:
        db.close()

def get_customer_analytics(owner_id: int) -> Dict[str, Any]:
    """Get customer analytics."""
    db: Session = SessionLocal()
    try:
        total_customers = db.query(Customer).filter_by(owner_id=owner_id).count()
        
        # Customers with orders
        customers_with_orders = db.query(Customer).filter(
            and_(Customer.owner_id == owner_id, Customer.orders.any())
        ).count()
        
        return {
            "total_customers": total_customers,
            "customers_with_orders": customers_with_orders,
            "conversion_rate": (customers_with_orders / total_customers * 100) if total_customers > 0 else 0
        }
    finally:
        db.close()

# =============================================
# UTILITY FUNCTIONS
# =============================================

def search_products(owner_id: int, search_term: str, limit: int = 20) -> List[Product]:
    """Search products by name or description."""
    db: Session = SessionLocal()
    try:
        return db.query(Product).filter(
            and_(
                Product.owner_id == owner_id,
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%")
                )
            )
        ).limit(limit).all()
    finally:
        db.close()

def get_low_stock_products(owner_id: int, threshold: int = 5) -> List[Product]:
    """Get products with low stock."""
    db: Session = SessionLocal()
    try:
        return db.query(Product).filter(
            and_(Product.owner_id == owner_id, Product.stock <= threshold)
        ).all()
    finally:
        db.close()

def backup_business_data(owner_id: int) -> Dict[str, Any]:
    """Get all business data for backup purposes."""
    db: Session = SessionLocal()
    try:
        owner = db.query(BusinessOwner).filter_by(id=owner_id).first()
        if not owner:
            return {}
        
        return {
            "business_info": {
                "id": owner.id,
                "business_name": owner.business_name,
                "email": owner.email,
                "phone": owner.phone,
                "slug": owner.slug,
                "created_at": owner.created_at.isoformat() if owner.created_at else None
            },
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "size": p.size,
                    "stock": p.stock,
                    "image_path": p.image_path
                }
                for p in owner.products
            ],
            "customers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "phone": c.phone,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in owner.customers
            ],
            "orders_count": len(owner.orders),
            "settings": {
                "whatsapp_number": owner.settings.whatsapp_number if owner.settings else None,
                "currency": owner.settings.currency if owner.settings else "NGN",
                "delivery_enabled": owner.settings.delivery_enabled if owner.settings else False,
                "pickup_enabled": owner.settings.pickup_enabled if owner.settings else False
            } if owner.settings else {}
        }
    finally:
        db.close()