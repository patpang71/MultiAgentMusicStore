from db_connection import get_connection


def get_albums_by_artist(artist_input: str) -> dict:
    try:
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
        return {"artistNameInput": artist_input, "results": results}

    except Exception as e:
        return {"message": f"Error {str(e)}"}
