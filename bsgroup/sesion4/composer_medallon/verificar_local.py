"""Validacion local de archivos, reglas de negocio y configuracion; no ejecuta BigQuery."""
import ast
import csv
import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
source = (ROOT / "dags/dag_medallon_clinares.py").read_text(encoding="utf-8")
ast.parse(source)
# Esquema esperado de los CSV del ejercicio.
schemas = {'clientes': ['cliente_id', 'nombre_completo', 'email', 'telefono', 'ciudad', 'segmento', 'fecha_registro', 'activo'], 'productos': ['producto_id', 'nombre_producto', 'categoria', 'marca', 'precio_unitario', 'costo_unitario', 'stock_actual', 'disponible'], 'transacciones': ['transaccion_id', 'fecha_transaccion', 'cliente_id', 'producto_id', 'cantidad', 'precio_unitario', 'descuento_monto', 'monto_total', 'metodo_pago', 'canal_venta', 'estado']}
rows = {}
for name, columns in schemas.items():
    with (ROOT / "data" / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == columns, f"Cabecera inesperada: {name}"
        rows[name] = list(reader)
    assert rows[name], f"Tabla vacia: {name}"
    assert all(all(r[c] is not None and r[c].strip() for c in columns) for r in rows[name])
    assert len({r[columns[0]] for r in rows[name]}) == len(rows[name]), name
clientes = {r["cliente_id"] for r in rows["clientes"]}
productos = {r["producto_id"] for r in rows["productos"]}
for r in rows["clientes"]:
    date.fromisoformat(r["fecha_registro"])
    assert r["activo"].lower() in ("true", "false")
for r in rows["productos"]:
    assert D(r["precio_unitario"]) >= 0 and D(r["costo_unitario"]) >= 0
    assert int(r["stock_actual"]) >= 0
    assert r["disponible"].lower() in ("true", "false")
for r in rows["transacciones"]:
    assert r["cliente_id"] in clientes and r["producto_id"] in productos
    datetime.fromisoformat(r["fecha_transaccion"])
    q, price, discount, total = int(r["cantidad"]), D(r["precio_unitario"]), D(r["descuento_monto"]), D(r["monto_total"])
    assert q > 0 and price >= 0 and total >= 0 and 0 <= discount <= q * price
    assert abs(q * price - discount - total) <= D("0.01")
    assert r["estado"] in ("COMPLETADO", "PENDIENTE", "ANULADO")
# Probar el DAG y los SQL del unico ejemplo versionado.
for alumno, base in [("clinares", ROOT)]:
    dag_source = (base / f"dags/dag_medallon_{alumno}.py").read_text(encoding="utf-8")
    tree = ast.parse(dag_source)
    # Regresion del Broken DAG reportado en Composer: nombre real del argumento del sensor.
    sensor_calls = [node for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "GCSObjectExistenceSensor"]
    assert len(sensor_calls) == 1
    for call in sensor_calls:
        keywords = {kw.arg for kw in call.keywords}
        assert "google_cloud_conn_id" in keywords and "gcp_conn_id" not in keywords
        assert "dag" in keywords
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in (
                "CargaBigQueryJSONOperator", "ConsultaBigQueryJSONOperator"):
            assert any(kw.arg == "dag" for kw in node.keywords)
    cfg = json.loads((base / f"config/ecommerce_config_{alumno}.json").read_text(encoding="utf-8"))
    key = f"ecommerce_config_{alumno}"
    from types import SimpleNamespace
    from zoneinfo import ZoneInfo
    import datetime as datetime_module
    fecha_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "fecha_de_carga")
    fecha_namespace = {"ZoneInfo": ZoneInfo}
    exec(compile(ast.Module(body=[fecha_function], type_ignores=[]), "fecha", "exec"), fecha_namespace)
    fecha = fecha_namespace["fecha_de_carga"]
    run = SimpleNamespace(start_date=datetime_module.datetime(2026, 11, 11, 15, 0, tzinfo=datetime_module.timezone.utc))
    assert "fecha_carga" not in cfg
    assert fecha(run) == "20261111"
    assert fecha(SimpleNamespace(start_date=datetime_module.datetime(2026, 11, 12, 4, 59, tzinfo=datetime_module.timezone.utc))) == "20261111"
    assert fecha(SimpleNamespace(start_date=datetime_module.datetime(2026, 11, 12, 5, 0, tzinfo=datetime_module.timezone.utc))) == "20261112"
    context = {"params": {"config_key": key}, "var": {"json": {key: cfg}},
               "dag_run": run, "fecha_de_carga": fecha}
    env = Environment(loader=FileSystemLoader(str(base / "sql")), undefined=StrictUndefined)
    for file in (base / "sql").glob("*.sql"):
        rendered = env.from_string("{% include '" + file.name + "' %}").render(**context)
        assert "{{" not in rendered and "{%" not in rendered
        assert f"bronze_{alumno}" in rendered or f"silver_{alumno}" in rendered or f"gold_{alumno}" in rendered
    # Ejecutar unicamente la funcion pura que arma expresiones Jinja.
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "config")
    namespace = {"CONFIG_KEY": key}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "config", "exec"), namespace)
    for field, expected in cfg.items():
        assert env.from_string(namespace["config"](field)).render(**context) == expected
    landing = namespace["config"]("landing_prefix") + "/" + "{{ fecha_de_carga(dag_run) }}" + "/clientes.csv"
    assert env.from_string(landing).render(**context) == f"landing/{alumno}/20261111/clientes.csv"
    # Todos los CALL del DAG deben apuntar a los SP definidos por los consolidados.
    import re
    rendered_files = [env.get_template(file.name).render(**context)
                      for file in (base / "sql").glob("*.sql")]
    assert len(rendered_files) == 2
    definitions = set(re.findall(r"CREATE OR REPLACE PROCEDURE `([^`]+)`", "\n".join(rendered_files)))
    assert len(definitions) == 2
    ddl = env.get_template(f"00_ddl_consolidado_{alumno}.sql").render(**context)
    assert "CREATE OR REPLACE PROCEDURE" not in ddl
    assert ddl.count("CREATE TABLE IF NOT EXISTS") == 10
    assert ddl.count("CREATE OR REPLACE VIEW") == 3
    assert "CREATE " not in dag_source and "sql_task" not in dag_source
    assert "sp_cargar_bronze" not in dag_source and "sp_cargar_bronze" not in "\n".join(rendered_files)
    call_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "call_sp")
    namespace.update(ALUMNO=alumno, PROJECT_ID=namespace["config"]("project_id"),
                     query_task=lambda task_id, query: query)
    exec(compile(ast.Module(body=[call_function], type_ignores=[]), "call_sp", "exec"), namespace)
    for layer, procedure in [("silver", "sp_cargar_silver"), ("gold", "sp_cargar_gold")]:
        call = namespace["call_sp"](procedure, layer, procedure)
        rendered = env.from_string(call).render(**context)
        assert re.search(r"CALL `([^`]+)`", rendered).group(1) in definitions
    dml = env.get_template(f"01_sp_cargas_{alumno}.sql").render(**context)
    assert dml.count("BEGIN TRANSACTION;") == dml.count("COMMIT TRANSACTION;") == 2
    for block in dml.split("BEGIN TRANSACTION;")[1:]:
        assert "ASSERT " in block.split("COMMIT TRANSACTION;", 1)[0]
    # Construir el grafo con dobles locales: valida dependencias y configuracion,
    # sin afirmar compatibilidad de importacion con un proveedor no instalado.
    class LocalDAG:
        def __init__(self, **kwargs):
            self.tasks = {}
        def get_task(self, task_id):
            return self.tasks[task_id]
    class LocalOperator:
        template_fields = ()
        def __init__(self, task_id, dag, **kwargs):
            self.task_id, self.upstream, self.downstream = task_id, set(), set()
            self.__dict__.update(kwargs)
            dag.tasks[task_id] = self
        def __rshift__(self, other):
            self.downstream.add(other.task_id)
            other.upstream.add(self.task_id)
            return other
    import datetime as datetime_module
    local = {"DAG": LocalDAG, "GCSObjectExistenceSensor": LocalOperator,
             "GCSToBigQueryOperator": LocalOperator, "BigQueryInsertJobOperator": LocalOperator,
             "datetime": datetime_module, "re": re, "ZoneInfo": ZoneInfo}
    without_imports = ast.Module(body=[node for node in tree.body
                                      if not isinstance(node, (ast.Import, ast.ImportFrom))], type_ignores=[])
    exec(compile(without_imports, "dag_local", "exec"), local)
    tasks = local["dag"].tasks
    assert len(tasks) == 8
    expected_sensors = {f"esperar_{name}" for name in schemas}
    expected_loads = {f"bronze_{name}" for name in schemas}
    for name, columns in schemas.items():
        load = tasks[f"bronze_{name}"]
        assert load.upstream == expected_sensors
        assert load.downstream == {"sp_cargar_silver"}
        assert load.autodetect is False and load.max_bad_records == 0
        assert load.create_disposition == "CREATE_NEVER" and load.write_disposition == "WRITE_TRUNCATE"
        assert [field["name"] for field in load.schema_fields] == columns
        assert all(field["type"] == "STRING" for field in load.schema_fields)
        assert env.from_string(load.destination_project_dataset_table).render(**context) == f"{cfg['project_id']}.bronze_{alumno}.{name}"
        assert env.from_string(load.source_objects[0]).render(**context) == f"landing/{alumno}/20261111/{name}.csv"
    assert tasks["sp_cargar_silver"].upstream == expected_loads
    assert tasks["sp_cargar_gold"].upstream == {"sp_cargar_silver"}
    changed = dict(cfg, project_id="otro-proyecto")
    alternate = dict(context, var={"json": {key: changed}},
                     dag_run=SimpleNamespace(start_date=datetime_module.datetime(2026, 11, 12, 15, 0, tzinfo=datetime_module.timezone.utc)))
    assert env.from_string(landing).render(**alternate) == f"landing/{alumno}/20261112/clientes.csv"
    assert env.from_string(namespace["config"]("project_id")).render(**alternate) == "otro-proyecto"
    try:
        env.from_string(namespace["config"]("bucket")).render(var={"json": {}}, params=context["params"])
    except Exception as error:
        from jinja2 import UndefinedError
        assert isinstance(error, UndefinedError)
    else:
        raise AssertionError("Una key ausente debe fallar sin usar valores predeterminados")
completed = [r for r in rows["transacciones"] if r["estado"] == "COMPLETADO"]
net = sum((D(r["monto_total"]) for r in completed), D(0))
report = {"filas": {k: len(v) for k,v in rows.items()},
          "estados": dict(Counter(r["estado"] for r in rows["transacciones"])),
          "ventas_netas_completadas": str(net),
          "unidades_vendidas_completadas": sum(int(r["cantidad"]) for r in completed),
          "clientes_compradores_completados": len({r["cliente_id"] for r in completed}),
          "ticket_promedio_transaccion": str(net / len(completed)),
          "validacion": "Python, plantillas Jinja y reglas sobre CSV: OK. Sin ejecucion en Composer/BigQuery."}
print(json.dumps(report, indent=2, ensure_ascii=False))
