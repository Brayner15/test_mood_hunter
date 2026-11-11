-- =============================================================================
-- Tablero de solicitudes - esquema MySQL 8 + datos de prueba
--
-- Se ejecuta automáticamente la primera vez que se inicializa el contenedor
-- (docker-entrypoint-initdb.d). También se puede ejecutar a mano:
--   mysql -u root -p < db/schema.sql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS solicitudes
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE solicitudes;

-- ---------------------------------------------------------------------------
-- Catálogo de estados.
-- `code` es el identificador público y estable que expone la API; el id
-- autoincremental es un detalle interno de la base de datos.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS statuses (
  id          TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code        VARCHAR(30)      NOT NULL,
  label       VARCHAR(60)      NOT NULL,
  sort_order  TINYINT UNSIGNED NOT NULL,
  is_final    BOOLEAN          NOT NULL DEFAULT FALSE,
  PRIMARY KEY (id),
  UNIQUE KEY uq_statuses_code (code),
  UNIQUE KEY uq_statuses_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Solicitudes. Las transiciones de estado se validan en el dominio de la
-- aplicación; la FK garantiza que nunca quede un status_id inválido.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS requests (
  id          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  title       VARCHAR(150)     NOT NULL,
  description TEXT             NULL,
  status_id   TINYINT UNSIGNED NOT NULL,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_requests_status (status_id),
  KEY idx_requests_created_at (created_at),
  CONSTRAINT fk_requests_status
    FOREIGN KEY (status_id) REFERENCES statuses (id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catálogo de estados (idempotente)
-- ---------------------------------------------------------------------------
INSERT INTO statuses (code, label, sort_order, is_final) VALUES
  ('created',     'Creada',      1, FALSE),
  ('in_review',   'En revisión', 2, FALSE),
  ('in_progress', 'En progreso', 3, FALSE),
  ('paused',      'Pausada',     4, FALSE),
  ('done',        'Finalizada',  5, TRUE)
ON DUPLICATE KEY UPDATE
  label = VALUES(label),
  sort_order = VALUES(sort_order),
  is_final = VALUES(is_final);

-- ---------------------------------------------------------------------------
-- Datos de prueba: 12 solicitudes repartidas en todos los estados.
-- Se insertan solo si la tabla está vacía, para poder re-ejecutar el script.
-- ---------------------------------------------------------------------------
INSERT INTO requests (title, description, status_id, created_at, updated_at)
SELECT
  seed.title,
  seed.description,
  s.id,
  seed.created_at,
  seed.updated_at
FROM (
  SELECT 'Migrar formulario de contacto' AS title,
         'Reemplazar el formulario actual por el nuevo componente accesible.' AS description,
         'created' AS status_code,
         NOW() - INTERVAL 1 DAY AS created_at,
         NOW() - INTERVAL 1 DAY AS updated_at
  UNION ALL SELECT 'Revisar política de privacidad',
         'Actualizar el texto legal según la nueva normativa de datos.',
         'created',
         NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 2 DAY
  UNION ALL SELECT 'Añadir filtro por fecha en reportes',
         'Permitir filtrar el reporte mensual por rango de fechas.',
         'created',
         NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 3 DAY
  UNION ALL SELECT 'Corregir error 500 al exportar CSV',
         'El endpoint de exportación falla cuando hay más de 10.000 filas.',
         'in_review',
         NOW() - INTERVAL 6 DAY, NOW() - INTERVAL 4 DAY
  UNION ALL SELECT 'Documentar endpoints de autenticación',
         'Agregar ejemplos de request/response en la documentación interna.',
         'in_review',
         NOW() - INTERVAL 8 DAY, NOW() - INTERVAL 5 DAY
  UNION ALL SELECT 'Implementar paginación en el listado',
         'Añadir parámetros page y page_size al listado de solicitudes.',
         'in_progress',
         NOW() - INTERVAL 10 DAY, NOW() - INTERVAL 2 DAY
  UNION ALL SELECT 'Optimizar consulta de solicitudes por estado',
         'Agregar índice compuesto y revisar el plan de ejecución.',
         'in_progress',
         NOW() - INTERVAL 12 DAY, NOW() - INTERVAL 3 DAY
  UNION ALL SELECT 'Configurar monitorización de errores',
         'Integrar Sentry en backend y frontend con entorno de staging.',
         'in_progress',
         NOW() - INTERVAL 14 DAY, NOW() - INTERVAL 1 DAY
  UNION ALL SELECT 'Rediseñar pantalla de detalle',
         'Trabajo pausado a la espera de la validación de diseño.',
         'paused',
         NOW() - INTERVAL 20 DAY, NOW() - INTERVAL 9 DAY
  UNION ALL SELECT 'Migrar imágenes a almacenamiento externo',
         'Pausada hasta confirmar el proveedor y los costos.',
         'paused',
         NOW() - INTERVAL 25 DAY, NOW() - INTERVAL 15 DAY
  UNION ALL SELECT 'Desplegar entorno de staging',
         'Entorno creado y validado por el equipo de QA.',
         'done',
         NOW() - INTERVAL 30 DAY, NOW() - INTERVAL 18 DAY
  UNION ALL SELECT 'Actualizar dependencias de seguridad',
         'Parches aplicados y verificación de vulnerabilidades completada.',
         'done',
         NOW() - INTERVAL 35 DAY, NOW() - INTERVAL 20 DAY
) AS seed
JOIN statuses s ON s.code = seed.status_code
WHERE NOT EXISTS (SELECT 1 FROM requests);
