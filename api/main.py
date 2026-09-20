from fastapi import FastAPI
from pydantic import BaseModel, Field
from predictor import predecir_churn

class ClienteInput(BaseModel):
    gender: str = Field(..., examples=["Female"])
    SeniorCitizen: int = Field(..., examples=[0])
    Partner: str = Field(..., examples=["Yes"])
    Dependents: str = Field(..., examples=["No"])
    tenure: int = Field(..., examples=[12])
    PhoneService: str = Field(..., examples=["Yes"])
    MultipleLines: str = Field(..., examples=["No"])
    InternetService: str = Field(..., examples=["Fiber optic"])
    OnlineSecurity: str = Field(..., examples=["No"])
    OnlineBackup: str = Field(..., examples=["Yes"])
    DeviceProtection: str = Field(..., examples=["No"])
    TechSupport: str = Field(..., examples=["No"])
    StreamingTV: str = Field(..., examples=["Yes"])
    StreamingMovies: str = Field(..., examples=["No"])
    Contract: str = Field(..., examples=["Month-to-month"])
    PaperlessBilling: str = Field(..., examples=["Yes"])
    PaymentMethod: str = Field(..., examples=["Electronic check"])
    MonthlyCharges: float = Field(..., examples=[70.35])
    TotalCharges: float = Field(..., examples=[845.5])



app = FastAPI(
    title="API de Predicción de Cancelación de Clientes",
    description="Predice la probabilidad de que un cliente cancele un servicio.",
    version="1.0.0"
)

@app.get("/")
def inicio():
    return {"mensaje": "API de Churn Prediction activa (v2 - desplegado con CI/CD). Visita /docs para probarla."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict")
def predict(cliente: ClienteInput):
    datos = cliente.model_dump()
    resultado = predecir_churn(datos)
    return resultado