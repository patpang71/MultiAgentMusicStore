from db_connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)


def get_albums_by_artist(artist_input: str) -> dict:
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Received input for get_albums_by_artist: {artist_input}")
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT ar.Name AS artist, al.Title AS album
                FROM Artist ar, Album al
                WHERE ar.ArtistId = al.ArtistId
                AND ar.Name LIKE %s
                ORDER BY ar.Name, al.Title
            """
            cursor.execute(sql, (f"%{artist_input}%",))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": "Cannot find any artists"}

        grouped: dict = {}
        for row in rows:
            artist = row["artist"]
            if artist not in grouped:
                grouped[artist] = []
            grouped[artist].append(row["album"])

        results = [
            {"artist": artist, "albums": albums}
            for artist, albums in grouped.items()
        ]
        logger.info(f"Found {len(results)} artists matching input '{artist_input}'")
        return {"artistNameInput": artist_input, "results": results}

    except Exception as e:
        logger.error(f"Error in get_albums_by_artist: {str(e)}")
        return {"message": f"Error {str(e)}"}
