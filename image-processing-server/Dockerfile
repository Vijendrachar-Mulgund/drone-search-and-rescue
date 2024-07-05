FROM python:3.12

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Run the command to install any necessary dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 9999 available to the world outside this container
EXPOSE 9999
EXPOSE 5000

# Run hello.py when the container launches
CMD ["python3", "app.py"]