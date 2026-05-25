from db_connection import get_connection


def get_detail_line_item_for_invoice(invoice_id) -> dict:
    try:
        invoice_id = int(invoice_id)
    except (TypeError, ValueError):
        return {"message": "Error invoice_id must be numeric"}

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT inv.InvoiceId         AS invoiceId,
                       inv.CustomerId        AS customerId,
                       inv.InvoiceDate       AS invoiceDate,
                       inv.BillingAddress    AS billingAddress,
                       inv.BillingCity       AS billingCity,
                       inv.BillingState      AS billingState,
                       inv.BillingCountry    AS billingCountry,
                       inv.BillingPostalCode AS billingPostalCode,
                       inv.Total             AS total,
                       il.InvoiceLineId      AS invoiceLineId,
                       il.TrackId            AS trackId,
                       tr.Name               AS trackName,
                       il.UnitPrice          AS unitPrice,
                       il.Quantity           AS quantity
                FROM Invoice inv, InvoiceLine il, Track tr
                WHERE inv.InvoiceId = il.InvoiceId
                AND   il.TrackId    = tr.TrackId
                AND   inv.InvoiceId = %s
                ORDER BY il.InvoiceLineId ASC
            """
            cursor.execute(sql, (invoice_id,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": f"Cannot find invoice {invoice_id}"}

        first = rows[0]
        return {
            "invoiceId":         str(first["invoiceId"]),
            "customerId":        str(first["customerId"]),
            "invoiceDate":       str(first["invoiceDate"]),
            "billingAddress":    first["billingAddress"],
            "billingCity":       first["billingCity"],
            "billingCountry":    first["billingCountry"],
            "billingPostalCode": str(first["billingPostalCode"]),
            "total":             str(first["total"]),
            "lineItems": [
                {
                    "invoiceLineId": str(row["invoiceLineId"]),
                    "trackId":       str(row["trackId"]),
                    "trackName":     row["trackName"],
                    "unitPrice":     str(row["unitPrice"]),
                    "quantity":      str(row["quantity"]),
                }
                for row in rows
            ],
        }

    except Exception as e:
        return {"message": f"Error {str(e)}"}
