# Kubernetes Deployment for Chat with PDF Application

This directory contains the Kubernetes manifests to deploy the "Chat with PDF" application.

## Prerequisites

1.  **Kubernetes Cluster:** You need access to a running Kubernetes cluster.
2.  **`kubectl` Configured:** Your `kubectl` command-line tool must be configured to communicate with your cluster.
3.  **Docker Images:** The Docker images for each service (`backend`, `worker`, `frontend`, `upload-service`) must be built and pushed to a container registry accessible by your Kubernetes cluster.

## Setup Instructions

### 1. Clone the Repository

If you haven't already, clone the repository containing these Kubernetes manifests.

### 2. Configure Image Names

In each of the deployment YAML files (`backend-deployment.yaml`, `worker-deployment.yaml`, `frontend-deployment.yaml`, `upload-service-deployment.yaml`), you need to update the image placeholder:

*   Find the line `image: YOUR_REGISTRY/chat-pdf-<service_name>:latest`
*   Replace `YOUR_REGISTRY` with the path to your container registry (e.g., `docker.io/yourusername`, `gcr.io/yourprojectid`, `youracr.azurecr.io`).

**Example (for `backend-deployment.yaml`):**
Change `image: YOUR_REGISTRY/chat-pdf-backend:latest`
To (e.g.): `image: docker.io/myuser/chat-pdf-backend:latest`

Do this for all `*-deployment.yaml` files.

### 3. Configure `configmap.yaml`

Edit `kubernetes/configmap.yaml`:

*   **`DATABASE_URL_PLACEHOLDER`**: Replace the placeholder value with the actual connection string for your **external** PostgreSQL database.
    *   Example: `postgresql://db_user:db_super_secret_password@my-external-db.example.com:5432/chatpdf_db`
*   **`CELERY_BROKER_URL_PLACEHOLDER`**: Replace the placeholder value with the actual connection string for your **external** Redis instance.
    *   Example: `redis://my-external-redis.example.com:6379/0`
*   **`UPLOAD_URL`**: This is pre-configured to `http://upload-service:8050`, which should work if the upload service is deployed within Kubernetes as defined by `upload-service-service.yaml`.

### 4. Create Kubernetes Secrets (`app-secrets`)

Secrets for the application (API keys, database credentials if not in DB URL, Flask secret key) must be created in the cluster. The `kubernetes/secret.yaml` file is a template.

**Values to Prepare:**

*   `OPENAI_API_KEY`: Your actual OpenAI API key.
*   `SECRET_KEY`: A long, random string for Flask's `SECRET_KEY`.
*   (Optional) `POSTGRES_USER` and `POSTGRES_PASSWORD`: If your `DATABASE_URL` in the ConfigMap does not include credentials, or if other parts of your setup need them separately. The current deployments primarily use `DATABASE_URL`.

**Method 1: Editing `secret.yaml` (Recommended for clarity)**

1.  For each key in `kubernetes/secret.yaml` (e.g., `OPENAI_API_KEY_PLACEHOLDER`, `SECRET_KEY_PLACEHOLDER`), you need to provide its **base64 encoded** value.
2.  To base64 encode a value, use the following command:
    ```bash
    echo -n 'your_actual_value_here' | base64
    ```
    *   **Example for OpenAI API Key:** `echo -n 'sk-xxxxxxxxxxxxxxxxx' | base64` will output something like `c2steHh4eHh4eHh4eHh4eHh4eHg==`.
    *   **Example for Flask Secret Key:** `echo -n 'a_very_strong_and_random_secret_123!@#' | base64`
3.  Replace the placeholder base64 strings in `secret.yaml` with your generated ones. For instance, for `OPENAI_API_KEY_PLACEHOLDER:`, replace `eW91ci1vcGVuYWktYXBpLWtleQ==` with your actual base64 encoded OpenAI key.
4.  Apply the secret:
    ```bash
    kubectl apply -f kubernetes/secret.yaml
    ```

**Method 2: Using `kubectl create secret`**

You can create the secret directly without editing the YAML file. Ensure the `--from-literal` keys match what the deployments expect (e.g., `OPENAI_API_KEY_PLACEHOLDER`).

```bash
kubectl create secret generic app-secrets \
  --from-literal=OPENAI_API_KEY_PLACEHOLDER='your_actual_openai_api_key' \
  --from-literal=SECRET_KEY_PLACEHOLDER='your_actual_flask_secret_key'
  # Add other secrets like POSTGRES_USER_PLACEHOLDER if needed, matching the keys in deployment YAMLs
```
*Note: `kubectl create secret` handles base64 encoding automatically for `--from-literal`.*

The deployment YAMLs are configured to use keys like `OPENAI_API_KEY_PLACEHOLDER`. If you change these key names in your Secret object (e.g., to just `OPENAI_API_KEY`), you must also update the `secretKeyRef.key` fields in the deployment YAMLs accordingly.

### 5. Deploy the Application

Once the configurations and secrets are in place, apply all the manifests:

```bash
kubectl apply -f kubernetes/
```
This command will create all the deployments, services, and the configmap (the secret should already be created).

### 6. Initialize the Database

After the `backend` pods are running, you need to initialize the database schema:

1.  Find the name of one of your backend pods:
    ```bash
    kubectl get pods -l app=chat-pdf,service=backend
    ```
    This will list pods, e.g., `backend-deployment-xxxxxxxxxx-yyyyy`.
2.  Execute the `init-db` command in the backend pod (replace `<backend-pod-name>` with the actual pod name):
    ```bash
    kubectl exec -it <backend-pod-name> -- flask init-db
    ```

### 7. Accessing the Application

*   **Frontend:** The `frontend-service.yaml` is configured as `type: LoadBalancer`. Kubernetes will attempt to provision an external IP address for it from your cloud provider.
    Find the external IP:
    ```bash
    kubectl get service frontend
    ```
    Look for the `EXTERNAL-IP` value. It might take a few minutes to appear. Once available, you can access the application at `http://<EXTERNAL-IP>`.
    If you are running on a local cluster (like Minikube or Kind), you might need to use `minikube service frontend --url` or `kubectl port-forward svc/frontend 8080:80` and access via `http://localhost:8080`.

*   **Backend/Upload Service:** These are exposed as `ClusterIP` services and are typically not directly accessible from outside the cluster, except through the frontend or an Ingress controller (not included in this basic setup).

## Important Notes

*   **Persistence for Upload Service:** The `upload-service-deployment.yaml` uses an `emptyDir` volume for `/app/uploads`. This means uploaded files are **ephemeral** and will be lost if the pod restarts. For production, you should configure a `PersistentVolume` and `PersistentVolumeClaim` and update the deployment to use it.
*   **Database and Redis:** This setup assumes you are using externally managed PostgreSQL and Redis services. For a production Kubernetes deployment, consider using managed database/Redis services from your cloud provider or deploying them as `StatefulSets` with appropriate persistent storage.
*   **Image Tags:** Using `:latest` tag for images is convenient for development but not recommended for production. Use specific, immutable image tags (e.g., Git commit SHA or semantic version) for reliable rollbacks and consistent deployments.
*   **Resource Requests and Limits:** The provided deployment YAMLs do not specify CPU/memory requests and limits. For production, these should be configured based on application needs to ensure stable performance and resource utilization.
*   **Ingress:** For more advanced routing, SSL termination, and path-based routing to services, an Ingress controller and Ingress resources should be set up. This is not part of these basic manifests.

## Cleaning Up

To delete all the resources created by these manifests:
```bash
kubectl delete -f kubernetes/
# Don't forget to delete the secret if you created it separately
kubectl delete secret app-secrets
```
