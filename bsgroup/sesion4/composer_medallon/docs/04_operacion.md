# 🛠️ Operación y solución de errores

[🏠 Proyecto y arquitectura](../README.md) · [Despliegue](02_despliegue.md)

## Modo manual

schedule=None: pulsar Trigger DAG. Los sensores detectan los tres archivos de la carpeta de la fecha de inicio en Lima. Subir un archivo por sí solo no inicia el DAG. Conservar la Variable JSON y los archivos mientras corre la ejecución.

## Modo automático opcional

El bloque comentado del Python se habilita junto con schedule="*/5 * * * *". Cada ejecución revisa si la identidad de proyecto, prefijo, datasets y fecha del día coincide con la última entrega exitosa. Si coincide, ShortCircuitOperator omite el procesamiento; si no, los sensores esperan y las cargas avanzan.

La Variable ecommerce_ultima_carga_clinares se escribe después de gold. No crearla a mano. Para reprocesar el día actual, eliminarla y ejecutar otra vez. Si el guardado del control falla después de gold, puede haber reproceso: no se garantiza exactly-once. Solo se recuerda la última identidad, no un histórico.

Una ejecución que empieza antes de medianoche sigue esperando la carpeta del día anterior hasta terminar o alcanzar timeout; una nueva ejecución usará su propia fecha inicial. No hay selector de fechas históricas en el JSON. La solución supone una entrega completa por día.

## Diagnóstico

| Síntoma | Revisar | Acción |
|---|---|---|
| DAG no aparece | Bucket real del entorno y DAG Import Errors | Confirmar /dags, sincronización y nombre de archivo |
| Invalid arguments gcp_conn_id en sensor | Firma del sensor | Usar google_cloud_conn_id; BigQuery mantiene gcp_conn_id |
| Variable inexistente | Key ecommerce_config_clinares | Crear JSON válido antes de ejecutar |
| Template UndefinedError | Campos obligatorios | Comparar con configuración documentada |
| Sensores en espera/timeout | Ruta renderizada, nombre y fecha en Lima | Subir los tres CSV a esa ruta exacta |
| Access Denied | Cuenta de servicio de Composer | Revisar IAM en proyecto, bucket y datasets |
| Not found tabla o SP | Proyecto/datasets y ejecución manual de setup | Ejecutar DDL primero, SP después |
| Error de ubicación | Dataset, bucket y location | Usar ubicaciones compatibles y coincidentes |
| ASSERT falla en silver | Campos vacíos, conversión, claves o referencias | Ver logs del CALL y corregir origen |
| ASSERT falla en gold | Reconciliación y dimensiones | Revisar silver y logs de la rutina |
| Modo automático omite entrega | Última identidad guardada | Es esperado si el día ya terminó correctamente |

## Reintentos y correcciones

1. Consultar logs de la tarea que falló; no comenzar eliminando tablas.
2. Esperar que la ejecución termine antes de cambiar archivos o configuración.
3. Si fue un problema de permisos/infraestructura, corregirlo y limpiar las tareas necesarias desde Airflow.
4. Si cambió el origen, reprocesar la entrega completa para mantener consistencia entre capas.
5. En modo automático, retirar el control del último éxito cuando se necesite reprocesar el día actual.
6. Reconciliar métricas y guardar evidencia del run_id y commit probado.

Para fallos de gold con silver correcto puede bastar reintentar gold; si se modifica el CSV, repetir desde bronze. Los reintentos mantienen la fecha de inicio de la ejecución mientras sea la misma ejecución activa; una nueva ejecución usará su nueva fecha. Revisar siempre las rutas renderizadas antes de reprocesar alrededor de medianoche.

## Cambios que requieren atención

- Cambiar un esquema requiere ALTER TABLE manual; IF NOT EXISTS no migra tablas.
- Renombrar DAG requiere retirar el Python anterior para evitar dos procesos escribiendo lo mismo.
- Los DAGs de alumnos comparten cuenta de servicio; sufijos no equivalen a aislamiento de permisos.
- max_active_runs=1 limita cada DAG, no la concurrencia total del aula.

## Revertir un cambio de código

Pausar el DAG y esperar su ejecución activa. Recuperar una versión anterior conocida desde Git, publicarla en la misma ruta y revisar importación antes de reactivar. Revertir el Python no restaura datos ni esquemas: evaluar por separado los cambios SQL y conservar evidencia de las pruebas.

---

[🏠 Proyecto y arquitectura](../README.md) · [⚙️ Configuración](01_configuracion.md) · [🚀 Despliegue](02_despliegue.md) · [🛠️ Operación](04_operacion.md)
