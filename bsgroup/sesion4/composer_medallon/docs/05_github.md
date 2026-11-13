# Publicar el código y la documentación en GitHub

[Volver al README](../README.md) · [Buenas prácticas](06_documentacion.md)

## 1. Identificar la raíz del repositorio

La estructura preparada utiliza esta raíz:

```text
repositorio/
├── README.md
├── .gitignore
├── .gitattributes
└── composer_medallon/
    ├── README.md
    ├── docs/
    ├── dags/
    └── ...
```

Abrir PowerShell en la carpeta que contiene composer_medallon, no dentro de dags. En el workspace original, esa carpeta es Sesion 3 - Arquitectura de proyectos. Comprobar:

```powershell
git rev-parse --show-toplevel
git status --short
git remote -v
```

En el momento de preparar esta guía, el workspace ya tenía Git inicializado, sin commits ni remoto. Si trabajas con una copia nueva y git rev-parse indica que no es un repositorio, ejecutar git init. No crear otro .git anidado dentro de composer_medallon si quieres mantener esta estructura.

## 2. Revisar qué se publicará

El .gitignore preparado excluye cachés, entornos virtuales, ZIP, .env y nombres habituales de claves. No excluye todos los JSON: los archivos config del ejercicio son necesarios y no contienen credenciales.

Revisar manualmente el contenido: no publicar tokens, contraseñas ni claves de servicio. Los IDs de proyecto y nombres de buckets son configuración, no credenciales. Los CSV contienen nombres, emails y teléfonos: confirmar que son datos autorizados para publicación; si no corresponde hacerlos públicos, usar repositorio privado o sustituirlos por ejemplos aprobados y actualizar las cifras esperadas.

La carpeta sql contiene la única versión de DDL y SP, ejecutable directamente en BigQuery. Si cambia un identificador o esquema, actualizar estos SQL y la configuración/documentación relacionada. No se versionan copias de alumnos ni resultados generados.

## 3. Verificar el proyecto

Desde la raíz:

```powershell
python -m pip install -r ./composer_medallon/requirements-local.txt
python ./composer_medallon/verificar_local.py
```

Abrir el preview Markdown del README y comprobar enlaces y diagramas. Los resultados locales no prueban la ejecución real en Composer.

## 4. Crear el repositorio remoto

Abrir [Nuevo repositorio en GitHub](https://github.com/new).

1. Elegir cuenta u organización y nombre, por ejemplo airflow-composer-medallon.
2. Seleccionar visibilidad según la política del aula y los datos que se publicarán.
3. Para este primer push, crear el repositorio vacío: sin README, .gitignore ni licencia generados por la web, porque el README y .gitignore ya están preparados localmente.
4. Copiar la URL HTTPS que proporciona GitHub. Ejemplo de formato: https://github.com/OWNER/airflow-composer-medallon.git.

La licencia es una decisión del titular: añadir una licencia solo cuando estén definidos los permisos de uso y de los datos.

## 5. Crear el primer commit

Desde la raíz del repositorio:

```powershell
git add README.md .gitignore .gitattributes composer_medallon
git status --short
git diff --cached --stat
git diff --cached
```

Revisar el diff y confirmar que no contiene archivos inesperados. Después:

```powershell
git commit -m "Documenta arquitectura medallon y despliegue en Composer"
git branch -M main
```

Este ejemplo usa main para el primer repositorio vacío. Si trabajas en un repositorio con historial o políticas existentes, conservar sus convenciones. Si Git pide identidad, configurar user.name y user.email a nivel de este repositorio con tus datos, sin copiar identidades ajenas.

## 6. Conectar y publicar

Reemplazar OWNER y el nombre del repositorio por los reales:

```powershell
git remote add origin https://github.com/OWNER/airflow-composer-medallon.git
git remote -v
git push -u origin main
```

Autenticarse con el método corporativo o con el gestor de credenciales de Git. No escribir tokens dentro de la URL ni de scripts del repositorio. Si origin ya existe, verificarlo antes de cambiarlo. Si el remoto tiene commits, revisar y conciliar el historial; no usar push --force para resolver automáticamente el rechazo.

## 7. Revisar la publicación

En GitHub comprobar:

- README de raíz visible y navegación al proyecto.
- Guías Markdown accesibles mediante enlaces relativos.
- Diagramas Mermaid y bloques de código legibles.
- DAG, SQL y JSON coincidentes con la documentación.
- Ausencia de ZIP, cachés y credenciales.

La publicación del código no publica el DAG en Composer. Para desplegarlo, seguir la [guía de Google Cloud](02_despliegue.md). No se añadió un pipeline de CI/CD automático en esta entrega.

## 8. Mantener los cambios

Para próximos cambios:

```powershell
git switch -c codex/actualizar-documentacion
```

Cambiar código y documentos juntos, verificar, revisar diff, crear commit y publicar la rama. Abrir un Pull Request que describa qué cambia, cómo se probó y qué falta validar en nube. Evitar ramas por alumno si cada alumno ya tiene su carpeta y las normas del curso requieren un solo flujo de integración.

## Referencias

- [Publicar un repositorio local](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
- [Administrar remotos](https://docs.github.com/en/get-started/git-basics/managing-remote-repositories).
- [README y enlaces relativos](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
