import sys
from typing import Optional
import requests
import os
from urllib.parse import urlparse
from typing import TypedDict


class MovieNotFound(BaseException):
    pass

# Example
# {
#   "Title": "The Cabinet of Dr Caligari",
#   "Year": "1948",
#   "Rated": "N/A",
#   "Released": "05 Jul 1948",
#   "Runtime": "5 min",
#   "Genre": "Short, Family",
#   "Director": "N/A",
#   "Writer": "Roger Manvell",
#   "Actors": "Roger Manvell",
#   "Plot": "N/A",
#   "Language": "English",
#   "Country": "United Kingdom",
#   "Awards": "N/A",
#   "Poster": "https://m.media-amazon.com/images/M/MV5BZmEzYzlmMmYtYTI2Mi00OWY1LWI2MjQtMjZmM2M3ODNmMWZlXkEyXkFqcGdeQXVyMjk1ODk3NzE@._V1_SX300.jpg",
#   "Ratings": [
#     {
#       "Source": "Internet Movie Database",
#       "Value": "9.2/10"
#     }
#   ],
#   "Metascore": "N/A",
#   "imdbRating": "9.2",
#   "imdbVotes": "8",
#   "imdbID": "tt5444282",
#   "Type": "movie",
#   "DVD": "N/A",
#   "BoxOffice": "N/A",
#   "Production": "N/A",
#   "Website": "N/A",
#   "Response": "True"
# }

class MovieMeta(TypedDict):

    Title: str
    Year: str
    Director: str
    Genre: str
    Poster: str
    imdbId: str
    imdbRating: str



def noneify_n_a(val: str) -> Optional[str]:
    if val == 'N/A':
        return None
    return val

def fetch_movie_meta_moviedb(movie_descriptor: str) -> MovieMeta:

    interesting_fields = [x for x in MovieMeta.__annotations__]

    url = "https://moviesdb5.p.rapidapi.com/om"


    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "moviesdb5.p.rapidapi.com"
    }

    print(f"Fetching movie with slug '{movie_descriptor}'", file=sys.stderr)
    querystring = {"t": movie_descriptor}
    resp = requests.get(url, headers=headers, params=querystring)
    resp.raise_for_status()
    movie = resp.json()
    return {
       k: (noneify_n_a(movie[k]) if k in movie else None) for k in interesting_fields
    }
    

def fetch_movie_imdb_id(movie_descriptor: str):
    print(f"Searching for imdb movie '{movie_descriptor}'", file=sys.stderr)

    url = "https://bing-web-search1.p.rapidapi.com/search"

    querystring = {"q":f"site:imdb.com {movie_descriptor}","mkt":"en-us","safeSearch":"Off"}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Key": "tayrtv8lanfaywe68wdwr35cqq7j4r",
        "X-RapidAPI-Host": "bing-web-search1.p.rapidapi.com"
    }

    resp = requests.request("GET", url, headers=headers, params=querystring)
    if resp.status_code == 404:
        raise MovieNotFound(movie_descriptor)

    resp.raise_for_status()

    for webpage in resp.json()["webPages"]["value"]:

        parsed = urlparse(webpage["url"])
        if 'imdb.com' not in parsed.hostname:
            continue
        _, imdb_id = parsed.path.split('/title/')
        imdb_id = imdb_id.strip('/').strip()
        return imdb_id

    raise MovieNotFound(movie_descriptor)


def fetch_movie_meta_via_movie_details(imdb_id: str) -> MovieMeta:
    print(f"Fetching movie details '{imdb_id}'", file=sys.stderr)
    url = "https://movie-details1.p.rapidapi.com/imdb_api/movie"

    querystring = {"id":imdb_id}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "movie-details1.p.rapidapi.com"
    }

    resp = requests.request("GET", url, headers=headers, params=querystring)

    resp.raise_for_status()
    data = resp.json()

    return MovieMeta(
        Title=data["title"],
        Year=data["release_year"],
        Genre=", ".join(data["genres"][:2]),
        Director=data["director_names"][0],
        imdbId=data["id"],
        imdbRating=data["rating"],
        Poster=data["image"]

    )


def fetch_movie_meta_bing_imdb(movie_descriptor: str):

    imdb_id = fetch_movie_imdb_id(movie_descriptor)
    return fetch_movie_meta_via_movie_details(imdb_id)


def fetch_movie_meta(movie_descriptor: str):
    return fetch_movie_meta_bing_imdb(movie_descriptor)