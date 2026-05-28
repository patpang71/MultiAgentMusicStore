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


def get_customer_by_id(customer_id) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for get_customer_by_id: {customer_id}")

    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        return {"message": "Error customer_id must be numeric"}

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Customer WHERE CustomerId = %s", (customer_id,)
            )
            row = cursor.fetchone()
        conn.close()

        if not row:
            return {"message": f"Cannot find customer with id {customer_id}"}
        logger.info(f"Found customer with id {customer_id}")
        return _format_customer(row)

    except Exception as e:
        logger.error(f"Error in get_customer_by_id: {str(e)}")
        return {"message": f"Error {str(e)}"}
