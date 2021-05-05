FROM rayproject/ray:1.3.0-py38
WORKDIR /app
# COPY requirements.txt ./
# RUN pip install -r requirements.txt
RUN pip install Flask
ENV FLASK_APP=cracking
ENV FLASK_ENV=development
COPY . .
ENV PYTHONPATH=/app/cracking
# CMD [ "flask", "run", "--host=0.0.0.0" ]
CMD sh -c "ray start --head --port=6379 --dashboard-host=0.0.0.0 && flask run --host=0.0.0.0"
