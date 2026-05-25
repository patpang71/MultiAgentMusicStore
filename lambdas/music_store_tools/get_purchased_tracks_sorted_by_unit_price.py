from db_connection import get_connection


def get_purchased_tracks_sorted_by_unit_price(_input=None) -> list | dict:
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
        return {"message": f"Error {str(e)}"}
