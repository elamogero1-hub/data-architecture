# 🚀 Despliegue paso a paso

[🏠 Proyecto y arquitectura](../README.md) · [⚙️ Requisitos y configuración](01_configuracion.md) · [Operación](04_operacion.md)

## 1. Preparar el equipo

Abrir PowerShell dentro de composer_medallon (la carpeta que contiene verificar_local.py):

```powershell
python -m pip install -r requirements-local.txt
python verificar_local.py
```

Para los pasos con gcloud, autenticar y seleccionar proyecto:

```powershell
gcloud auth login
gcloud config set project bsgroup-dev-test-1
```

El login es personal; nunca copiar sus credenciales al repositorio.

## 2. Revisar los SQL

La carpeta [sql](../sql/) contiene una sola versión de cada script:

- [00_ddl_consolidado_clinares.sql](../sql/00_ddl_consolidado_clinares.sql).
- [01_sp_cargas_clinares.sql](../sql/01_sp_cargas_clinares.sql).

Son SQL ejecutables directamente en BigQuery, sin Jinja ni pasos de generación. Usan bsgroup-dev-test-1, bronze_clinares, silver_clinares y gold_clinares. Si se cambia proyecto o alumno, actualizar los SQL y el JSON de Airflow de forma consistente antes de ejecutar.

## 3. Ejecutar DDL manualmente

En [BigQuery](https://console.cloud.google.com/bigquery?project=bsgroup-dev-test-1), pegar el DDL y ejecutarlo completo con ubicación US.

Esperado: tres datasets, diez tablas y tres vistas de KPIs. IF NOT EXISTS conserva tablas existentes; no migra sus esquemas. Si las estructuras ya están correctas, no hace falta recrearlas.

## 4. Crear los SP manualmente

En otra consulta BigQuery, ejecutar el SQL de SP. Esperado:

- silver_clinares.sp_cargar_silver_clinares.
- gold_clinares.sp_cargar_gold_clinares.

No hay SP de bronze ni de DDL. El DAG tampoco crea objetos. Las rutinas antiguas de versiones previas dejan de invocarse; retirarlas manualmente solo cuando corresponda.

## 5. Configurar Airflow

Abrir pe-composer-orchestrator-bsgroup desde [Composer](https://console.cloud.google.com/composer/environments?project=bsgroup-dev-test-1) y entrar a su interfaz Airflow. Crear la Variable JSON descrita en [Configuración](01_configuracion.md). Comprobar permisos antes de ejecutar.

## 6. Publicar solo el DAG

Conservar inicialmente schedule=None y el bloque automático comentado para probar manualmente.

```powershell
gcloud storage cp ./dags/dag_medallon_clinares.py gs://pe-cs-orchestrator-bsgroup/dags/dag_medallon_clinares.py
```

También se puede subir desde la [carpeta de DAGs](https://console.cloud.google.com/storage/browser/pe-cs-orchestrator-bsgroup/dags?project=bsgroup-dev-test-1). No subir todo el repositorio a dags. Si existe el antiguo ecommerce_medallon_clinares.py, pausar su DAG y retirar ese archivo para no mantener dos procesos que escriben las mismas tablas.

Esperar sincronización. Confirmar dag_medallon_clinares sin DAG Import Errors en Airflow.

## 7. Iniciar ejecución y subir archivos

Activar el DAG y pulsar Trigger DAG sin JSON adicional. Los tres sensores comienzan a esperar; timeout de una hora y revisión cada 30 segundos.

Obtener la fecha actual en Lima desde PowerShell:

```powershell
$fechaCarga = python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('America/Lima')).strftime('%Y%m%d'))"
$fechaCarga
```

Debe coincidir con la fecha en Lima en que empezó el DAG. Si cruzó medianoche, usar la fecha de inicio de esa ejecución, visible en sus rutas renderizadas.

```powershell
gcloud storage cp ./data/clientes.csv "gs://pe-cs-datalake-bsgroup/landing/clinares/$fechaCarga/clientes.csv"
gcloud storage cp ./data/productos.csv "gs://pe-cs-datalake-bsgroup/landing/clinares/$fechaCarga/productos.csv"
gcloud storage cp ./data/transacciones.csv "gs://pe-cs-datalake-bsgroup/landing/clinares/$fechaCarga/transacciones.csv"
```

También se pueden subir desde el [bucket de datos](https://console.cloud.google.com/storage/browser/pe-cs-datalake-bsgroup?project=bsgroup-dev-test-1). Mantener CSV UTF-8, cabeceras y orden original de columnas. No reemplazar archivos durante una ejecución.

## 8. Validar ejecución y datos

En Graph deben verse tres sensores, tres cargas bronze y dos CALL. Todas las cargas esperan a los tres sensores; silver espera a las tres cargas.

```sql
SELECT estado, COUNT(*) AS transacciones
FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas`
GROUP BY estado;

SELECT SUM(importe_neto) AS ventas_netas,
       SUM(cantidad) AS unidades_vendidas,
       ROUND(AVG(importe_neto), 2) AS ticket_promedio
FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas`
WHERE estado = 'COMPLETADO';
```

| Comprobación | Esperado con los CSV originales |
|---|---:|
| Clientes | 50 |
| Productos | 30 |
| Hechos | 100 |
| Completados / pendientes / anulados | 60 / 21 / 19 |
| Ventas netas completadas | 51599.45 |
| Unidades completadas | 194 |
| Ticket por transacción completada | 859.99 |

## 9. Activar modo automático opcional

En el Python:

1. Comentar schedule=None.
2. Descomentar schedule="*/5 * * * *"; debe quedar una sola opción schedule.
3. Descomentar todo el código entre INICIO CODIGO AUTOMATICO y FIN CODIGO AUTOMATICO.
4. Publicar de nuevo el Python y mantener el DAG activo.

El bloque ya está incluido pero desactivado. Su funcionamiento y límites están en [Operación](04_operacion.md). No incluir fecha en el JSON: al día siguiente se buscará la nueva carpeta sin editar configuración. GitHub no publica estos cambios a Composer por sí solo.

## Registro de aceptación

Después de probar en nube, registrar en el PR o issue: fecha, versión de Composer/Airflow/proveedor Google, commit probado, run_id, resultado del DAG y reconciliación de datos. No afirmar despliegue exitoso solo por pasar verificar_local.py.

---

[🏠 Proyecto y arquitectura](../README.md) · [⚙️ Configuración](01_configuracion.md) · [🚀 Despliegue](02_despliegue.md) · [🛠️ Operación](04_operacion.md)
