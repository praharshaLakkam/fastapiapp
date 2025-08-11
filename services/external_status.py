from services.db import get_db_connection

def check_external_order_status(vendor_order_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Get order_header_id from vendor_order_code
        cursor.execute("""
            SELECT oh.order_header_id 
            FROM vendor_order vo
            JOIN order_header oh ON oh.vendor_order_id = vo.vendor_order_id
            WHERE vo.vendor_order_code = ?
        """, (vendor_order_code,))

        result = cursor.fetchone()
        print(result)
        if not result:
            return f"❌ Invalid vendor_order_code: {vendor_order_code}"

        order_header_id = result.order_header_id

        # Step 2: Check for failure messages
        cursor.execute("""
            SELECT sfdc_response_message 
            FROM sfdc_opportunity_update_failure 
            WHERE order_header_id = ?
        """, (order_header_id,))

        failure = cursor.fetchone()
        if failure:
            return f"❌ Order Failed: {failure.sfdc_response_message}"
        else:
            return "✅ Order Successful"

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

    finally:
        if 'conn' in locals():
            conn.close()
