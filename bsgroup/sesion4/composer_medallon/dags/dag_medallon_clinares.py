"""Ejercicio: ejecutar manualmente ANTES de subir una entrega inmutable a landing."""
import re
import datetime
from zoneinfo import ZoneInfo

from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

# Cada alumno tiene una key propia en Airflow > Variables, con valor JSON.
ALUMNO = "clinares"
if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", ALUMNO):
    raise ValueError("ALUMNO debe tener 2-40 caracteres: minusculas, numeros o guion bajo")
CONFIG_KEY = f"ecommerce_config_{ALUMNO}"

# Jinja lee la Variable durante el renderizado de cada tarea, no al importar el DAG.
def config(campo):
    return "{{ var.json['" + CONFIG_KEY + "']['" + campo + "'] }}"

PROJECT_ID = config("project_id")
BUCKET = config("bucket")
LOCATION = config("location")
BRONZE = config("bronze_dataset")
CONNECTION = "google_cloud_default"
# La fecha se obtiene al iniciar la ejecucion, nunca al importar el DAG.
# Se mantiene fija para todos los sensores, cargas y reintentos de esa ejecucion.
def fecha_de_carga(dag_run):
    if dag_run.start_date is None:
        raise ValueError("La ejecucion debe tener fecha de inicio")
    return dag_run.start_date.astimezone(ZoneInfo("America/Lima")).strftime("%Y%m%d")

FECHA_CARGA = "{{ fecha_de_carga(dag_run) }}"
LANDING = config("landing_prefix") + "/" + FECHA_CARGA

# Asegurar renderizado de project_id/location en el operador de consultas.
# Se conserva el operador oficial y se habilitan esos dos campos para Jinja.
class ConsultaBigQueryJSONOperator(BigQueryInsertJobOperator):
    template_fields = tuple(dict.fromkeys((*BigQueryInsertJobOperator.template_fields,
                                          "project_id", "location")))

# El operador oficial conserva la carga CSV y habilita estos campos para Jinja.
class CargaBigQueryJSONOperator(GCSToBigQueryOperator):
    template_fields = tuple(dict.fromkeys((*GCSToBigQueryOperator.template_fields,
                                          "project_id", "location")))

SCHEMAS = {
    "clientes": ["cliente_id", "nombre_completo", "email", "telefono", "ciudad",
                 "segmento", "fecha_registro", "activo"],
    "productos": ["producto_id", "nombre_producto", "categoria", "marca",
                  "precio_unitario", "costo_unitario", "stock_actual", "disponible"],
    "transacciones": ["transaccion_id", "fecha_transaccion", "cliente_id", "producto_id",
                      "cantidad", "precio_unitario", "descuento_monto", "monto_total",
                      "metodo_pago", "canal_venta", "estado"],
}

default_args = {
    'owner': ALUMNO,
    'start_date': datetime.datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=1),
}

dag = DAG(
    dag_id=f"dag_medallon_{ALUMNO}",
    description="Landing -> bronze STRING -> silver tipada -> gold dimensional",
    schedule=None,  # Modo manual para la clase.
    # AUTOMATICO: comentar la linea anterior y descomentar esta:
    # schedule="*/5 * * * *",  # Crear una revision cada cinco minutos.
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    params={"config_key": CONFIG_KEY},
    user_defined_macros={"fecha_de_carga": fecha_de_carga},
    tags=["academico", "ecommerce", "medallon", ALUMNO],
)

def query_task(task_id, query):
    return ConsultaBigQueryJSONOperator(
        task_id=task_id, dag=dag, project_id=PROJECT_ID, location=LOCATION,
        gcp_conn_id=CONNECTION,
        configuration={"query": {"query": query, "useLegacySql": False}},
    )

def call_sp(task_id, capa, nombre, argumentos=""):
    dataset = config(capa + "_dataset")
    return query_task(task_id, f"CALL `{PROJECT_ID}.{dataset}.{nombre}_{ALUMNO}`({argumentos});")

