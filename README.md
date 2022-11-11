# Magic Movie Sheet

Automatically populate movie Google Spreadsheet with IMDB data

## Testing

Run `pip install --editable .` before running `pytest`

## Docker

### Build

- Run `./build.sh` > 

### Run

- Run `docker run -ti --rm --env-file=.env ghcr.io/topher515/magicmoviesheet:latest`