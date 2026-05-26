from get_albums_by_artist import get_albums_by_artist
from search_tracks_by_artist import search_tracks_by_artist
from get_songs_by_genre import get_songs_by_genre
from search_songs_by_title import search_songs_by_title
from get_track_details_by_id import get_track_details_by_id
from get_invoices_by_customer_sorted_by_date import get_invoices_by_customer_sorted_by_date
from get_purchased_tracks_sorted_by_unit_price import get_purchased_tracks_sorted_by_unit_price
from get_detail_line_item_for_invoice import get_detail_line_item_for_invoice
from get_customer_by_id import get_customer_by_id
from get_customer_by_email import get_customer_by_email
from get_customer_by_phone import get_customer_by_phone

TOOL_NAMES = {
    "get_albums_by_artist",
    "search_tracks_by_artist",
    "get_songs_by_genre",
    "search_songs_by_title",
    "get_track_details_by_id",
    "get_invoices_by_customer_sorted_by_date",
    "get_purchased_tracks_sorted_by_unit_price",
    "get_detail_line_item_for_invoice",
    "get_customer_by_id",
    "get_customer_by_email",
    "get_customer_by_phone",
}

# Tools that require no input value
NO_INPUT_TOOLS = {
    "get_purchased_tracks_sorted_by_unit_price",
}


def handler(event, context):
    tool_name = event.get("tool")
    input_value = event.get("input")

    if not tool_name:
        return {"message": "Error missing required field: tool"}

    if tool_name not in TOOL_NAMES:
        return {"message": f"Error unknown tool: {tool_name}"}

    if input_value is None and tool_name not in NO_INPUT_TOOLS:
        return {"message": "Error missing required field: input"}

    tools = {
        "get_albums_by_artist":                     get_albums_by_artist,
        "search_tracks_by_artist":                  search_tracks_by_artist,
        "get_songs_by_genre":                       get_songs_by_genre,
        "search_songs_by_title":                    search_songs_by_title,
        "get_track_details_by_id":                  get_track_details_by_id,
        "get_invoices_by_customer_sorted_by_date":   get_invoices_by_customer_sorted_by_date,
        "get_purchased_tracks_sorted_by_unit_price": get_purchased_tracks_sorted_by_unit_price,
        "get_detail_line_item_for_invoice":          get_detail_line_item_for_invoice,
        "get_customer_by_id":                        get_customer_by_id,
        "get_customer_by_email":                     get_customer_by_email,
        "get_customer_by_phone":                     get_customer_by_phone,
    }
    return tools[tool_name](input_value)
