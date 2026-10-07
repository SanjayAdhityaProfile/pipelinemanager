# Base image
FROM python:3.11.5

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 unixodbc unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y python3-dev default-libmysqlclient-dev build-essential
 
# Install Microsoft ODBC drivers (both 17 and 18)
RUN apt-get update && \
    apt-get install -y unixodbc unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    echo "deb [arch=amd64,arm64,armhf] https://packages.microsoft.com/debian/12/prod bookworm main" | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 msodbcsql17 && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin:/opt/mssql-tools17/bin"' >> ~/.bashrc && \
    rm -rf /var/lib/apt/lists/*


# Set working directory in the container
WORKDIR /app

# Copy only requirements to leverage caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port FastAPI runs on
EXPOSE 5000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
