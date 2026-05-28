from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def search_tracks_by_artist(artist_input: str) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for search_tracks_by_artist: {artist_input}")
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
                AND ar.Name = %s
                LIMIT 20
            """
            cursor.execute(sql, (artist_input,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": "Cannot find any artist"}

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
        logger.info(f"Found {len(tracks)} tracks for artist '{artist_input}'")
        return {"artist": artist_input, "tracks": tracks}

    except Exception as e:
        logger.error(f"Error in search_tracks_by_artist: {str(e)}")
        return {"message": f"Error {str(e)}"}
