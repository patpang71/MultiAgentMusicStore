import re
from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def _normalize_phone(phone: str) -> str:
    # Strip spaces, parentheses, and dashes so "+49 0711 2842222" → "+4907112842222"
    return re.sub(r'[\s()\-]', '', phone)


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


def get_customer_by_phone(phone: str) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for get_customer_by_phone: {phone}")
    try:
        normalized = _normalize_phone(str(phone))
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM Customer
                   WHERE REPLACE(REPLACE(REPLACE(REPLACE(Phone, ' ', ''), '(', ''), ')', ''), '-', '') = %s""",
                (normalized,)
            )
            row = cursor.fetchone()
        conn.close()

        if not row:
            return {"message": f"Cannot find customer with phone {phone}"}
        logger.info(f"Found customer with phone {phone}")
        return _format_customer(row)

    except Exception as e:
        logger.error(f"Error in get_customer_by_phone: {str(e)}")
        return {"message": f"Error {str(e)}"}
