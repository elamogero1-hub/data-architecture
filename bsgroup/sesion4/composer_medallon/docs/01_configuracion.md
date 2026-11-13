# ⚙️ Configuración de la solución

[🏠 Proyecto y arquitectura](../README.md) · [🚀 Siguiente: despliegue](02_despliegue.md)

## Recursos y requisitos

| Recurso | Configuración |
|---|---|
| Proyecto | bsgroup-dev-test-1 |
| Entorno Composer | pe-composer-orchestrator-bsgroup |
| Código DAG | gs://pe-cs-orchestrator-bsgroup/dags/dag_medallon_clinares.py |
| Datos CSV | gs://pe-cs-datalake-bsgroup/landing/clinares/YYYYMMDD/ |
| BigQuery | US en el ejemplo |
| Zona horaria de carpetas | America/Lima |

Necesitas Python y Git en el equipo local. Google Cloud CLI se usa para los comandos de publicación; también puedes usar la consola web. Composer debe existir, tener las APIs necesarias habilitadas y usar una imagen con proveedor Google compatible. No actualizar el proveedor a ciegas ni instalar Airflow localmente solo para renderizar SQL.

## Enlaces del proyecto

- [Composer](https://console.cloud.google.com/composer/environments?project=bsgroup-dev-test-1).
- [Carpeta de DAGs](https://console.cloud.google.com/storage/browser/pe-cs-orchestrator-bsgroup/dags?project=bsgroup-dev-test-1).
- [Bucket de CSV](https://console.cloud.google.com/storage/browser/pe-cs-datalake-bsgroup?project=bsgroup-dev-test-1).
- [BigQuery](https://console.cloud.google.com/bigquery?project=bsgroup-dev-test-1).
- [IAM](https://console.cloud.google.com/iam-admin/iam?project=bsgroup-dev-test-1).

Seleccionar el entorno y confirmar su carpeta real de DAGs y cuenta de servicio. La región de Composer aún no está especificada: no asumir que sea US, porque ese valor pertenece a BigQuery. Confirmar compatibilidad de ubicación entre bucket de datos y datasets.

## Permisos

| Identidad | Acceso |
|---|---|
| Docente que prepara BigQuery | Crear datasets, tablas, vistas y rutinas |
| Cuenta de servicio de Composer | Storage Object Viewer en bucket de datos |
| Cuenta de servicio de Composer | BigQuery Job User en el proyecto |
| Cuenta de servicio de Composer | BigQuery Data Editor en los tres datasets del alumno |
| Persona que publica | Escritura en el bucket de DAGs y/o bucket de CSV, según tarea |

Mantener además los permisos propios del entorno Composer. Usar google_cloud_default con credenciales predeterminadas de su cuenta de servicio. No colocar claves de servicio en código ni Variables del ejemplo.

## Variable JSON en Airflow

En la interfaz de Airflow, abrir Variables (en Airflow 2, Admin → Variables).

**Key:** ecommerce_config_clinares

**Value:**

```json
{
  "project_id": "bsgroup-dev-test-1",
  "bucket": "pe-cs-datalake-bsgroup",
  "location": "US",
  "landing_prefix": "landing/clinares",
  "bronze_dataset": "bronze_clinares",
  "silver_dataset": "silver_clinares",
  "gold_dataset": "gold_clinares"
}
```

[JSON de configuración para copiar en Airflow](../config/ecommerce_config_clinares.json).

| Campo | Significado |
|---|---|
| project_id | Proyecto de tablas y jobs |
| bucket | Bucket de CSV, sin gs:// y sin /dags |
| location | Ubicación BigQuery; debe coincidir con los datasets |
| landing_prefix | Carpeta del alumno, sin barra final |
| bronze_dataset | Destino de la carga original |
| silver_dataset | Entidades limpias y tipadas |
| gold_dataset | Dimensiones, hechos y KPIs |

No incluir fecha_carga ni lote. No cambiar la Variable durante una ejecución. El DAG utiliza Jinja var.json durante el renderizado de cada tarea. El identificador ALUMNO se fija en el archivo Python para elegir su DAG y su key; no es una variable global de Composer. No habilitar sobrescritura de params desde dag_run.conf para este laboratorio.

## Ejemplo Alumno

> **Importante:** cada alumno debe reemplazar `clinares` por **la primera letra de su nombre + su primer apellido**, en minúsculas, sin espacios ni tildes. Este identificador debe ser el mismo en todos sus archivos y recursos para evitar sobrescribir el trabajo de otros alumnos en el Composer compartido.

Por ejemplo: **Carlos Linares → `clinares`** y **María Torres → `mtorres`**. Si dos alumnos tienen el mismo identificador, acordar uno único con el docente, por ejemplo `mtorres2`.

Para María Torres, los nombres quedarían así:

| Recurso | Ejemplo |
|---|---|
| Archivo DAG | `dag_medallon_mtorres.py` |
| Identificador ALUMNO | `mtorres` |
| DAG ID | `dag_medallon_mtorres` |
| Key de Variable Airflow | `ecommerce_config_mtorres` |
| Datasets | `bronze_mtorres`, `silver_mtorres`, `gold_mtorres` |
| SP | `sp_cargar_silver_mtorres`, `sp_cargar_gold_mtorres` |
| Prefijo de CSV | `landing/mtorres` |

Cada alumno puede trabajar en su propio clon del repositorio:

1. Copiar el ejemplo o ajustar su clon sustituyendo clinares por su identificador en el DAG, los dos SQL y el JSON. Renombrar los archivos correspondientes.
2. Mantener ALUMNO, dag_id, nombres de SP, datasets, key de Variable y landing_prefix coherentes.
3. Ejecutar manualmente sus DDL y SP y crear su Variable JSON.
4. Publicar su DAG con nombre único en el Composer compartido.
5. Subir sus CSV a landing/IDENTIFICADOR/YYYYMMDD/.

Usar inicial y primer apellido sin tildes; agregar número si hay coincidencias. No conservar copias completas de alumnos de ejemplo en este repositorio. Se comparten proyecto y Composer, pero cambian los nombres de recursos de cada alumno. Esta separación evita colisiones, no constituye aislamiento de permisos.

El verificador local está preparado para clinares. Si se adapta el ejemplo, actualizar también el identificador y las rutas esperadas del verificador.

---

[🏠 Proyecto y arquitectura](../README.md) · [⚙️ Configuración](01_configuracion.md) · [🚀 Despliegue](02_despliegue.md) · [🛠️ Operación](04_operacion.md)
