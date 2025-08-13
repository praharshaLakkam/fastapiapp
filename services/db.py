import pyodbc

def get_db_connection():
    return pyodbc.connect(
        'DRIVER=ODBC Driver 18 for SQL Server;'
        'SERVER=DEVDENECOM4.SERVICES.WEBROOT;'
        'DATABASE=ecommerce_vh5;'
        'UID=ecomuser;'
        'PWD=k74*8lp!;'
        'TrustServerCertificate=yes;'
    )
