# Buenas prácticas de documentación Markdown

[Volver al README](../README.md) · [Contribuir](../CONTRIBUTING.md)

## Objetivo y organización

Markdown (.md) es el formato principal de documentación del repositorio. El README debe explicar qué hace el proyecto, cómo empezar y dónde encontrar detalles. Las guías largas van en docs/ y se organizan por tarea: configuración, despliegue, arquitectura, operación y publicación.

Una sola fuente por decisión: configuración y significado de campos en 01_configuracion.md; secuencia de despliegue en 02_despliegue.md; fórmulas y grano en 03_arquitectura_modelo.md. Los demás documentos enlazan a esa fuente en lugar de repetir instrucciones que luego divergen.

## Convenciones de Markdown

- Un título H1 por archivo; H2 y H3 en orden sin saltos arbitrarios.
- Dejar línea en blanco antes y después de listas, tablas y bloques de código.
- Usar listas numeradas para pasos y tablas para comparaciones o mapeos.
- Etiquetar bloques con powershell, python, sql, json, text o mermaid.
- Usar nombres de archivo estables y sin espacios: 02_despliegue.md.
- Usar enlaces relativos para archivos internos, nunca C:/Users/... ni enlaces que dependan del equipo del autor.
- Dar títulos descriptivos a enlaces externos; evitar textos como clic aquí.
- Mantener JSON válido: comillas dobles, sin comentarios ni comas finales.
- Revisar el preview de GitHub después de modificar tablas o diagramas.

Ejemplo de enlace dentro de README.md:

```markdown
[Guía de despliegue](docs/02_despliegue.md)
```

Ejemplo desde docs/ hacia código:

```markdown
[DAG del alumno](../dags/dag_medallon_clinares.py)
```

## Qué debe explicar cada procedimiento

| Elemento | Ejemplo de este proyecto |
|---|---|
| Prerrequisitos | Permisos, Python, Composer existente |
| Punto de partida | PowerShell dentro de composer_medallon |
| Acción | Publicar un único Python en el bucket de código |
| Resultado esperado | DAG visible sin Import Errors |
| Validación | Ocho tareas y reconciliación de importes |
| Recuperación | Consultar logs, corregir causa y reprocesar |
| Límite | La prueba local no ejecuta BigQuery |

Los comandos deben ser copiables y mostrar claramente qué valores sustituir. Preferir ejemplos completos y concretos. Distinguir fecha de ejemplo de fecha calculada: YYYYMMDD viene de la ejecución en America/Lima, no de una Variable JSON. No inferir región Composer a partir de location US de BigQuery.

## Documentar decisiones y contratos de datos

Explicar la razón de decisiones que afectan al alumno: por qué bronze es STRING, por qué el ticket es por transacción, qué significa una entrega diaria y por qué el SP de bronze no existe. Definir grano, claves, tipos, filtros y fórmula de cada métrica. Cuando cambie una regla de negocio, cambiar también la cifra de referencia y la consulta que la valida.

## Mantener documentación y código juntos

En el mismo PR, actualizar lo que corresponda:

- DAG o task_id cambiado: despliegue y operación.
- Campo JSON cambiado: ejemplo y tabla de configuración.
- Esquema o SP cambiado: SQL, modelo y verificaciones.
- KPI cambiado: definición, consulta y resultado esperado.
- Ruta de Storage cambiada: configuración y comandos.
- Comportamiento cambiado: CHANGELOG.md.

La carpeta sql contiene la única fuente de DDL y SP; se edita directamente. El JSON de config es un ejemplo publicable de configuración sin credenciales; la Variable en Airflow debe mantenerse consistente de forma explícita. No mantener un PDF o Word como copia paralela de la documentación principal.

## Evidencia y compatibilidad

Registrar versiones de Composer, Airflow y proveedor Google después de probar en el entorno real. Distinguir comprobaciones locales, importación del DAG y ejecución de los jobs. No usar badges de pruebas o despliegue sin un proceso real que los respalde. No afirmar compatibilidad universal con versiones no probadas.

En el PR de despliegue, incluir commit probado, fecha, run_id y métricas reconciliadas. Evitar capturas con tokens o información personal. Las capturas pueden ayudar, pero no sustituir comandos ni pasos de texto accesibles y buscables.

## Revisión antes de integrar

- ¿Alguien nuevo puede completar los pasos con la documentación disponible?
- ¿Los enlaces internos resuelven a archivos versionados?
- ¿El JSON coincide con el código y omite fecha_carga/lote?
- ¿Se distinguen bucket de código y bucket de datos?
- ¿Se explican resultados y errores habituales?
- ¿Los SQL y el JSON usan los mismos identificadores y tipos?
- ¿Las limitaciones están descritas sin promesas de pruebas no realizadas?
- ¿Se revisó que los datos y archivos estén autorizados para publicación?

## Referencias oficiales

- [README en GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
- [Sintaxis Markdown de GitHub](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).
