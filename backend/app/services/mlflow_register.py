import mlflow
import mlflow.sklearn

def register_model(model, name="forex_scalper"):
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    with mlflow.start_run():
        mlflow.sklearn.log_model(model, name)
        mlflow.log_param("version", "v1")
