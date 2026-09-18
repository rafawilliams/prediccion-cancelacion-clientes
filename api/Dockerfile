FROM python:3.13-slim

WORKDIR /app

#copiamos primero solo requirements.txt para instalar dependencias
COPY requirements.txt .

#intalizamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

#copiamos el resto de la app
COPY . .

#exponemos el puerto 8000
EXPOSE 8000

#comando que se ejecuta al iniciar el contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]