# Chat with PDF Document

## Table of Contents

1.  [Overview](#overview)
2.  [System Architecture](#system-architecture)
    *   [Overall Application Architecture](#overall-application-architecture)
    *   [Docker Compose Service Interaction](#docker-compose-service-interaction)
    *   [Kubernetes Deployment Overview](#kubernetes-deployment-overview)
3.  [System Requirements](#system-requirements)
4.  [Configuration](#configuration)
5.  [Running the Application with Docker Compose (Recommended)](#running-the-application-with-docker-compose-recommended)
    *   [Prerequisites (Docker)](#prerequisites-docker)
    *   [Setup Steps (Docker)](#setup-steps-docker)
    *   [Common Docker Compose Commands](#common-docker-compose-commands)
6.  [Testing](#testing)
    *   [Unit Tests](#unit-tests)
    *   [Integration Tests](#integration-tests)
7.  [Deploying to Kubernetes](#deploying-to-kubernetes)
8.  [Manual Installation and Usage](#manual-installation-and-usage)
    *   [Prerequisites (Manual)](#prerequisites-manual)
    *   [Installation (Manual)](#installation-manual)
    *   [Running the Application Manually](#running-the-application-manually)
9.  [Usage](#usage)
10. [Maintenance and Resetting](#maintenance-and-resetting)
    *   [Stopping the Application](#stopping-the-application)
    *   [Resetting the Database](#resetting-the-database)

## Overview

This platform provides a robust solution for uploading and interacting with PDF documents. It leverages the capabilities of LangChain and OpenAI APIs to offer an enhanced chat-based user experience. This documentation will guide you through the setup and usage of the platform.

## System Architecture

This section outlines the main components of the application and how they interact.

### Overall Application Architecture

This diagram shows the high-level components and data flow:

```mermaid
graph TD
    User[End User] -->|HTTPS| Frontend[Frontend (SvelteKit + Nginx)]
    Frontend -->|HTTP API Calls (/api)| Backend[Backend API (Flask + Gunicorn)]
    Backend -->|SQLAlchemy ORM| Database[(PostgreSQL)]
    Backend -->|Task Queue (Celery)| Redis[Redis (Celery Broker)]
    Backend -->|HTTP API Calls| UploadService[Upload Service (Flask + Gunicorn)]
    
    CeleryWorker[Celery Worker] --|>| Redis
    CeleryWorker -->|SQLAlchemy ORM| Database
    
    Backend -->|External API| OpenAI_API[(OpenAI API)]
    CeleryWorker -->|External API| OpenAI_API

    subgraph "User's Browser"
        User
    end

    subgraph "Application Infrastructure (Docker/Kubernetes)"
        Frontend
        Backend
        Database
        Redis
        UploadService
        CeleryWorker
    end
    
    subgraph "External Services"
        OpenAI_API
    end
```

**Components:**
*   **Frontend:** A SvelteKit application served by Nginx, providing the user interface.
*   **Backend API:** A Flask application (using Gunicorn) that handles business logic, API requests, user authentication, and orchestrates tasks.
*   **Upload Service:** A separate Flask application dedicated to handling file uploads.
*   **Celery Worker:** A background worker process that consumes tasks from a queue (e.g., PDF processing, AI computations).
*   **Database (PostgreSQL):** Stores persistent data like user information, PDF metadata, conversation history, etc.
*   **Redis:** Acts as a message broker for Celery (task queue) and can also be used for caching.
*   **OpenAI API:** External service used for language model interactions.

### Docker Compose Service Interaction

This diagram illustrates how the services defined in `docker-compose.yml` interact within the Docker environment:

```mermaid
graph TD
    User[User via Browser] -->|HTTP Port ${FRONTEND_PORT:-3000}| FrontendService[frontend (Nginx)]
    
    subgraph "Docker Network (e.g., 'chat-pdf_default')"
        FrontendService -->|/api proxy to http://backend:8000| BackendService[backend (Gunicorn)]
        BackendService -->|DATABASE_URL via internal DNS 'db'| DBService[db (PostgreSQL)]
        BackendService -->|CELERY_BROKER_URL via internal DNS 'redis'| RedisService[redis]
        BackendService -->|UPLOAD_URL to http://upload_service:8050 via internal DNS 'upload_service'| UploadSvcContainer[upload_service (Gunicorn)]
        
        WorkerService[worker (Celery)] -->|DATABASE_URL via internal DNS 'db'| DBService
        WorkerService -->|CELERY_BROKER_URL via internal DNS 'redis'| RedisService
        
        UploadSvcContainer -.->|Volume: persisted_uploads| UploadsVolume[(persisted_uploads)]
        DBService -.->|Volume: postgres_data| DBVolume[(postgres_data)]
    end

    User -->|Direct access if host port mapped, e.g., Port ${POSTGRES_PORT:-5432}| DBService
    User -->|Direct access if host port mapped, e.g., Port ${REDIS_PORT:-6379}| RedisService
```
*   Services within the Docker network communicate using their service names as hostnames (e.g., `backend` can reach `db` at `db:5432`).
*   The frontend's Nginx proxies API calls to the `backend` service.
*   Persistent data for PostgreSQL and uploads are managed using Docker volumes.

### Kubernetes Deployment Overview

This provides a simplified view of the Kubernetes deployment. For detailed information, please refer to the [Kubernetes Deployment Guide](./kubernetes/README.md).

```mermaid
graph TD
    User[End User] -->|HTTPS via Cloud LoadBalancer| K8S_FrontendService[Service: frontend (LoadBalancer)]
    K8S_FrontendService --> K8S_FrontendDeployment[Deployment: frontend (Nginx Pods)]
    
    K8S_FrontendDeployment -->|HTTP via ClusterIP (e.g., backend.default.svc.cluster.local)| K8S_BackendService[Service: backend (ClusterIP)]
    K8S_BackendService --> K8S_BackendDeployment[Deployment: backend (Flask Pods)]
    
    K8S_BackendDeployment -->|Env Vars from| K8S_AppConfig[ConfigMap: app-config]
    K8S_BackendDeployment -->|Env Vars from| K8S_AppSecrets[Secret: app-secrets]
    K8S_BackendDeployment -->|Network Call to External Service| K8S_ExternalDB[(External PostgreSQL)]
    K8S_BackendDeployment -->|Network Call to External Service| K8S_ExternalRedis[(External Redis)]
    K8S_BackendDeployment -->|HTTP via ClusterIP (e.g., upload-service.default.svc.cluster.local)| K8S_UploadServiceService[Service: upload-service (ClusterIP)]
    
    K8S_UploadServiceService --> K8S_UploadServiceDeployment[Deployment: upload-service (Flask Pods)]
    K8S_UploadServiceDeployment -.->|Volume (e.g., emptyDir or PVC)| K8S_UploadsVolume[(Uploads Volume)]
        
    K8S_WorkerDeployment[Deployment: worker (Celery Pods)] -->|Env Vars from| K8S_AppConfig
    K8S_WorkerDeployment -->|Env Vars from| K8S_AppSecrets
    K8S_WorkerDeployment -->|Network Call to External Service| K8S_ExternalDB
    K8S_WorkerDeployment -->|Network Call to External Service| K8S_ExternalRedis
```
*   Kubernetes Services (LoadBalancer, ClusterIP) manage network access to Pods.
*   Deployments manage Pod replicas and updates.
*   Configuration is externalized using ConfigMaps and Secrets.
*   Persistent storage for uploads would ideally use PersistentVolumeClaims (PVCs) in a production setup. The current basic setup uses `emptyDir` which is ephemeral.
*   This diagram assumes external PostgreSQL and Redis, as per the basic Kubernetes manifests provided.

## System Requirements

*   **For Docker Compose (Recommended):**
    *   Docker Engine (latest version recommended)
    *   Docker Compose (latest version recommended)
*   **For Manual Installation:**
    *   Python (3.9+ recommended)
    *   Access to a PostgreSQL database and a Redis instance.
*   **For Kubernetes Deployment:**
    *   See details in the [Kubernetes Deployment Guide](./kubernetes/README.md).
*   **Operating System:** The application has been tested on macOS, Windows (with WSL2 for Docker/manual setup), and Linux.

## Configuration

Key application settings are managed via environment variables. A template for these variables is provided in the `.env.example` file. When using Docker Compose, create a `.env` file (by copying `.env.example`) in the project root, and Docker Compose will automatically load it. For Kubernetes deployments, these configurations are managed through ConfigMaps and Secrets.

**Essential Variables (from `.env.example`):**

*   `OPENAI_API_KEY`: **Required.** Your API key for accessing OpenAI services.
*   `SECRET_KEY`: **Required for production.** A strong, random string used by Flask for session management and cryptographic signing. The default value in `app/web/config/__init__.py` is for development only and **must** be overridden for production.
*   `POSTGRES_USER`: Username for the PostgreSQL database. Default: `user`.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL database. Default: `password`.
*   `POSTGRES_DB`: Name of the PostgreSQL database. Default: `appdb`.

**Docker Compose Specific Variables (defaults usually fine):**

*   `DATABASE_URL`: Full connection string for PostgreSQL. In Docker Compose, this is automatically constructed using the `POSTGRES_` variables and the `db` service name (e.g., `postgresql://user:password@db:5432/appdb`).
*   `CELERY_BROKER_URL`: Connection string for Redis, used as the Celery message broker. In Docker Compose, this defaults to `redis://redis:6379/0`, pointing to the `redis` service.
*   `UPLOAD_URL`: URL that the backend uses to communicate with the upload service. In Docker Compose, this defaults to `http://upload_service:8050`.

**Optional Port Mappings for Docker Compose (Host machine ports):**

These variables in `.env` allow you to change which ports on your host machine map to the services running inside Docker. The defaults are generally fine unless they conflict with other applications.

*   `BACKEND_PORT`: Host port for the backend API service. Default: `8000`.
*   `FRONTEND_PORT`: Host port for the frontend web interface. Default: `3000`.
*   `UPLOAD_SERVICE_PORT`: Host port for the upload service. Default: `8050`.
*   `POSTGRES_PORT`: Host port to expose the PostgreSQL database externally (e.g., for direct database access). Default: `5432`.
*   `REDIS_PORT`: Host port to expose Redis externally. Default: `6379`.

For Kubernetes, configuration is handled differently. Refer to `kubernetes/configmap.yaml` and `kubernetes/secret.yaml` for how these are structured, and the `kubernetes/README.md` for instructions on applying them.

## Running the Application with Docker Compose (Recommended)

Docker Compose simplifies the setup and execution of multi-container Docker applications. It allows you to define and run all services (backend, frontend, database, etc.) with a single command, ensuring a consistent environment.

### Prerequisites (Docker)

*   Ensure Docker Engine and Docker Compose are installed on your system. Visit the official Docker website for installation instructions.

### Setup Steps (Docker)

1.  **Clone the Repository:**
    If you haven't already, clone the project repository to your local machine.
    ```bash
    git clone <your_repository_url>
    cd <repository_directory_name>
    ```

2.  **Create and Configure `.env` File:**
    The application uses environment variables for configuration. A template `.env.example` is provided. Copy it to a new file named `.env`:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and edit the values. **Crucially, you must provide your `OPENAI_API_KEY`.** You may also want to review:
    *   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: For the local PostgreSQL instance managed by Docker Compose.
    *   `SECRET_KEY`: For Flask session security. A strong, random key is recommended.
    *   Port mappings (`FRONTEND_PORT`, `BACKEND_PORT`, etc.) if the defaults conflict with other services on your machine.

3.  **Build and Start Containers:**
    This command will build the Docker images for each service (if they don't exist or if their Dockerfiles have changed) and then start all services in detached mode (`-d`).
    ```bash
    docker-compose up --build -d
    ```
    *(You can run `docker-compose build` separately before `docker-compose up -d` if you prefer to build images first.)*

4.  **Initialize Database (First time only):**
    Once the containers are running (especially the `db` and `backend` services), you need to initialize the database schema. This is a one-time step for the initial setup or if you want to completely reset the database.
    ```bash
    docker-compose exec backend flask init-db
    ```
    *Note: The `backend` service's health check specified in `docker-compose.yml` might fail or indicate unhealthiness until the database is initialized. It's good practice to wait a minute for services to stabilize before running this command, or re-run it if it fails the first time due to service startup race conditions.*

5.  **Accessing the Application:**
    Once all services are running and the database is initialized, you can access the application:
    *   **Frontend:** `http://localhost:${FRONTEND_PORT:-3000}` (e.g., `http://localhost:3000` if using the default port)
    *   **Backend API:** `http://localhost:${BACKEND_PORT:-8000}` (e.g., `http://localhost:8000`)
    *   **Upload Service API:** `http://localhost:${UPLOAD_SERVICE_PORT:-8050}` (e.g., `http://localhost:8050`)

### Common Docker Compose Commands

*   **Stopping Services:**
    To stop all running services defined in `docker-compose.yml`:
    ```bash
    docker-compose down
    ```

*   **Stopping Services and Removing Volumes:**
    If you want to stop services AND remove the data volumes (e.g., to reset the PostgreSQL database completely):
    ```bash
    docker-compose down -v
    ```
    *Caution: This will delete all data in your Docker-managed database.*

*   **Viewing Logs:**
    To view logs from all running services in real-time:
    ```bash
    docker-compose logs -f
    ```
    To view logs for a specific service (e.g., `backend`):
    ```bash
    docker-compose logs -f backend
    ```

*   **Rebuilding a Specific Service:**
    If you've made changes to the source code or Dockerfile of a specific service and need to rebuild its image:
    ```bash
    docker-compose build <service_name>
    # Example: docker-compose build backend
    ```
    After rebuilding, you can restart the specific service and its dependencies:
    ```bash
    docker-compose up -d --no-deps <service_name>
    # Example: docker-compose up -d --no-deps backend
    # To restart all services and apply changes:
    # docker-compose up -d 
    ```

*   **Executing Commands in a Running Container:**
    You can run commands inside a running container (e.g., a shell for debugging):
    ```bash
    docker-compose exec <service_name> <command>
    # Example: docker-compose exec backend bash
    ```

## Deploying to Kubernetes
(To be filled in with a link to kubernetes/README.md)

For deploying the application to a Kubernetes cluster, which provides orchestration, scalability, and resilience, please refer to the detailed instructions and manifests provided in the Kubernetes specific README:

➡️ **[Kubernetes Deployment Guide](./kubernetes/README.md)**

**Key Prerequisites (covered in the guide):**
*   Access to a Kubernetes cluster.
*   `kubectl` command-line tool configured to interact with your cluster.
*   Docker images for all application services (`backend`, `frontend`, `worker`, `upload-service`) must be built and pushed to a container registry that your Kubernetes cluster can access.

The Kubernetes setup assumes that the database (PostgreSQL) and Redis are running as external services, and their connection details are provided via Kubernetes ConfigMaps and Secrets.

## Manual Installation and Usage

This section describes setting up the application directly on your machine without Docker. This is more complex and less recommended than using Docker Compose due to the need to manage services like PostgreSQL and Redis manually.

### Prerequisites (Manual)

*   Python (3.9+ recommended).
*   A running PostgreSQL server.
*   A running Redis server.
*   Node.js and npm (for building and running the SvelteKit frontend).

### Installation (Manual)

1.  **Clone the Repository:**
    ```bash
    git clone <your_repository_url> # Replace <your_repository_url> with the actual URL
    cd <repository_directory_name> # Replace <repository_directory_name> with the cloned directory name
    ```

2.  **Backend & Worker Setup (Python):**
    *   **Create and Activate Virtual Environment:**
        ```bash
        # From the project root
        python -m venv .venv
        source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
        ```
    *   **Install Python Dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    *   **Configure Environment Variables:**
        You must set environment variables for your system to tell the Flask application how to connect to your manually managed PostgreSQL and Redis, and your OpenAI API key. This can be done by setting them in your shell, or by creating a `.env` file in the project root (ensure `python-dotenv` is used by the application; it's in `requirements.txt` and loaded by `app/web/config/__init__.py`).
        Key variables to set:
        *   `OPENAI_API_KEY=your_openai_api_key`
        *   `SECRET_KEY=your_strong_flask_secret_key` (Refer to `app/web/config/__init__.py` for its usage)
        *   `SQLALCHEMY_DATABASE_URI=postgresql://your_user:your_password@your_host:your_port/your_db_name`
        *   `REDIS_URI=redis://your_redis_host:your_redis_port/0` (for Celery broker, used as `CELERY.broker_url` in `app/web/config/__init__.py`)
        *   `UPLOAD_URL=http://localhost:8050` (if running upload service manually on default port, used by backend)

    *   **Initialize Database:**
        Ensure your `SQLALCHEMY_DATABASE_URI` environment variable is correctly configured. Then, run:
        ```bash
        flask --app app.web init-db
        ```

3.  **Frontend Setup (SvelteKit):**
    *   Navigate to the client directory:
        ```bash
        cd client
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```
    *   *(Frontend development typically runs on its own dev server; see running instructions below).*

4.  **Upload Service Setup (Python):**
    *   The upload service is a separate Flask app. It can share the same Python virtual environment if you run it from the project root context.
    *   **Configure Environment Variables (if needed, or rely on defaults in `upload/app.py`):**
        *   `UPLOAD_FOLDER=uploads` (default, ensure this directory exists or the app can create it)
        *   `UPLOAD_SERVICE_PORT=8050` (default port for Flask dev server)
        *   `FLASK_DEBUG=True` (for development mode)

### Running the Application Manually

All components (Backend API, Celery Worker, Redis, PostgreSQL, Frontend dev server, Upload service) must be running. Ensure your PostgreSQL and Redis servers are started first according to their respective documentation.

1.  **Start PostgreSQL Server:** (Refer to your PostgreSQL installation guide).
2.  **Start Redis Server:** (e.g., `redis-server` if installed locally and in PATH).

3.  **Start the Backend API Server (Flask/Gunicorn):**
    From the project root, with the Python virtual environment activated, in a new terminal:
    ```bash
    # For development (Flask dev server, ensure FLASK_APP=app.web.wsgi:app is set or implied):
    FLASK_APP=app.web.wsgi:app flask run --port ${BACKEND_PORT:-8000} --host 0.0.0.0
    # Or for a more production-like setup with Gunicorn:
    # gunicorn -b 0.0.0.0:${BACKEND_PORT:-8000} app.web.wsgi:app
    ```

4.  **Start the Celery Worker:**
    From the project root, with the Python virtual environment activated, in a new terminal:
    ```bash
    celery -A app.celery.worker.celery_app worker -l info
    ```

5.  **Start the Frontend Development Server (SvelteKit):**
    From the `client/` directory, in a new terminal:
    ```bash
    npm run dev
    ```
    This usually starts the frontend on `http://localhost:5173` or a similar port. The `vite.config.ts` proxy for `/api` should be configured to point to your manually running backend (e.g., `http://localhost:8000` by default).

6.  **Start the Upload Service:**
    From the `upload/` directory (or project root, ensuring Python can find `upload.app`), with the Python virtual environment activated, in a new terminal:
    ```bash
    # For development (Flask dev server, ensure FLASK_APP=app:app or run python -m flask):
    FLASK_APP=upload.app python -m flask run --port ${UPLOAD_SERVICE_PORT:-8050} --host 0.0.0.0
    # Or for a more production-like setup with Gunicorn:
    # gunicorn -b 0.0.0.0:${UPLOAD_SERVICE_PORT:-8050} app:app
    ```
    *(The `inv dev`, `inv devworker` commands mentioned in older versions of this README were custom Invoke tasks; direct Flask/Celery commands are shown here for clarity).*

## Usage

Once all application components are running (either via Docker Compose or manually), the platform is ready for use. Access the frontend URL in your web browser (e.g., `http://localhost:3000` for default Docker Compose setup, or the SvelteKit dev server URL for manual setup). Users can then upload PDF documents, view them, and interact with them through a chat interface that leverages the configured AI models.

## Maintenance and Resetting

### Stopping the Application

*   **Docker Compose:**
    ```bash
    docker-compose down
    ```
*   **Manual Setup:** Stop each process individually using `Control-C` in their respective terminal windows. Don't forget to stop the manually managed PostgreSQL and Redis servers if you started them specifically for this application.

### Resetting the Database

*   **Docker Compose:**
    To reset the database when using Docker Compose, you stop the services and remove the Docker volume used by PostgreSQL. This permanently deletes the database data.
    ```bash
    docker-compose down -v 
    # Then, restart the services:
    docker-compose up --build -d
    # And re-initialize the database schema:
    docker-compose exec backend flask init-db
    ```
    *Caution: `docker-compose down -v` removes ALL named volumes defined in the compose file if they are not marked as external (e.g., `postgres_data`, `persisted_uploads`).*

*   **Manual Setup:**
    Ensure your `SQLALCHEMY_DATABASE_URI` environment variable is correctly pointing to your database.
    ```bash
    # Ensure virtual environment is active and you are in the project root
    flask --app app.web init-db
    ```
    This command will drop all tables and recreate them. It assumes you have direct access to the database and the necessary privileges. *Caution: This will delete all data in the specified database.*

## Testing

This project includes both unit tests and integration tests.

### Unit Tests

Unit tests are designed to test individual components or functions in isolation, without relying on external services like databases or running Docker containers. They are located in `app/tests/` and `upload/tests/`.

**Prerequisites:**
*   Ensure your Python virtual environment is activated.
*   All development dependencies (including `pytest`) are installed from `requirements.txt`.
    ```bash
    pip install -r requirements.txt 
    ```

**Running Unit Tests:**
To run all unit tests, execute the following command from the root of the project:
```bash
pytest app/tests upload/tests
```
Or, more simply, if your `pytest` is configured for auto-discovery (which is typical):
```bash
pytest
```
(Pytest should auto-discover tests in these directories if they follow naming conventions like `test_*.py` or `*_test.py`. If you have a `pytest.ini` or `pyproject.toml` file, it might also control discovery.)

### Integration Tests

Integration tests are designed to verify that different parts of the application work together correctly. These tests **require the Docker Compose environment to be fully up and running** because they make live HTTP requests to the services. They are located in the `tests_integration/` directory.

**Prerequisites:**
*   Docker and Docker Compose must be installed and running.
*   The application services must be running via Docker Compose. Start them with:
    ```bash
    docker-compose up -d
    ```
*   The database must be initialized. If this is the first time or you've cleared data, run:
    ```bash
    docker-compose exec backend flask init-db
    ```
    *(Ensure all services like `backend`, `upload_service`, `frontend`, `db`, `redis` are healthy. You can check with `docker-compose ps`.)*
*   Ensure your Python virtual environment is activated (for running `pytest` locally against the Dockerized services).
*   All development dependencies (including `pytest` and `requests`) are installed from `requirements.txt`.
*   Environment variables for service ports (`BACKEND_PORT`, `UPLOAD_SERVICE_PORT`, `FRONTEND_PORT` in your shell or `.env` file) should match your Docker Compose setup if you've customized them. The tests use defaults (8000, 8050, 3000) if these are not set in the environment where `pytest` is run.

**Running Integration Tests:**
To run the integration tests, execute the following command from the root of the project:
```bash
pytest tests_integration/test_docker_services.py
```
Or, for pytest to discover all tests within that directory:
```bash
pytest tests_integration
```

**Important Notes for Integration Tests:**
*   The tests target `http://localhost` using the respective service ports defined in `tests_integration/test_docker_services.py` (which default to those in `.env.example`). Ensure these are accessible from the environment where you run `pytest`.
*   If tests fail due to connection issues, double-check that:
    *   The Docker containers are running and healthy (`docker-compose ps`).
    *   Ports are correctly mapped and exposed (check `docker-compose.yml` and your `.env` file).
    *   There are no firewall issues blocking localhost connections to these ports.
*   The `test_list_conversations_empty` test in `tests_integration/test_docker_services.py` is currently skipped as it requires authentication setup, which is beyond the scope of these basic integration tests.