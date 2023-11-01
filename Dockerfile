FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt

RUN apt-get update -y

RUN apt-get install libglib2.0-0

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code to the container
COPY . /app/

# Define environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["python", "./bot.py"]