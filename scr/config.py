import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/ecommerce_inteligente_simple'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
    
