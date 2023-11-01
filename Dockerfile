FROM python:3.10.0-alpine

WORKDIR /app

COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt

RUN apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code to the container
COPY . /app/

# Define environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["python", "./bot.py"]