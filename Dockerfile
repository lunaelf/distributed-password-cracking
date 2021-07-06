FROM rayproject/ray:1.3.0-py38

# Install Flask
RUN pip install Flask

WORKDIR /app
# COPY requirements.txt ./
# RUN pip install -r requirements.txt
COPY . .

# Set enviroment variables
ENV FLASK_APP=cracking
ENV FLASK_ENV=development
ENV PYTHONPATH=${PYTHONPATH}:/app/cracking