# Los sensores detectan los CSV; las cargas usan GCSToBigQueryOperator.
# Las tablas ya deben existir: DDL manual y CREATE_NEVER en cada carga.
sensores = []
cargas = []
for tabla, columnas in SCHEMAS.items():
    esperar = GCSObjectExistenceSensor(
        task_id=f"esperar_{tabla}", dag=dag, bucket=BUCKET,
        object=f"{LANDING}/{tabla}.csv", google_cloud_conn_id=CONNECTION,
        mode="reschedule", poke_interval=30, timeout=3600,
    )
    cargar = CargaBigQueryJSONOperator(
        task_id=f"bronze_{tabla}", dag=dag, bucket=BUCKET,
        source_objects=[f"{LANDING}/{tabla}.csv"],
        destination_project_dataset_table=f"{PROJECT_ID}.{BRONZE}.{tabla}",
        project_id=PROJECT_ID, location=LOCATION, gcp_conn_id=CONNECTION,
        schema_fields=[{"name": col, "type": "STRING", "mode": "NULLABLE"}
                       for col in columnas],
        source_format="CSV", skip_leading_rows=1, field_delimiter=",",
        encoding="UTF-8", autodetect=False, max_bad_records=0,
        create_disposition="CREATE_NEVER", write_disposition="WRITE_TRUNCATE",
    )
    sensores.append(esperar)
    cargas.append(cargar)

silver = call_sp("sp_cargar_silver", "silver", "sp_cargar_silver")
gold = call_sp("sp_cargar_gold", "gold", "sp_cargar_gold")

# Barrera: cada carga espera a los TRES sensores, no solo a su propio archivo.
for sensor in sensores:
    for carga in cargas:
        sensor >> carga
for carga in cargas:
    carga >> silver
silver >> gold

# ============================================================================
# BLOQUE OPCIONAL: DETECCION AUTOMATICA SIN RECARGAR LA MISMA FECHA
# ============================================================================
# Activacion (hacer los dos pasos):
# 1. Cambiar schedule=None por schedule="*/5 * * * *" arriba y activar el DAG.
# 2. Descomentar TODAS las lineas de codigo entre INICIO y FIN de este bloque.
#
# Subir la entrega a la carpeta YYYYMMDD del dia en America/Lima.
# La fecha se calcula con el inicio de la ejecucion; no se configura en el JSON.
# Airflow revisa por sondeo: GCS no dispara una ejecucion por si solo.
# No cambiar la configuracion mientras una ejecucion este activa.
# El control omite la ultima entrega exitosa; para reprocesarlo manualmente,
# eliminar la Variable ecommerce_ultima_carga_clinares en Airflow.
# El marker se escribe solo despues de que gold termine correctamente.
# Si falla, la entrega puede volver a intentarse; esto no garantiza exactly-once.
#
# --- INICIO CODIGO AUTOMATICO ---
# import json
# from airflow.models import Variable
# try:
#     from airflow.providers.standard.operators.python import PythonOperator, ShortCircuitOperator
# except ImportError:
#     from airflow.operators.python import PythonOperator, ShortCircuitOperator
#
# ULTIMA_CARGA_KEY = f"ecommerce_ultima_carga_{ALUMNO}"
#
# def identidad_carga(dag_run):
#     cfg = Variable.get(CONFIG_KEY, deserialize_json=True)
#     campos = ("project_id", "bucket", "landing_prefix",
#               "bronze_dataset", "silver_dataset", "gold_dataset", "location")
#     identidad = {campo: cfg[campo] for campo in campos}
#     identidad["fecha_carga"] = fecha_de_carga(dag_run)
#     return json.dumps(identidad, sort_keys=True)
#
# def es_carga_nueva(dag_run, **context):
#     ultimo = Variable.get(ULTIMA_CARGA_KEY, default_var="")
#     return identidad_carga(dag_run) != ultimo
#
# def registrar_carga_exitosa(dag_run, **context):
#     Variable.set(ULTIMA_CARGA_KEY, identidad_carga(dag_run))
#
# revisar_carga = ShortCircuitOperator(
#     task_id="revisar_fecha_nueva", python_callable=es_carga_nueva, dag=dag,
# )
# registrar_carga = PythonOperator(
#     task_id="registrar_carga_exitosa", python_callable=registrar_carga_exitosa, dag=dag,
# )
# for tabla in ("clientes", "productos", "transacciones"):
#     revisar_carga >> dag.get_task(f"esperar_{tabla}")
# gold >> registrar_carga
# --- FIN CODIGO AUTOMATICO ---
