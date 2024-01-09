# Chat with PDF Document

## Overview

This platform provides a robust solution for uploading and interacting with PDF documents. It leverages the capabilities of LangChain and OpenAI APIs to offer an enhanced chat-based user experience. This documentation will guide you through the setup and usage of the platform.

## System Requirements

Before proceeding, ensure you have Python installed on your system. This platform has been tested on MacOS, Windows, Linux, and WSL environments.

## Installation

1. **Creating a Virtual Environment**:
   To avoid any conflicts with existing Python packages, it's recommended to use a virtual environment. Run the following commands based on your operating system:

   - **MacOS/WSL/Linux**:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

   - **Windows**:
     ```bash
     python -m venv .venv
     .\.venv\Scripts\activate
     ```

2. **Install Dependencies**:
   With the virtual environment activated, install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   The platform uses a database to manage PDF documents and user interactions. Initialize it using:
   ```bash
   flask --app app.web init-db
   ```

## Running the Application

The application consists of three main components: the server, a worker, and Redis. Each of these needs to be running simultaneously in separate terminal windows.

1. **Running the Python Server**:
   Start the server to handle web requests:
   ```bash
   inv dev
   ```

2. **Running the Worker**:
   This worker process handles background tasks and processing:
   ```bash
   inv devworker
   ```

3. **Running Redis**:
   Redis is used for managing state and caching:
   ```bash
   redis-server
   ```

## Usage

Once all processes are running, the platform is ready for use. Users can upload, view, and interact with PDF documents through a chat interface, leveraging advanced natural language processing technologies.

## Maintenance

- **Stopping the Processes**: To stop any of the running components (server, worker, or Redis), select the corresponding terminal window and press `Control-C`.
- **Resetting the Database**: If you need to reset the database to its initial state, use the following command:
  ```bash
  flask --app app.web init-db
  ```