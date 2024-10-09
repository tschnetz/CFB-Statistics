# Log in to the Google Cloud Console: https://console.cloud.google.com/.
  #	2.	Create a new project:
  #	•	Go to the project selector and click New Project.
  #	•	Give your project a name and note down the project ID.
# Create a Dockerfile in the root of your project directory
docker build --platform linux/amd64 -t streamlit-app .
# gcloud auth login
gcloud config set project cfb-data-2024
gcloud builds submit --tag gcr.io/cfb-data-2024/streamlit-app
gcloud run deploy streamlit-app --image gcr.io/cfb-data-2024/streamlit-app --platform managed --region us-east1 --allow-unauthenticated