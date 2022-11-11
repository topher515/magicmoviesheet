import sys
import os
import pytz
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from magicmovie.lib.movie_meta import MovieNotFound, fetch_movie_meta
from magicmovie.lib.spreadsheet import autosaving_sheet

# Sheet Col Names
ADDED_COL_NAME = "!Added"
GENRE_COL_NAME = "!Genre"
IMDB_RATING_COL_NAME = "!IMDB Rating"
TITLE_COL_NAME = "!Title"
DIRECTOR_COL_NAME = "!Director"
FAIL_COL_NAME = "!Fail"

def main():

    movie_speadsheet_id = os.getenv('MOVIE_SPREADSHEET_ID')

    with autosaving_sheet(movie_speadsheet_id) as sheet:

        row_update_count = 0
        for i in range(2, len(sheet)+1):

            cell_added = sheet.get_cell(i, ADDED_COL_NAME)
            cell_genre = sheet.get_cell(i, GENRE_COL_NAME)
            cell_imdb_r = sheet.get_cell(i, IMDB_RATING_COL_NAME)
            cell_title = sheet.get_cell(i, TITLE_COL_NAME)
            cell_director = sheet.get_cell(i, DIRECTOR_COL_NAME)
            cell_fail = sheet.get_cell(i, FAIL_COL_NAME)

            slug = sheet.get_cell(i, "Slug")

            if cell_fail:
                continue

            if all((cell_genre, cell_imdb_r, cell_title, cell_director)):
                continue

            if not slug:
                print(f"Row is missing movie title row_num={i}", file=sys.stderr)
                continue

            try:
                movie = fetch_movie_meta(slug)
            except MovieNotFound as err:
                print(f"Whoops. Movie not found '{slug}'", file=sys.stderr)
                sheet.set_cell(i, FAIL_COL_NAME, 'x')
                continue

            if not cell_added:
                now = datetime.utcnow().replace(tzinfo=pytz.utc)
                now = now.astimezone(pytz.timezone("US/Pacific"))
                sheet.set_cell(i, ADDED_COL_NAME, now.strftime('%m/%d/%Y'))

            if not cell_genre:
                sheet.set_cell(i, GENRE_COL_NAME, movie["Genre"] or '?')
            if not cell_imdb_r:
                sheet.set_cell(i, IMDB_RATING_COL_NAME, movie["imdbRating"] or '?')
            if not cell_imdb_r:
                sheet.set_cell(i, TITLE_COL_NAME, f'{movie["Title"]} ({movie["Year"]})')
            if not cell_director:
                sheet.set_cell(i, DIRECTOR_COL_NAME, movie["Director"] or '?')

            row_update_count += 1


    print(f"Updated {row_update_count} rows", file=sys.stderr)



