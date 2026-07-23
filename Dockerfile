# ══════════════════════════════════════════════════════════════
# Dockerfile — TechNova Solutions
# Imagen Python 3.12-slim con Gunicorn
# ══════════════════════════════════════════════════════════════

# Imagen base ligera de Python
FROM python:3.12.8-slim

# Evita que Python escriba archivos .pyc y fuerza salida directa
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para mysql-connector-python
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para ejecutar la aplicacion
RUN useradd -r -s /bin/false -d /app technova

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar archivo de dependencias e instalar paquetes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo de la aplicacion
COPY . .

# Dar permisos al usuario tecnova
RUN chown -R technova:technova /app

# Puerto que expone la aplicacion
EXPOSE 5000

# Ejecutar como usuario no-root
USER technova

# Ejecutar la app con Gunicorn
# 4 workers para concurrencia basica
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
