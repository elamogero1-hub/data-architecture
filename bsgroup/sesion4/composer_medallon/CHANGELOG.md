# Historial de cambios

## Sin publicar — 2026-11-11

### Solución actual

- DAG dag_medallon_clinares con aislamiento de nombres por alumno.
- DDL manual de datasets, tablas y vistas.
- Bronze con GCSToBigQueryOperator y columnas STRING; SP solo para silver y gold.
- Variable JSON propia por alumno, sin fecha_carga ni lote.
- Carpeta YYYYMMDD calculada desde inicio de ejecución en America/Lima.
- Bloque automático opcional comentado con control de la última entrega exitosa.

### Documentación

- README de entrada y guías Markdown separadas por tarea.
- Pasos para publicar el repositorio en GitHub.
- Convenciones de documentación y contribución.
- Dependencias locales y exclusiones Git preparadas.

### Validación

Verificación local disponible. Importación y ejecución real en Composer/BigQuery pendientes de registrar; publicación remota en GitHub no realizada en esta entrega.

### Depuración del repositorio

- Eliminadas las copias completas de entregas de alumnos y los scripts de generación.
- SQL unificados en sql/, sin plantillas ni duplicados renderizados.
- Conservado un solo JSON para copiar como Variable de Airflow.
- El verificador ya no depende de mtorres ni escribe resultado_esperado.json.
- Actualizadas las guías y los enlaces para la estructura mínima.
