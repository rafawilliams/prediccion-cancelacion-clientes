# Customer Churn Prediction — Predicción de Cancelación de Clientes

Proyecto de Machine Learning end-to-end que predice si un cliente cancelará un
servicio, como parte de un portafolio profesional de **Ingeniería en IA/ML y MLOps**.
Incluye análisis de datos, entrenamiento de modelos, una API contenerizada,
desplegada en AWS y gestionada como Infraestructura como Código con Terraform.

> **Nota sobre el despliegue:** la infraestructura se crea y destruye bajo demanda
> con Terraform (`terraform apply` / `terraform destroy`) para controlar costos,
> por lo que la URL pública cambia en cada creación. Ver la sección
> [Cómo desplegar la infraestructura](#cómo-desplegar-la-infraestructura).

## Objetivo del proyecto

Anticipar qué clientes tienen alta probabilidad de cancelar un servicio (*churn*),
para que una empresa pueda actuar a tiempo con estrategias de retención, en lugar
de reaccionar después de que el cliente ya se fue.

## Dataset

- **Fuente:** Telco Customer Churn (IBM Sample Dataset, vía Kaggle)
- **Tamaño original:** 7,043 clientes, 21 columnas
- **Tamaño tras limpieza:** 7,032 clientes (se eliminaron 11 filas con datos faltantes)
- **Variable objetivo:** `Churn` (Yes/No → 1/0)

## Fase 1 — Análisis Exploratorio de Datos (EDA)

📓 Notebook: [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb)

### Calidad de los datos
- Se detectaron 11 valores faltantes en `TotalCharges` (venían como texto vacío
  en lugar de números) y se eliminaron por representar menos del 0.2% del dataset.
- No se encontraron filas duplicadas.

### Distribución de la variable objetivo
- **73.5%** de los clientes no cancelaron.
- **26.5%** de los clientes sí cancelaron.
- Desbalance de clases moderado, considerado en la fase de modelado.

### Principales hallazgos
- Los clientes con contrato **mes a mes** cancelan significativamente más que
  los de contrato anual o bianual.
- La cancelación es más frecuente en clientes **nuevos** (baja antigüedad).
- Los clientes que pagan con **cheque electrónico** cancelan más que quienes
  tienen pago automático.
- Cargos mensuales más **altos** se asocian con mayor cancelación.
- La falta de servicios adicionales (ej. soporte técnico) se asocia con mayor
  cancelación.

## Fase 2 — Entrenamiento y Evaluación del Modelo

📓 Notebook: [`notebooks/02_training.ipynb`](notebooks/02_training.ipynb)

### Preparación de datos
- Codificación de variables categóricas mediante One-Hot Encoding.
- Escalado de variables numéricas con `StandardScaler`.
- División 80/20 en entrenamiento y prueba, estratificada por la variable objetivo.

### Modelos evaluados

| Métrica | Regresión Logística | Random Forest |
|---|---|---|
| Accuracy | 77.97% | 70.29% |
| Precision | 69.75% | 46.60% |
| **Recall** | 30.21% | **80.75%** |
| F1-score | 42.16% | 59.10% |

### Modelo elegido: Random Forest

Se seleccionó **Random Forest** (con `class_weight='balanced'`) como modelo final,
priorizando el **recall** sobre el accuracy general.

**Justificación:** en un caso de negocio de retención de clientes, el costo de
*no detectar* a un cliente que va a cancelar (falso negativo) suele ser mayor
que el costo de contactar a un cliente que en realidad no iba a cancelar (falso
positivo) — adquirir un cliente nuevo típicamente cuesta más que retener uno
existente. Con un recall de 80.75%, el modelo detecta a 4 de cada 5 clientes en
riesgo real de cancelación, frente a solo 3 de cada 10 con Regresión Logística.

## Fase 3 — Construcción y Contenerización de la API

📁 Código: [`api/`](api/)

### Diseño de la API
- Construida con **FastAPI**, expuesta en el puerto `8000`.
- Endpoints:
  - `GET /` — mensaje de bienvenida / verificación básica.
  - `GET /health` — chequeo de salud (health check), usado por AWS en la Fase 4
    para monitorear si el servicio sigue disponible.
  - `POST /predict` — recibe los datos de un cliente y devuelve la predicción
    de cancelación junto con su probabilidad.
- Validación automática de los datos de entrada mediante `pydantic`, incluyendo
  documentación interactiva autogenerada en `/docs` (Swagger UI).

### Lógica de predicción (`predictor.py`)
- Carga el modelo (`model.pkl`), el `scaler.pkl` y el orden de columnas
  (`columnas.json`) una sola vez al iniciar la API.
- Transforma los datos de un cliente nuevo aplicando el mismo proceso usado en
  el entrenamiento: One-Hot Encoding, `reindex()` para garantizar las mismas
  columnas en el mismo orden, y escalado con `StandardScaler`.
- Devuelve tanto la clase predicha (cancela / no cancela) como la probabilidad,
  permitiendo priorizar clientes según su nivel de riesgo en vez de una
  decisión binaria.

### Ejemplo de respuesta de la API

```json
{
  "prediccion": 1,
  "probabilidad": 0.5516
}
```

### Contenerización con Docker
- La API se empaquetó en una imagen Docker basada en `python:3.11-slim`,
  incluyendo el modelo entrenado y todas sus dependencias.
- Uso de `.dockerignore` para excluir archivos innecesarios de la imagen
  (entornos virtuales, cache, archivos de git).
- Verificada localmente con:
  ```bash
  docker build -t churn-prediction-api .
  docker run -p 8000:8000 churn-prediction-api
  ```

## Fase 4 — Despliegue en AWS

### Arquitectura de despliegue

```
[Imagen Docker local]
        |
        v
[Amazon ECR]  <- almacena la imagen del contenedor
        |
        v
[Amazon ECS - Express Mode]  <- ejecuta el contenedor, genera URL pública
        |
        v
[Usuario / Cliente HTTP]  <- consume la API desde internet
```

### Decisión de arquitectura: por qué ECS Express Mode y no App Runner

El plan original consideraba **AWS App Runner** por su simplicidad. Sin embargo,
AWS dejó de aceptar cuentas nuevas en App Runner a partir del **30 de abril de
2026**, y recomienda **Amazon ECS Express Mode** como sucesor para nuevos
despliegues de contenedores. Express Mode ofrece una experiencia de despliegue
igual de simple (un solo formulario: imagen, puerto, tamaño de recursos), pero
construida directamente sobre ECS estándar, sin costo adicional por el propio
servicio — solo se paga por los recursos de cómputo (Fargate) y networking
subyacentes.

### Pasos del despliegue

1. Creación de un repositorio privado en **Amazon ECR**.
2. Etiquetado (`docker tag`) y subida (`docker push`) de la imagen local al
   repositorio de ECR.
3. Creación de un servicio con **ECS Express Mode**, especificando la imagen
   de ECR, el puerto (`8000`) y el tamaño de recursos (`0.25 vCPU / 0.5 GB`).
4. AWS aprovisionó automáticamente el balanceador de carga y una URL pública.

### Verificación en producción

Se confirmó que la API responde de forma idéntica en la nube y en local: una
misma petición de prueba devolvió exactamente la misma probabilidad de
cancelación (`0.5515920199080583`) en ambos entornos, validando que el modelo,
el scaler y el preprocesamiento se comportan de forma consistente end-to-end.

```json
{
  "prediccion": 1,
  "probabilidad": 0.5515920199080583
}
```

### Control de costos

- Tamaño de recursos mínimo (`0.25 vCPU / 0.5 GB`) para mantener el costo bajo,
  al ser un proyecto de portafolio sin tráfico de producción real.
- Alarma de facturación configurada en CloudWatch (umbral de aviso por correo).
- El servicio puede escalarse a 0 réplicas cuando no se está usando activamente:
  ```bash
  aws ecs update-service --cluster <nombre-del-cluster> \
    --service churn-prediction-api --desired-count 0 --region us-east-1
  ```

## Fase 5 — CI/CD con GitHub Actions

### Objetivo
Automatizar por completo el ciclo de despliegue: cada cambio en el código de la
API (`git push` a `main`) dispara automáticamente la construcción de la imagen,
su publicación en ECR, y el redespliegue en ECS — sin intervención manual.

### Arquitectura del pipeline

```
[git push a main]
        |
        v
[GitHub Actions se activa]  <- solo si el cambio afecta la carpeta api/
        |
        v
[Build de la imagen Docker]
        |
        v
[Push a Amazon ECR]
        |
        v
[Forzar redespliegue en ECS]  <- aws ecs update-service --force-new-deployment
        |
        v
[Nueva versión disponible en producción]
```

### Seguridad: usuario IAM dedicado

Se creó un usuario IAM específico (`github-actions-churn-api`), distinto del
usuario usado para el despliegue manual, con permisos acotados solo a ECR y
ECS (en vez de reutilizar credenciales personales de mayor privilegio). Las
credenciales se almacenan como **Repository Secrets** de GitHub (nunca en el
código): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ACCOUNT_ID`.

> **Mejora de seguridad pendiente:** reemplazar la política predefinida
> `AmazonECS_FullAccess` por una política personalizada de mínimo privilegio,
> acotada a este repositorio de ECR y este servicio de ECS específicamente.

### Workflow (`.github/workflows/deploy.yml`)

- **Trigger:** `push` a la rama `main`, filtrado a cambios dentro de `api/**`
  (evita despliegues innecesarios si solo cambian notebooks o documentación).
- **Pasos:** checkout del código → autenticación con AWS → login en ECR →
  build y push de la imagen (`:latest`) → redespliegue forzado en ECS.

### Verificación

Se probó el pipeline de extremo a extremo: un cambio en el mensaje de
bienvenida de la API se subió con `git push`, se construyó y publicó
automáticamente, y se reflejó en la URL pública sin ejecutar ningún comando
manual de Docker o AWS CLI.

## Fase 6 — Monitoreo del modelo en producción

### Motivación

Un modelo entrenado con datos de un momento dado puede volverse menos preciso
con el tiempo a medida que el comportamiento real de los clientes cambia
(*model drift* / *data drift*), sin que esto produzca ningún error visible —
solo predicciones cada vez menos confiables. Este enfoque implementa un
monitoreo ligero, basado en la infraestructura ya existente (CloudWatch), que
sirve como señal indirecta y económica de ese fenómeno.

### Logging estructurado (`predictor.py`)

Cada llamada a `predecir_churn()` registra un evento en formato JSON:

```json
{"evento": "prediccion_realizada", "timestamp": "2026-...", "prediccion": 1, "probabilidad": 0.5516}
```

- Deliberadamente **no** incluye los datos del cliente (por privacidad):
  solo el resultado de la predicción.
- El logger usa un `StreamHandler(sys.stdout)` explícito — necesario para que
  ECS/Fargate capture la salida del contenedor y la envíe automáticamente a
  CloudWatch Logs (un logger sin handler configurado no emite nada visible).

### Métrica personalizada en CloudWatch

Se creó un **metric filter** sobre el log group del servicio:

- **Patrón:** `{ $.evento = "prediccion_realizada" }`
- **Namespace:** `ChurnPredictionAPI`
- **Métrica:** `PrediccionValue` — extrae `$.prediccion` (0 o 1) de cada log

Esto convierte cada predicción registrada en un punto de datos graficable,
sin necesidad de una base de datos ni un servicio adicional.

### Alarmas configuradas

Dos alarmas sobre el promedio horario (`Average`, período de 1 hora) de
`PrediccionValue`, usadas como señal de que el comportamiento del modelo
se desvió del ~26.5% de cancelación observado en el dataset de entrenamiento:

| Alarma | Condición | Qué podría indicar |
|---|---|---|
| `churn-api-prediccion-promedio-alto` | Promedio > 0.6 | El modelo marca muchos más clientes como riesgo de lo esperado |
| `churn-api-prediccion-promedio-bajo` | Promedio < 0.05 | El modelo casi no detecta cancelaciones (posible falla en el pipeline de datos, no solo *drift*) |

### Alcance y limitación reconocida

Este enfoque detecta cambios en la **distribución de las predicciones del
modelo**, un proxy razonable y de bajo costo para *drift*, pero no equivale a
un monitoreo estadístico riguroso de *data drift* (que compararía las
distribuciones de las variables de entrada contra las del entrenamiento, con
pruebas como Kolmogorov-Smirnov o PSI). Ese nivel más avanzado queda como
mejora futura, previsiblemente con una herramienta especializada como
**Evidently AI**.

## Fase 7 — Infraestructura como Código (IaC) con Terraform

📁 Código: [`infra/`](infra/)

### Motivación

Durante el despliegue manual (Fase 4), eliminar por completo la infraestructura
(servicio ECS Express + ALB + security groups asociados) requería recordar y
ejecutar comandos específicos (`delete-express-gateway-service`, distinto del
`delete-service` estándar de ECS). Un olvido de este tipo derivó en un gasto
no controlado. Terraform resuelve esto: describe toda la infraestructura como
código versionado, y su archivo de estado (`terraform.tfstate`) lleva registro
exacto de qué se creó, de modo que un solo comando crea o destruye todo el
conjunto sin dejar recursos huérfanos.

### Recursos gestionados

- `aws_iam_role` (x2): rol de ejecución de tareas y rol de infraestructura
  requerido por ECS Express Mode.
- `aws_iam_role_policy_attachment` (x2): políticas administradas asociadas a
  cada rol.
- `aws_ecs_express_gateway_service`: el servicio en sí, referenciando la
  imagen publicada en Amazon ECR, con `cpu = 256`, `memory = 512` y
  `health_check_path = "/health"`.

### Ciclo de trabajo

```bash
cd infra
terraform init      # descarga el provider de AWS (una sola vez)
terraform validate  # valida sintaxis y nombres de atributos, sin tocar AWS
terraform plan       # previsualiza qué se va a crear/cambiar/destruir
terraform apply      # crea la infraestructura real y muestra la URL pública
terraform destroy    # elimina todo el conjunto de recursos de una sola vez
```

### Verificación del ciclo completo

Se ejecutó `terraform apply` (5 recursos creados) seguido de `terraform destroy`
(5 recursos eliminados, sin recursos huérfanos), confirmando que Terraform
gestiona correctamente la cadena completa de dependencias — incluyendo el
tiempo de espera propio del *deregistration delay* del ALB (~5-8 minutos) al
destruir el servicio.

### Próxima mejora: modularización

El código vive actualmente en un único archivo `main.tf`. Está planeada su
refactorización a un módulo reutilizable (`modules/ecs-express-service/`),
de forma que pueda reutilizarse para desplegar otros proyectos del portafolio
(por ejemplo, el proyecto de detección de fraude) sin duplicar código.

## Estructura del proyecto

```
churn-prediction-mlops/
├── data/
│   ├── telco_churn.csv          # Dataset original
│   └── telco_churn_clean.csv    # Dataset limpio (post Fase 1)
├── notebooks/
│   ├── 01_eda.ipynb             # Análisis exploratorio
│   └── 02_training.ipynb        # Entrenamiento y evaluación
├── model/
│   ├── model.pkl                # Modelo Random Forest entrenado
│   ├── scaler.pkl               # StandardScaler ajustado
│   └── columnas.json            # Orden de columnas esperado por el modelo
├── api/
│   ├── model/                   # Copia del modelo usada por la API
│   ├── main.py                  # Definición de la API (FastAPI)
│   ├── predictor.py             # Lógica de carga del modelo y predicción
│   ├── requirements.txt         # Dependencias de la API
│   ├── Dockerfile               # Imagen Docker de la API
│   └── .dockerignore
├── .github/
│   └── workflows/
│       └── deploy.yml           # Pipeline de CI/CD (build + push + deploy)
├── infra/
│   ├── main.tf                  # Infraestructura de AWS como código (Terraform)
│   └── .gitignore                # Excluye .terraform/ y *.tfstate
└── README.md
```

## Cómo reproducir este proyecto

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd churn-prediction-mlops

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Instalar dependencias
pip install pandas numpy matplotlib seaborn scikit-learn jupyter joblib

# 4. Ejecutar los notebooks en orden
jupyter notebook
# Correr 01_eda.ipynb y luego 02_training.ipynb
```

### Levantar la API localmente

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
# Visitar http://127.0.0.1:8000/docs para probarla
```

### Levantar la API con Docker

```bash
cd api
docker build -t churn-prediction-api .
docker run -p 8000:8000 churn-prediction-api
# Visitar http://127.0.0.1:8000/docs para probarla
```

### Cómo desplegar la infraestructura

La infraestructura en AWS se gestiona con Terraform y se crea/destruye bajo
demanda (ver [Fase 7](#fase-7--infraestructura-como-código-iac-con-terraform)):

```bash
cd infra
terraform init
terraform plan
terraform apply    # escribir "yes" para confirmar
# La URL pública se imprime al final como output "api_url"

# Cuando ya no se necesite el servicio activo:
terraform destroy  # escribir "yes" para confirmar
```

## Próximos pasos

- [x] **Fase 3:** Construir una API con FastAPI que sirva el modelo (`POST /predict`)
      y contenerizarla con Docker.
- [x] **Fase 4:** Desplegar el contenedor en AWS (Amazon ECR + ECS Express Mode).
- [x] **Fase 5:** Automatizar el pipeline con CI/CD (GitHub Actions): build, push
      a ECR y despliegue automático en cada cambio.
- [x] **Fase 6:** Monitoreo del modelo en producción (logging estructurado,
      métrica personalizada en CloudWatch y alarmas sobre la distribución
      de predicciones, como proxy de *model/data drift*).
- [x] **Fase 7:** Gestionar la infraestructura como código con Terraform
      (creación y destrucción reproducible, sin recursos huérfanos).
- [ ] Modularizar el código de Terraform para reutilizarlo en otros proyectos
      del portafolio.
- [ ] Migrar el entrenamiento a **Amazon SageMaker** (siguiente proyecto del
      portafolio de MLOps).

---
*Proyecto desarrollado como parte de un portafolio de Ingeniería en IA/ML y MLOps.*