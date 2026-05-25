from db_connection import get_connection


def get_invoices_by_customer_sorted_by_date(customer_id) -> list | dict:
    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        return {"message": "Error customer_id must be numeric"}

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT inv.InvoiceId    AS invoiceId,
                       inv.CustomerId   AS customerId,
                       inv.InvoiceDate  AS invoiceDate,
                       inv.BillingAddress   AS billingAddress,
                       inv.BillingCity      AS billingCity,
                       inv.BillingState     AS billingState,
                       inv.BillingCountry   AS billingCountry
                FROM Invoice inv
                WHERE inv.CustomerId = %s
                ORDER BY inv.InvoiceDate DESC
            """
            cursor.execute(sql, (customer_id,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": f"Cannot find any invoices for customer {customer_id}"}

        return [
            {
                "invoiceId":      str(row["invoiceId"]),
                "customerId":     str(row["customerId"]),
                "invoiceDate":    str(row["invoiceDate"]),
                "billingAddress": row["billingAddress"],
                "billingCity":    row["billingCity"],
                "billingCountry": row["billingCountry"],
            }
            for row in rows
        ]

    except Exception as e:
        return {"message": f"Error {str(e)}"}
