from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3  # AWS SDK
import joblib
import os

app = FastAPI()

ARTIFACT_BUCKET = os.environ["ARTIFACT_BUCKET"]
MODEL_KEY = "artifacts/current/model.joblib"
MODEL_PATH = os.path.expanduser("~/models/model.joblib")


def download_model():
    """Tải model từ S3 về máy"""
    s3 = boto3.client('s3')
    s3.download_file(ARTIFACT_BUCKET, MODEL_KEY, MODEL_PATH)
    print(f"Model downloaded to {MODEL_PATH}")


# Tải model khi server khởi động
download_model()
model = joblib.load(MODEL_PATH)


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    """Endpoint kiểm tra sức khỏe"""
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    """
    Endpoint dự đoán thu nhập.
    
    Input:  {"features": [f1, f2, ..., f10]}
    Output: {"prediction": 0|1, "label": "thu_nhap_thap"|"thu_nhap_cao"}
    """
    if len(req.features) != 10:
        raise HTTPException(status_code=400, detail="Expected 10 features")
    
    prediction = model.predict([req.features])[0]
    label = "thu_nhap_cao" if prediction == 1 else "thu_nhap_thap"
    
    return {"prediction": int(prediction), "label": label}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
