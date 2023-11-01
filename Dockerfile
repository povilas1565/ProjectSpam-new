FROM python:3.10.0-alpine

WORKDIR /app

COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt

RUN apt-get update && apt-get install\
    libgl1\
    libgl1-mesa-glx \ 
    libglib2.0-0 -y

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code to the container
COPY . /app/

# Define environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["python", "./bot.py"]