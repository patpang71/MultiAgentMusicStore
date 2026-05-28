from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def get_track_details_by_id(track_id: int) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for get_track_details_by_id: {track_id}")
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
                AND tr.TrackId = %s
            """
            cursor.execute(sql, (track_id,))
            row = cursor.fetchone()
        conn.close()

        if not row:
            return {"message": f"Cannot find any song from track Id {track_id}"}

        logger.info(f"Found details for track Id {track_id}: {row['trackName']} by {row['artist']}")
        return {
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

    except Exception as e:
        logger.error(f"Error in get_track_details_by_id: {str(e)}")
        return {"message": f"Error {str(e)}"}
