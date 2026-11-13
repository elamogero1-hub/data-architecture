# Contribuir al proyecto

[README](README.md) · [Convenciones de documentación](docs/06_documentacion.md)

## Flujo de trabajo

1. Partir de la rama integrada y crear una rama con propósito claro.
2. Mantener cambios pequeños: código, SQL y documentación relacionados en el mismo PR.
3. Para otro alumno, adaptar su clon y publicar un DAG con identificador único, sin sobrescribir el DAG ajeno.
4. Si cambia sql o config, revisar coherencia entre SQL, JSON y documentación.
5. Ejecutar verificar_local.py y documentar su resultado.
6. Abrir el PR con problema, cambio, validación local y validación pendiente en nube.

Se mantiene un único ejemplo versionado: clinares. No añadir copias completas de otros alumnos ni resultados generados. No copiar un segundo Python con el mismo dag_id dentro de dags.

## Criterios de revisión

- Preservar DDL manual, cargas bronze con operadores y SP solo para silver/gold.
- Configuración JSON sin credenciales y sin fecha_carga/lote.
- Fecha derivada del inicio de ejecución en America/Lima.
- Tres sensores antes de las tres cargas; silver después de todas ellas.
- Nombres de alumno y datasets sin colisiones.
- Guías con enlaces relativos y comandos vigentes.
- No afirmar despliegue o pruebas reales que no se hayan realizado.

## Validación local

Desde composer_medallon:

```powershell
python -m pip install -r requirements-local.txt
python verificar_local.py
```

La verificación usa dobles locales para el grafo; los cambios de importación o de proveedor requieren además revisar DAG Import Errors y ejecutar en Composer.
