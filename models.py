#this manages db for storing all business owner accounts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base,relationship
from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column,Integer,String,Float,ForeignKey,DATETIME,text,func,JSON,Boolean
from dotenv import load_dotenv
from datetime import datetime
import re
import os
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment ")

engine = create_engine(DATABASE_URL,echo=True)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()

#slugify function
def slugify(text:str)-> str:
    s = re.sub(r"[^\w\s-]","",text).strip().lower()
    s = re.sub(r"[-\s]+","-",s)
    return s 


#business table
class BusinessOwner(Base):
    __tablename__ = "business_owners"
    id = Column(Integer,primary_key=True,index=True,autoincrement=True)
    business_name = Column(String(255),unique=True,nullable=False)
    email = Column(String(255),unique=True,nullable=False)
    phone = Column(String(20),unique=True,nullable=False)
    password_hash = Column(String(255),nullable=False)
    created_at = Column(DATETIME,server_default=func.now())
    slug = Column(String,unique=True,nullable=False)

    #relationships
    customers = relationship("Customer",back_populates="owner",cascade="all,delete-orphan")
    products = relationship("Product",back_populates="owner",cascade="all,delete-orphan")
    orders = relationship("Order",back_populates="owner",cascade="all,delete-orphan")
    carts= relationship("Cart",back_populates="owner",cascade="all,delete-orphan")
    payments= relationship("Payment",back_populates="owner",cascade="all,delete-orphan")
    chatlogs = relationship("Chatlog",back_populates="owner",cascade='all,delete-orphan')
    settings = relationship("BusinessSettings",back_populates="owner",cascade="all,delete-orphan",uselist=False)

    def verify_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        return pbkdf2_sha256.verify(password, self.password_hash)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True,index=True,autoincrement=True)
    owner_id = Column(Integer,ForeignKey("business_owners.id"),nullable=False)
    name = Column(String(255),nullable=False,index=True)
    description =Column(String(500),nullable=True)
    price = Column(Float,nullable=False)
    size = Column(String(50),nullable=True)
    stock = Column(Integer,nullable=False, default=0)
    image_path =Column(String(300),nullable=True)
    created_at = Column(DATETIME,server_default=func.now())
    #relationships
    owner= relationship("BusinessOwner",back_populates="products")
    orders = relationship("Order",back_populates="product",cascade="all,delete-orphan")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer,primary_key=True,index=True,autoincrement=True)
    owner_id =Column(Integer,ForeignKey("business_owners.id"),nullable=False)
    name = Column(String(255),nullable=True,index=True)#this is optional provided they give a name
    phone= Column(String(20),nullable=False,unique=True,index=True)
    created_at = Column(DATETIME(timezone=True),server_default=func.now())

    #relationships
    owner = relationship("BusinessOwner",back_populates="customers")
    orders = relationship("Order",back_populates="customer")
    carts = relationship("Cart",back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer,primary_key=True, index=True,autoincrement=True)
    owner_id = Column(Integer,ForeignKey("business_owners.id"),nullable=False)
    product_id =Column(Integer,ForeignKey("products.id"),nullable=False)
    quantity = Column(Integer,nullable=False,default=0)
    customer_phone = Column(String(20),nullable=False,index=True)
    customer_id =Column(Integer,ForeignKey("customers.id"),nullable=False)
    total_price= Column(Float,nullable=False)
    status = Column(String(50),nullable=False,default="pending")#pending or completed then i would add cancelled
    created_at =Column(DATETIME,server_default=func.now())
    #relationships
    owner=relationship("BusinessOwner",back_populates="orders")
    product= relationship("Product",back_populates="orders")
    customer = relationship("Customer",back_populates="orders")
    payments = relationship("Payment",back_populates="order",cascade="all,delete-orphan")

#**CART TABLE
class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True,index=True,autoincrement=True)
    owner_id =Column(Integer,ForeignKey("business_owners.id", ondelete="CASCADE"),nullable=False,index=True)
    customer_id = Column(Integer,ForeignKey("customers.id",ondelete="CASCADE"),nullable=False,index=True)
    items=Column(JSON,nullable=False)
    total_amount=Column(Float,default=0.0)
    delivery_fee=Column(Float,default=0.0)
    final_total=Column(Float,default=0.0)
    status=Column(String(50),default="active")
    created_at=Column(DATETIME,default=datetime.utcnow) 
    updated_at=Column(DATETIME,default=datetime.utcnow,onupdate=datetime.utcnow)

    #relationships
    owner=relationship("BusinessOwner",back_populates="carts")
    customer = relationship("Customer",back_populates="carts")

# Payment table
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer,primary_key=True, index=True,autoincrement=True)
    owner_id = Column(Integer,ForeignKey("business_owners.id",ondelete="CASCADE"),nullable=False,index=True)
    order_id=Column(Integer,ForeignKey("orders.id",ondelete="CASCADE"),nullable=False,index=True)
    payment_reference=Column(String(255),nullable=True)
    amount=Column(Float,nullable=False)
    payment_method=Column(String(50),nullable=False,)
    status=Column(String(50),default= "pending")
    gateway_response=Column(JSON)
    created_at=Column(DATETIME,default=datetime.utcnow)
    updated_at =Column(DATETIME,default=datetime.utcnow,onupdate=datetime.utcnow)
    #relationships
    owner = relationship("BusinessOwner",back_populates="payments")
    order = relationship("Order",back_populates="payments")

##
class Chatlog(Base):
    __tablename__ = "chatlogs"
    id = Column(Integer,primary_key=True,index=True,autoincrement=True)
    owner_id = Column(Integer,ForeignKey("business_owners.id", ondelete="CASCADE"),nullable=False,index=True)
    customer_phone = Column(String(20),nullable=False,index=True)
    message = Column(String(500),nullable=False)
    message_type = Column(String(50),default="text")
    session_id = Column(String(255),nullable=True)
    created_at = Column(DATETIME,server_default=func.now())

    #relatioships
    owner = relationship("BusinessOwner",back_populates="chatlogs")

class BusinessSettings(Base):
    __tablename__="business_settings"
    id =Column(Integer,primary_key=True,nullable=False,index=True,autoincrement=True)
    owner_id =Column(Integer,ForeignKey("business_owners.id",ondelete="CASCADE"),nullable=False,index=True,unique =True)
    whatsapp_number = Column(String(20),nullable=True)
    currency = Column(String(10),default="NGN")
    delivery_enabled = Column(Boolean,default=False)
    pickup_enabled = Column(Boolean,default=False)
    auto_confirm_orders = Column(Boolean,default=False)
    order_notification_email = Column(String(255),nullable=True)
    order_notification_phone = Column(String(20),nullable=True)
    created_at = Column(DATETIME,server_default=func.now())
    #relationship
    owner = relationship("BusinessOwner",back_populates="settings")