# µSOCKS5

µSOCKS5 is a lightweight SOCKS5 proxy server written in Python that prioritizes resource efficiency.
Instead of creating a new thread for each connection, it iterates on each tuple of connections and checks for any pending data to forward, those data are then forwarded in chunks to avoid blocking the event loop and to allow other connections to be processed smoothly.

## How to Run

### Option 1: Docker

1. Make sure you have Docker installed on your system.
2. Build the Docker image by running the following command in the project directory:
    ```
    docker build -t usocks5 .
    ```
3. Run the Docker container using the following command:
    ```
    docker run -p 1080:1080 usocks5
    ```
    This will map the container's port 1080 to the host's port 1080.

### Option 2: Python Script

1. Make sure you have Python 3 installed on your system.
2. Open a terminal and navigate to the project directory.
3. Launch the proxy server by running the following command:
    ```
    python usocks5.py
    ```
    The proxy server will start listening on the standard port 1080.

## Usage

Once the uSOCKS5 proxy server is running, you can configure your applications or tools to use it as a SOCKS5 proxy. Set the proxy server address to `localhost` and the port to `1080`.

Please note that uSOCKS5 currently only supports TCP communications. UDP support may be added in future versions.