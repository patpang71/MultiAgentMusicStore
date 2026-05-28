from collections import defaultdict
from itertools import zip_longest

from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)

def get_songs_by_genre(genre_input: str) -> dict:
    logger = logging.getLogger(__name__)
    logger.info(f"Received input for get_songs_by_genre: {genre_input}")
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
                AND ge.Name = %s
                ORDER BY ar.Name, tr.Name
            """
            cursor.execute(sql, (genre_input,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": "Cannot find any genre"}

        by_artist = defaultdict(list)
        for row in rows:
            by_artist[row["artist"]].append({
                "trackName": row["trackName"],
                "albumTitle": row["albumTitle"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mediaType": row["mediaType"],
                "composer": row["composer"],
                "milliseconds": str(row["milliseconds"]),
                "bytes": str(row["bytes"]),
                "unitPrice": str(row["unitPrice"]),
            })

        # Round-robin: one track per artist per round so no artist dominates
        interleaved = []
        for round_tracks in zip_longest(*by_artist.values()):
            interleaved.extend(t for t in round_tracks if t is not None)

        logger.info(f"Found {len(rows)} tracks for genre '{genre_input}' across {len(by_artist)} artists")
        return {"genre": genre_input, "tracks": interleaved}

    except Exception as e:
        logger.error(f"Error in get_songs_by_genre: {str(e)}")
        return {"message": f"Error {str(e)}"}
