-- =====================================================================
-- Задание 1. Структура хранения информационной модели (ИМ) участка МН
-- СУБД: PostgreSQL 14+
-- =====================================================================

-- 1. Справочник типов объектов (классификатор)
CREATE TABLE object_type (
    type_code    varchar(32)  PRIMARY KEY,          -- 'TU', 'NPS', 'KP', 'ZD', ...
    name         varchar(200) NOT NULL,
    description  text
);

-- 2. Правила композиции: какой тип может быть дочерним для какого и в каком количестве.
--    Не дает «положить задвижку в резервуарный парк» и фиксирует нормативный состав
--    (НС = 4 МНА, ПНС = 1..10 ПА и т.д.)
CREATE TABLE object_type_rule (
    parent_type  varchar(32) NOT NULL REFERENCES object_type,
    child_type   varchar(32) NOT NULL REFERENCES object_type,
    min_count    int NOT NULL DEFAULT 0,
    max_count    int,                                -- NULL = без ограничения
    PRIMARY KEY (parent_type, child_type)
);

-- 3. Экземпляры объектов. parent_id — КОМПОЗИЦИЯ («входит в состав»): строгое дерево,
--    у каждого объекта ровно один родитель. Именно это поле отвечает на вопрос
--    «кто родитель / кто дочерний».
CREATE TABLE object (
    object_id    bigserial    PRIMARY KEY,
    object_code  varchar(200) NOT NULL UNIQUE,       -- устойчивый бизнес-код, напр. MT1.TU2.LU1.KP116
    type_code    varchar(32)  NOT NULL REFERENCES object_type,
    name         varchar(300) NOT NULL,
    parent_id    bigint       REFERENCES object(object_id),
    km           numeric(8,3),                       -- километр трассы (для объектов ЛЧ)
    seq_no       int,                                -- порядок среди «братьев» по ходу потока
    valid_from   timestamptz  NOT NULL DEFAULT now(),-- версионность: реконструкции, замены оборудования
    valid_to     timestamptz,
    attrs        jsonb        NOT NULL DEFAULT '{}'  -- паспортные данные (Ду, Ру, марка насоса...)
);
CREATE INDEX ix_object_parent ON object(parent_id);
CREATE INDEX ix_object_type   ON object(type_code);

-- 4. Связи, которые НЕ являются композицией (граф поверх дерева)
--    FLOW        — A -> B по ходу потока нефти (выше/ниже по течению)
--    USES        — A использует общий объект B (ГНПС-1 и ГНПС-2 используют общий РП)
--    LOCATED_AT  — A размещен на технологической площадке B
CREATE TABLE object_link (
    link_id         bigserial PRIMARY KEY,
    from_object_id  bigint      NOT NULL REFERENCES object(object_id),
    to_object_id    bigint      NOT NULL REFERENCES object(object_id),
    link_type       varchar(20) NOT NULL CHECK (link_type IN ('FLOW', 'USES', 'LOCATED_AT')),
    UNIQUE (from_object_id, to_object_id, link_type)
);
CREATE INDEX ix_link_to ON object_link(to_object_id, link_type);

-- 5. Параметры (сигналы) объектов — то, что потом имеет временные ряды.
--    Эта таблица — мост к Заданию 2: (object_id, parameter_id, label, nic)
CREATE TABLE parameter (
    parameter_id bigserial    PRIMARY KEY,
    object_id    bigint       NOT NULL REFERENCES object(object_id),
    code         varchar(32)  NOT NULL,              -- 'P', 'POS', 'STATE', ...
    name         varchar(200) NOT NULL,
    unit         varchar(20),
    label        varchar(300) UNIQUE,                -- имя/путь атрибута в исходной ИМ (PI AF)
    nic          varchar(100),                       -- идентификатор сигнала в ИС-источнике
    UNIQUE (object_id, code)
);

-- =====================================================================
-- Примеры запросов
-- =====================================================================

-- Q1. Все дочерние объекты (на любую глубину) технологического участка ТУ-2
-- WITH RECURSIVE sub AS (
--     SELECT object_id, object_code, name, type_code, 0 AS lvl
--     FROM object WHERE object_code = 'MT1.TU2'
--     UNION ALL
--     SELECT o.object_id, o.object_code, o.name, o.type_code, s.lvl + 1
--     FROM object o JOIN sub s ON o.parent_id = s.object_id
-- )
-- SELECT * FROM sub ORDER BY lvl;

-- Q2. Цепочка родителей для датчика давления до задвижки на КП-116 (ТУ-2)
-- WITH RECURSIVE up AS (
--     SELECT object_id, parent_id, name, type_code, 0 AS lvl
--     FROM object WHERE object_code = 'MT1.TU2.LU1.KP116.DD_BEFORE'
--     UNION ALL
--     SELECT o.object_id, o.parent_id, o.name, o.type_code, u.lvl + 1
--     FROM object o JOIN up u ON o.object_id = u.parent_id
-- )
-- SELECT lvl, type_code, name FROM up ORDER BY lvl;

-- Q3. Какие ГНПС используют общий РП головной площадки
-- SELECT f.name
-- FROM object_link l
-- JOIN object f ON f.object_id = l.from_object_id
-- JOIN object t ON t.object_id = l.to_object_id
-- WHERE l.link_type = 'USES' AND t.object_code = 'MT1.SITE_HEAD.RP';

-- Q4. Все объекты ниже по потоку от КП-387 на ТУ-1 (до конечного РП)
-- WITH RECURSIVE down AS (
--     SELECT o.object_id, o.name, 0 AS step
--     FROM object o WHERE o.object_code = 'MT1.TU1.LU1.KP387'
--     UNION ALL
--     SELECT o.object_id, o.name, d.step + 1
--     FROM down d
--     JOIN object_link l ON l.from_object_id = d.object_id AND l.link_type = 'FLOW'
--     JOIN object o ON o.object_id = l.to_object_id
-- )
-- SELECT step, name FROM down ORDER BY step;
