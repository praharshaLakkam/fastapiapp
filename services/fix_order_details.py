from services.db import get_db_connection
import pyodbc

def fix_order_dates(vendor_order_code, current_user= None):
    """
    Calls the stored procedure to fix order item dates for a given vendor_order_code.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            EXEC dbo.FixOrderItemDates_AllLines 
                @vendor_order_code = ?, 
                @current_user = ?
        """, (vendor_order_code, current_user))

        # If stored proc returns results
        result = []
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                result.append(dict(zip(columns, row)))

        conn.commit()
        cursor.close()
        return {"status": "success", "data": result}

    except pyodbc.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}
    finally:
        if conn:
            conn.close()
