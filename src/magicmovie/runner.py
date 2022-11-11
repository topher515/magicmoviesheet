import sys
import requests
from dotenv import load_dotenv
from pprint import pprint
from contextlib import contextmanager

load_dotenv()

from magicmovie.lib.movie_meta import fetch_movie_meta
from magicmovie.lib.spreadsheet import autosaving_sheet

# Sheet Col Names
GENRE_COL_NAME = "!Genre"
IMDB_RATING_COL_NAME = "!IMDB Rating"
TITLE_COL_NAME = "!Title"
DIRECTOR_COL_NAME = "!Director"


def main():

    movie_speadsheet_id = '1KLIddsNHuiHCzHTNN5bzRkGinHyRQUOg0fifd2RlRMo'


    with autosaving_sheet(movie_speadsheet_id) as sheet:

        row_update_count = 0
        for i in range(2, len(sheet)+1):

            cell_genre = sheet.get_cell(i, GENRE_COL_NAME)
            cell_imdb_r = sheet.get_cell(i, IMDB_RATING_COL_NAME)
            cell_title = sheet.get_cell(i, TITLE_COL_NAME)
            cell_director = sheet.get_cell(i, DIRECTOR_COL_NAME)

            slug = sheet.get_cell(i, "Slug")

            if all((cell_genre, cell_imdb_r, cell_title, cell_director)):
                continue

            if not slug:
                print(f"Row is missing movie title row_num={i}", file=sys.stderr)
                continue

            movie = fetch_movie_meta(slug)

            # import pdb; pdb.set_trace()

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



