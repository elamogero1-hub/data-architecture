# 🏅 Laboratorio de datos · Arquitectura medallón

**E-commerce · Google Cloud · Cloud Composer · BigQuery**

Recorre el end-to-end de datos desde tres CSV hasta un modelo dimensional y KPIs de ventas. El ejercicio está diseñado para trabajar en un Composer compartido, con recursos propios por alumno.

[🗺️ Proyecto y arquitectura](composer_medallon/README.md) · [⚙️ Configuración](composer_medallon/docs/01_configuracion.md) · [🚀 Despliegue](composer_medallon/docs/02_despliegue.md)

## 📚 Empieza aquí

| Paso | Guía | Objetivo |
|---|---|---|
| 1️⃣ | [Proyecto y arquitectura](composer_medallon/README.md) | Comprender landing, bronze, silver y gold |
| 2️⃣ | [Configuración](composer_medallon/docs/01_configuracion.md) | Preparar recursos, permisos e identificador de alumno |
| 3️⃣ | [Despliegue paso a paso](composer_medallon/docs/02_despliegue.md) | Crear objetos, publicar el DAG y ejecutar la primera carga |
| 4️⃣ | [Operación y errores](composer_medallon/docs/04_operacion.md) | Revisar sensores, validaciones y reprocesos |

## 🔄 Recorrido de los datos

```text
📁 CSV en Cloud Storage
   ↓ Sensores de Airflow
🥉 Bronze: columnas STRING
   ↓ SP de limpieza y validación
🥈 Silver: entidades tipadas
   ↓ SP del modelo dimensional
🥇 Gold: dimensiones, hechos y KPIs
```

## 🧰 Código y configuración

[🐍 DAG](composer_medallon/dags/dag_medallon_clinares.py) · [🏗️ DDL](composer_medallon/sql/00_ddl_consolidado_clinares.sql) · [🔧 SP silver/gold](composer_medallon/sql/01_sp_cargas_clinares.sql) · [⚙️ JSON Airflow](composer_medallon/config/ecommerce_config_clinares.json)

> [!IMPORTANT]
> Cada alumno reemplaza **clinares** por la **inicial de su nombre + su primer apellido**. Ejemplo: María Torres → mtorres. Revisa [Ejemplo Alumno](composer_medallon/docs/01_configuracion.md) antes de desplegar.

La documentación utiliza Markdown y enlaces relativos para navegar desde GitHub. Consulta el [alcance de la verificación local](composer_medallon/README.md) antes de ejecutar en Google Cloud.
