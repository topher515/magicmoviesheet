FROM python:3.9

WORKDIR /usr/src/app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install .

CMD [ "python", "bin/refresh_sheet.py" ]