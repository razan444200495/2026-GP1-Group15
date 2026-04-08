class Config:
    SECRET_KEY = "afaq-secret-key"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost:3306/afaq_db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False