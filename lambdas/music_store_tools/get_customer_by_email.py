from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)


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
        logger = logging.getLogger(__name__)
        logger.info(f"Received input for get_customer_by_email: {email}")
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Customer WHERE Email = %s", (email,)
            )
            row = cursor.fetchone()
        conn.close()

        if not row:
            return {"message": f"Cannot find customer with email {email}"}

        logger.info(f"Found customer with email {email}")
        return _format_customer(row)

    except Exception as e:
        logger.error(f"Error in get_customer_by_email: {str(e)}")
        return {"message": f"Error {str(e)}"}
