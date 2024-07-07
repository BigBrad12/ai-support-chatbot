import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    OPENAI_API_KEY = os.environ.get('OPENAI_KEY')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///default.db'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': Config
}