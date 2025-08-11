import pyodbc

def get_db_connection():
    return pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=DEVDENECOM4.SERVICES.WEBROOT;'
        'DATABASE=ecommerce_vh5;'
        'Trusted_Connection=yes;'
    )
