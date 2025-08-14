import pyodbc

def get_db_connection():
    return pyodbc.connect(
        'DRIVER=ODBC Driver 18 for SQL Server;'
        'SERVER={server};'
        'DATABASE=ecommerce_vh5;'
        'UID=username;'
        'PWD=password;'
        'TrustServerCertificate=yes;'
    )
