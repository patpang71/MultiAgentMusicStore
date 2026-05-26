from db_connection import get_connection


def _format_customer(row: dict) -> dict:
    return {
        "customerId": str(row["CustomerId"]),
        "firstName":  row["FirstName"],
        "lastName":   row["LastName"],
        "email":      row["Email"],
        "company":    row["Company"],
        "city":       row["City"],
        "country":    row["Country"],
        "phone":      row["Phone"],
    }


def get_customer_by_email(email: str) -> dict:
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Customer WHERE Email = %s", (email,)
            )
            row = cursor.fetchone()
        conn.close()

        if not row:
            return {"message": f"Cannot find customer with email {email}"}

        return _format_customer(row)

    except Exception as e:
        return {"message": f"Error {str(e)}"}
