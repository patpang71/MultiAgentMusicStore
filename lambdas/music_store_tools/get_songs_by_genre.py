from db_connection import get_connection


def get_songs_by_genre(genre_input: str) -> dict:
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
            """
            cursor.execute(sql, (genre_input,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"message": "Cannot find any genre"}

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
        return {"genre": genre_input, "tracks": tracks}

    except Exception as e:
        return {"message": f"Error {str(e)}"}
