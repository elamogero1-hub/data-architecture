
-- SP MANUALES: silver y gold. Bronze se carga con GCSToBigQueryOperator.

CREATE OR REPLACE PROCEDURE `bsgroup-dev-test-1.silver_clinares.sp_cargar_silver_clinares`()
BEGIN
  -- DML: refresco completo de silver en una transaccion.
  BEGIN TRANSACTION;
  -- DISTINCT elimina solo filas identicas despues de normalizar.
  -- Duplicados de clave con valores distintos detienen el control de calidad.
  -- SAFE_CAST convierte errores a NULL; el siguiente paso los detecta.
  DELETE FROM `bsgroup-dev-test-1.silver_clinares.clientes` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.silver_clinares.clientes` (cliente_id, nombre_completo, email, telefono, ciudad, segmento, fecha_registro, activo)
  SELECT DISTINCT
    UPPER(NULLIF(TRIM(cliente_id), '')) AS cliente_id,
    NULLIF(TRIM(nombre_completo), '') AS nombre_completo,
    LOWER(NULLIF(TRIM(email), '')) AS email,
    NULLIF(TRIM(telefono), '') AS telefono,
    NULLIF(TRIM(ciudad), '') AS ciudad,
    UPPER(NULLIF(TRIM(segmento), '')) AS segmento,
    SAFE_CAST(NULLIF(TRIM(fecha_registro), '') AS DATE) AS fecha_registro,
    SAFE_CAST(NULLIF(TRIM(activo), '') AS BOOL) AS activo
  FROM `bsgroup-dev-test-1.bronze_clinares.clientes`;
  
  DELETE FROM `bsgroup-dev-test-1.silver_clinares.productos` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.silver_clinares.productos` (producto_id, nombre_producto, categoria, marca, precio_unitario, costo_unitario, stock_actual, disponible)
  SELECT DISTINCT
    UPPER(NULLIF(TRIM(producto_id), '')) AS producto_id,
    NULLIF(TRIM(nombre_producto), '') AS nombre_producto,
    UPPER(NULLIF(TRIM(categoria), '')) AS categoria,
    NULLIF(TRIM(marca), '') AS marca,
    SAFE_CAST(NULLIF(TRIM(precio_unitario), '') AS NUMERIC) AS precio_unitario,
    SAFE_CAST(NULLIF(TRIM(costo_unitario), '') AS NUMERIC) AS costo_unitario,
    SAFE_CAST(NULLIF(TRIM(stock_actual), '') AS INT64) AS stock_actual,
    SAFE_CAST(NULLIF(TRIM(disponible), '') AS BOOL) AS disponible
  FROM `bsgroup-dev-test-1.bronze_clinares.productos`;
  
  DELETE FROM `bsgroup-dev-test-1.silver_clinares.transacciones` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.silver_clinares.transacciones` (transaccion_id, fecha_transaccion, cliente_id, producto_id, cantidad, precio_unitario, descuento_monto, monto_total, metodo_pago, canal_venta, estado)
  SELECT DISTINCT
    UPPER(NULLIF(TRIM(transaccion_id), '')) AS transaccion_id,
    SAFE_CAST(NULLIF(TRIM(fecha_transaccion), '') AS DATETIME) AS fecha_transaccion,
    UPPER(NULLIF(TRIM(cliente_id), '')) AS cliente_id,
    UPPER(NULLIF(TRIM(producto_id), '')) AS producto_id,
    SAFE_CAST(NULLIF(TRIM(cantidad), '') AS INT64) AS cantidad,
    SAFE_CAST(NULLIF(TRIM(precio_unitario), '') AS NUMERIC) AS precio_unitario,
    SAFE_CAST(NULLIF(TRIM(descuento_monto), '') AS NUMERIC) AS descuento_monto,
    SAFE_CAST(NULLIF(TRIM(monto_total), '') AS NUMERIC) AS monto_total,
    UPPER(NULLIF(TRIM(metodo_pago), '')) AS metodo_pago,
    UPPER(NULLIF(TRIM(canal_venta), '')) AS canal_venta,
    UPPER(NULLIF(TRIM(estado), '')) AS estado
  FROM `bsgroup-dev-test-1.bronze_clinares.transacciones`;
  
  -- ASSERT falla el job y bloquea gold: no se descartan errores silenciosamente.
  ASSERT (SELECT COUNT(*) > 0 FROM `bsgroup-dev-test-1.silver_clinares.clientes`) AS 'clientes: tabla vacia';
  ASSERT (SELECT COUNTIF(cliente_id IS NULL OR nombre_completo IS NULL OR email IS NULL OR telefono IS NULL OR ciudad IS NULL OR segmento IS NULL OR fecha_registro IS NULL OR activo IS NULL) = 0 FROM `bsgroup-dev-test-1.silver_clinares.clientes`) AS 'clientes: campo vacio o conversion invalida';
  ASSERT (SELECT COUNT(*) = COUNT(DISTINCT cliente_id) FROM `bsgroup-dev-test-1.silver_clinares.clientes`) AS 'clientes: clave duplicada';
  ASSERT (SELECT COUNT(*) > 0 FROM `bsgroup-dev-test-1.silver_clinares.productos`) AS 'productos: tabla vacia';
  ASSERT (SELECT COUNTIF(producto_id IS NULL OR nombre_producto IS NULL OR categoria IS NULL OR marca IS NULL OR precio_unitario IS NULL OR costo_unitario IS NULL OR stock_actual IS NULL OR disponible IS NULL) = 0 FROM `bsgroup-dev-test-1.silver_clinares.productos`) AS 'productos: campo vacio o conversion invalida';
  ASSERT (SELECT COUNT(*) = COUNT(DISTINCT producto_id) FROM `bsgroup-dev-test-1.silver_clinares.productos`) AS 'productos: clave duplicada';
  ASSERT (SELECT COUNT(*) > 0 FROM `bsgroup-dev-test-1.silver_clinares.transacciones`) AS 'transacciones: tabla vacia';
  ASSERT (SELECT COUNTIF(transaccion_id IS NULL OR fecha_transaccion IS NULL OR cliente_id IS NULL OR producto_id IS NULL OR cantidad IS NULL OR precio_unitario IS NULL OR descuento_monto IS NULL OR monto_total IS NULL OR metodo_pago IS NULL OR canal_venta IS NULL OR estado IS NULL) = 0 FROM `bsgroup-dev-test-1.silver_clinares.transacciones`) AS 'transacciones: campo vacio o conversion invalida';
  ASSERT (SELECT COUNT(*) = COUNT(DISTINCT transaccion_id) FROM `bsgroup-dev-test-1.silver_clinares.transacciones`) AS 'transacciones: clave duplicada';
  
  ASSERT (SELECT COUNT(*) = 0
  FROM `bsgroup-dev-test-1.silver_clinares.transacciones` t
  LEFT JOIN `bsgroup-dev-test-1.silver_clinares.clientes` c USING(cliente_id)
  LEFT JOIN `bsgroup-dev-test-1.silver_clinares.productos` p USING(producto_id)
  WHERE c.cliente_id IS NULL OR p.producto_id IS NULL) AS 'Relacion cliente/producto inexistente';
  ASSERT (SELECT COUNTIF(cantidad <= 0 OR precio_unitario < 0 OR descuento_monto < 0
    OR descuento_monto > cantidad * precio_unitario OR monto_total < 0
    OR ABS(monto_total - (cantidad * precio_unitario - descuento_monto)) > 0.01
    OR estado NOT IN ('COMPLETADO', 'PENDIENTE', 'ANULADO')) = 0
  FROM `bsgroup-dev-test-1.silver_clinares.transacciones`) AS 'Transaccion invalida';
  ASSERT (SELECT COUNTIF(precio_unitario < 0 OR costo_unitario < 0 OR stock_actual < 0) = 0
  FROM `bsgroup-dev-test-1.silver_clinares.productos`) AS 'Producto invalido';
  
  COMMIT TRANSACTION;
END;

CREATE OR REPLACE PROCEDURE `bsgroup-dev-test-1.gold_clinares.sp_cargar_gold_clinares`()
BEGIN
  -- DML: dimensiones y hechos se actualizan juntos.
  BEGIN TRANSACTION;
  -- Dimensiones tipo 1: el estado actual reemplaza al anterior.
  DELETE FROM `bsgroup-dev-test-1.gold_clinares.dim_cliente` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.gold_clinares.dim_cliente` (cliente_id, nombre_completo, email, telefono, ciudad, segmento, fecha_registro, activo)
  SELECT cliente_id, nombre_completo, email, telefono, ciudad, segmento, fecha_registro, activo FROM `bsgroup-dev-test-1.silver_clinares.clientes`;
  DELETE FROM `bsgroup-dev-test-1.gold_clinares.dim_producto` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.gold_clinares.dim_producto` (producto_id, nombre_producto, categoria, marca, precio_unitario, costo_unitario, stock_actual, disponible)
  SELECT producto_id, nombre_producto, categoria, marca, precio_unitario, costo_unitario, stock_actual, disponible FROM `bsgroup-dev-test-1.silver_clinares.productos`;
  
  DELETE FROM `bsgroup-dev-test-1.gold_clinares.dim_fecha` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.gold_clinares.dim_fecha` (fecha_id, fecha, anio, mes, dia, trimestre)
  SELECT CAST(FORMAT_DATE('%Y%m%d', fecha) AS INT64) AS fecha_id,
    fecha, EXTRACT(YEAR FROM fecha) AS anio, EXTRACT(MONTH FROM fecha) AS mes,
    EXTRACT(DAY FROM fecha) AS dia, EXTRACT(QUARTER FROM fecha) AS trimestre
  FROM UNNEST(GENERATE_DATE_ARRAY(
    (SELECT MIN(DATE(fecha_transaccion)) FROM `bsgroup-dev-test-1.silver_clinares.transacciones`),
    (SELECT MAX(DATE(fecha_transaccion)) FROM `bsgroup-dev-test-1.silver_clinares.transacciones`)
  )) AS fecha;
  
  -- Grano: una transaccion_id asociada a un cliente y un producto.
  -- Se conservan todos los estados para analizar pendientes y anulaciones.
  DELETE FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas` WHERE TRUE;
  INSERT INTO `bsgroup-dev-test-1.gold_clinares.fact_ventas` (transaccion_id, cliente_id, producto_id, fecha_id, fecha, fecha_transaccion, cantidad, precio_unitario, importe_bruto, descuento_monto, importe_neto, metodo_pago, canal_venta, estado)
  SELECT transaccion_id, cliente_id, producto_id,
    CAST(FORMAT_DATE('%Y%m%d', DATE(fecha_transaccion)) AS INT64) AS fecha_id,
    DATE(fecha_transaccion) AS fecha, fecha_transaccion, cantidad,
    precio_unitario, cantidad * precio_unitario AS importe_bruto,
    descuento_monto, monto_total AS importe_neto, metodo_pago, canal_venta, estado
  FROM `bsgroup-dev-test-1.silver_clinares.transacciones`;
  
  
  ASSERT (
    (SELECT COUNT(*) FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas`) =
    (SELECT COUNT(*) FROM `bsgroup-dev-test-1.silver_clinares.transacciones`)
  ) AS 'Gold debe conservar todas las transacciones';
  ASSERT (SELECT COUNT(*) = 0
  FROM `bsgroup-dev-test-1.gold_clinares.fact_ventas` f
  LEFT JOIN `bsgroup-dev-test-1.gold_clinares.dim_cliente` c USING(cliente_id)
  LEFT JOIN `bsgroup-dev-test-1.gold_clinares.dim_producto` p USING(producto_id)
  LEFT JOIN `bsgroup-dev-test-1.gold_clinares.dim_fecha` d USING(fecha_id)
  WHERE c.cliente_id IS NULL OR p.producto_id IS NULL OR d.fecha_id IS NULL
  ) AS 'Hechos sin dimension';
  ASSERT (
    (SELECT COALESCE(SUM(ventas_netas), 0) FROM `bsgroup-dev-test-1.gold_clinares.kpi_ventas_diarias`) =
    (SELECT COALESCE(SUM(monto_total), 0) FROM `bsgroup-dev-test-1.silver_clinares.transacciones` WHERE estado='COMPLETADO')
  ) AS 'Ventas netas deben reconciliar con silver';
  
  COMMIT TRANSACTION;
END;