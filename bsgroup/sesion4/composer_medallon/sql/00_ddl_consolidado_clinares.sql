
-- DDL MANUAL: ejecutar antes de crear SP y antes de activar el DAG.
-- BigQuery crea los datasets; la cuenta de Composer requiere permiso para ello.
CREATE SCHEMA IF NOT EXISTS `bsgroup-dev-test-1.bronze_clinares` OPTIONS(location='US');
CREATE SCHEMA IF NOT EXISTS `bsgroup-dev-test-1.silver_clinares` OPTIONS(location='US');
CREATE SCHEMA IF NOT EXISTS `bsgroup-dev-test-1.gold_clinares` OPTIONS(location='US');

-- DDL: estructura explicita. IF NOT EXISTS conserva tablas y datos existentes.
-- Si se cambia el esquema, aplicar una migracion ALTER TABLE por separado.

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.bronze_clinares.clientes` (
  cliente_id STRING,
  nombre_completo STRING,
  email STRING,
  telefono STRING,
  ciudad STRING,
  segmento STRING,
  fecha_registro STRING,
  activo STRING
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.bronze_clinares.productos` (
  producto_id STRING,
  nombre_producto STRING,
  categoria STRING,
  marca STRING,
  precio_unitario STRING,
  costo_unitario STRING,
  stock_actual STRING,
  disponible STRING
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.bronze_clinares.transacciones` (
  transaccion_id STRING,
  fecha_transaccion STRING,
  cliente_id STRING,
  producto_id STRING,
  cantidad STRING,
  precio_unitario STRING,
  descuento_monto STRING,
  monto_total STRING,
  metodo_pago STRING,
  canal_venta STRING,
  estado STRING
);

-- DDL: estructura explicita. IF NOT EXISTS conserva tablas y datos existentes.
-- Si se cambia el esquema, aplicar una migracion ALTER TABLE por separado.

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.silver_clinares.clientes` (
  cliente_id STRING,
  nombre_completo STRING,
  email STRING,
  telefono STRING,
  ciudad STRING,
  segmento STRING,
  fecha_registro DATE,
  activo BOOL
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.silver_clinares.productos` (
  producto_id STRING,
  nombre_producto STRING,
  categoria STRING,
  marca STRING,
  precio_unitario NUMERIC,
  costo_unitario NUMERIC,
  stock_actual INT64,
  disponible BOOL
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.silver_clinares.transacciones` (
  transaccion_id STRING,
  fecha_transaccion DATETIME,
  cliente_id STRING,
  producto_id STRING,
  cantidad INT64,
  precio_unitario NUMERIC,
  descuento_monto NUMERIC,
  monto_total NUMERIC,
  metodo_pago STRING,
  canal_venta STRING,
  estado STRING
);

-- DDL: estructura explicita. IF NOT EXISTS conserva tablas y datos existentes.
-- Si se cambia el esquema, aplicar una migracion ALTER TABLE por separado.

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.gold_clinares.dim_cliente` (
  cliente_id STRING,
  nombre_completo STRING,
  email STRING,
  telefono STRING,
  ciudad STRING,
  segmento STRING,
  fecha_registro DATE,
  activo BOOL
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.gold_clinares.dim_producto` (
  producto_id STRING,
  nombre_producto STRING,
  categoria STRING,
  marca STRING,
  precio_unitario NUMERIC,
  costo_unitario NUMERIC,
  stock_actual INT64,
  disponible BOOL
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.gold_clinares.dim_fecha` (
  fecha_id INT64,
  fecha DATE,
  anio INT64,
  mes INT64,
  dia INT64,
  trimestre INT64
);

CREATE TABLE IF NOT EXISTS `bsgroup-dev-test-1.gold_clinares.fact_ventas` (
  transaccion_id STRING,
  cliente_id STRING,
  producto_id STRING,
  fecha_id INT64,
  fecha DATE,
  fecha_transaccion DATETIME,
  cantidad INT64,
  precio_unitario NUMERIC,
  importe_bruto NUMERIC,
  descuento_monto NUMERIC,
  importe_neto NUMERIC,
  metodo_pago STRING,
  canal_venta STRING,
  estado STRING
)
PARTITION BY fecha;

-- Sin pedido_id no se puede calcular cantidad de pedidos ni ticket por pedido.
-- El ticket de este ejercicio es por transaccion completada.
CREATE OR REPLACE VIEW `bsgroup-dev-test-1.gold_clinares.kpi_ventas_diarias` AS
SELECT fecha, COUNT(*) AS transacciones_completadas, SUM(cantidad) AS unidades_vendidas,
  SUM(importe_bruto) AS ventas_brutas, SUM(descuento_monto) AS descuentos,
  SUM(importe_neto) AS ventas_netas,
  SAFE_DIVIDE(SUM(importe_neto), COUNT(*)) AS ticket_promedio_transaccion,
  COUNT(DISTINCT cliente_id) AS clientes_compradores
FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas`
WHERE estado = 'COMPLETADO' GROUP BY fecha;

CREATE OR REPLACE VIEW `bsgroup-dev-test-1.gold_clinares.kpi_ventas_producto` AS
SELECT p.producto_id, p.nombre_producto, p.categoria,
  SUM(f.cantidad) AS unidades_vendidas, SUM(f.importe_neto) AS ventas_netas
FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas` f
JOIN `bsgroup-dev-test-1.gold_clinares.dim_producto` p USING(producto_id)
WHERE f.estado = 'COMPLETADO'
GROUP BY p.producto_id, p.nombre_producto, p.categoria;

CREATE OR REPLACE VIEW `bsgroup-dev-test-1.gold_clinares.kpi_ventas_cliente` AS
SELECT c.cliente_id, c.nombre_completo, c.segmento, c.ciudad,
  COUNT(*) AS transacciones_completadas, SUM(f.importe_neto) AS ventas_netas
FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas` f
JOIN `bsgroup-dev-test-1.gold_clinares.dim_cliente` c USING(cliente_id)
WHERE f.estado = 'COMPLETADO'
GROUP BY c.cliente_id, c.nombre_completo, c.segmento, c.ciudad;