from prefect import flow, task
from sklearn.linear_model import LogisticRegression
from mlflow_register import register_model

@task
def load_data():
    # Replace with real loader
    X = [[0.1, 0.2], [0.3, 0.4]]
    y = [0, 1]
    return X, y

@task
def train_model(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    return model

@flow(name="Retrain Forex Model")
def retrain_pipeline():
    X, y = load_data()
    model = train_model(X, y)
    register_model(model)

if __name__ == "__main__":
    retrain_pipeline()
