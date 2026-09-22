import logging
import sys
import json
import joblib
import pandas as pd
import os
from datetime import datetime, timezone

# Configurar el logger
logger = logging.getLogger("churn_predictor")
logger.setLevel(logging.INFO)

#ruta a los archivos del modelo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'model', 'scaler.pkl')
COLUMNS_PATH = os.path.join(BASE_DIR, 'model', 'columnas.json')


# Cargar modelo, scaler y columnas
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

with open(COLUMNS_PATH, 'r') as f:
    columnas_esperadas = json.load(f)


if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False



def preparar_datos(datos_cliente: dict) -> pd.DataFrame:
    """
    Prepara los datos del cliente para la predicción.
    
    Args:
        datos_cliente (dict): Diccionario con los datos del cliente.
        
    Returns:
        pd.DataFrame: DataFrame con los datos preparados.
    """
    # Convertir el diccionario a DataFrame
    df_clientes = pd.DataFrame([datos_cliente])

    df_encoded = pd.get_dummies(df_clientes)
    df_encoded = df_encoded.reindex(columns=columnas_esperadas, fill_value=0)
    # Asegurarse de que todas las columnas estén presentes
    
    df_encoded = df_encoded.copy()

    df_scaled = scaler.transform(df_encoded)
    return df_scaled


def predecir_churn(datos_cliente: dict) -> dict:
    """
    Realiza la predicción de churn para un cliente.
    
    Args:
        datos_cliente (dict): Diccionario con los datos del cliente.
        
    Returns:
        dict: Diccionario con la predicción y la probabilidad.
    """
    # Preparar los datos
    df_preparado = preparar_datos(datos_cliente)
    
    # Realizar la predicción
    prediccion = model.predict(df_preparado)
    probabilidad = model.predict_proba(df_preparado)[:, 1]  # Probabilidad de churn

    # Registro estructurado de la predicción (sin datos personales del cliente)
    log_entry = {
        "evento": "prediccion_realizada",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prediccion": int(prediccion[0]),
        "probabilidad": float(probabilidad[0])
    }
    logger.info(json.dumps(log_entry))
    
    return {
        "prediccion": int(prediccion[0]),  # Convertir a int para JSON
        "probabilidad": float(probabilidad[0])  # Convertir a float para JSON
    }

