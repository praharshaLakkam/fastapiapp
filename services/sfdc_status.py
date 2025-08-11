from services.db import get_db_connection

def check_sfdc_order(vendor_order_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Get opportunity ID using vendor order code
        cursor.execute("""
            SELECT oo.salesforce_opportunity_id 
            FROM dbo.order_opportunity AS oo
            JOIN dbo.order_header AS oh ON oh.order_header_id = oo.order_header_id
            JOIN dbo.vendor_order AS vo ON vo.vendor_order_id = oh.vendor_order_id
            WHERE vo.vendor_order_code = ?
        """, (vendor_order_code,))

        result = cursor.fetchone()
        if not result:
            return "❌ No opportunity ID found for the given vendor order code."

        opportunity_id = result.salesforce_opportunity_id

        # Step 2: Call stored procedure with opportunity_id
        cursor.execute("""
            DECLARE @response_code INT,
                    @message VARCHAR(100);
            EXEC dbo.usp_sfdc_select_opportunity 
                @opportunity_id = ?, 
                @response_code = @response_code OUTPUT, 
                @message = @message OUTPUT;
        """, (opportunity_id,))

        row = cursor.fetchone()
        if row:
            if hasattr(row, 'failure_description') and row.failure_description.lower() != 'success':
                return f"❌ Order failed: {row.failure_description}"
            else:
                return "✅ Order successful"
        else:
            return "ℹ️ No record found for the given opportunity ID."

    except Exception as e:
        return f"⚠️ Error executing SFDC procedure: {str(e)}"

    finally:
        if 'conn' in locals():
            conn.close()
