import logging
import json
import joblib
import pandas as pd
import json
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
    columnas = json.load(f)


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
    
    # Asegurarse de que todas las columnas estén presentes
    for col in columnas:
        if col not in df_clientes.columns:
            df_clientes[col] = 0  # Asignar 0 a las columnas faltantes
    
    # Reordenar las columnas según el orden original
    df = df_clientes[columnas]
    
    # Escalar los datos
    df_scaled = scaler.transform(df)
    
    return pd.DataFrame(df_scaled, columns=columnas)


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

