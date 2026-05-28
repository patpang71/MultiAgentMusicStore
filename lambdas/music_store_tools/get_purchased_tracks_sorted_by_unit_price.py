from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def get_purchased_tracks_sorted_by_unit_price(_input=None) -> list | dict:
    logger = logging.getLogger(__name__)
    logger.info("Received input for get_purchased_tracks_sorted_by_unit_price")
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT DISTINCT
                    tr.TrackId  AS trackId,
                    tr.Name     AS trackName,
                    ar.Name     AS artist,
                    al.Title    AS album,
                    il.UnitPrice AS unitPrice
                FROM InvoiceLine il
                JOIN Track  tr ON il.TrackId  = tr.TrackId
                JOIN Album  al ON tr.AlbumId  = al.AlbumId
                JOIN Artist ar ON al.ArtistId = ar.ArtistId
                ORDER BY il.UnitPrice DESC, tr.Name ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": "Cannot find any purchased tracks"}

        logger.info(f"Found {len(rows)} purchased tracks sorted by unit price")
        return [
            {
                "trackId":   str(row["trackId"]),
                "trackName": row["trackName"],
                "artist":    row["artist"],
                "album":     row["album"],
                "unitPrice": str(row["unitPrice"]),
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error in get_purchased_tracks_sorted_by_unit_price: {str(e)}")
        return {"message": f"Error {str(e)}"}
