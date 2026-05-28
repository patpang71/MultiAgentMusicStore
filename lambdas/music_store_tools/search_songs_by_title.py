from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def search_songs_by_title(title_input: str) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for search_songs_by_title: {title_input}")
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT tr.Name AS trackName, al.Title AS albumTitle, ar.Name AS artist,
                       ge.Name AS genre, me.Name AS mediaType, tr.Composer AS composer,
                       tr.Milliseconds AS milliseconds, tr.Bytes AS bytes,
                       tr.UnitPrice AS unitPrice
                FROM Track tr, Album al, Artist ar, Genre ge, MediaType me
                WHERE tr.AlbumId = al.AlbumId
                AND tr.GenreId = ge.GenreId
                AND tr.MediaTypeId = me.MediaTypeId
                AND al.ArtistId = ar.ArtistId
                AND tr.Name LIKE %s
                LIMIT 10
            """
            cursor.execute(sql, (f"%{title_input}%",))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": f"Cannot find any song from title {title_input}"}

        tracks = [
            {
                "trackName": row["trackName"],
                "albumTitle": row["albumTitle"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mediaType": row["mediaType"],
                "composer": row["composer"],
                "milliseconds": str(row["milliseconds"]),
                "bytes": str(row["bytes"]),
                "unitPrice": str(row["unitPrice"]),
            }
            for row in rows
        ]
        logger.info(f"Found {len(tracks)} tracks matching title input '{title_input}'")
        return {"trackInput": title_input, "tracks": tracks}

    except Exception as e:
        logger.error(f"Error in search_songs_by_title: {str(e)}")
        return {"message": f"Error {str(e)}"}
