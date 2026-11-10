# -*- coding: utf-8 -*-
"""
Генератор примера информационной модели для выделенного участка МН (рис. 3)
с двумя параллельными ТУ. Формирует:
  - task1_section.json  — дерево объектов (состав) + связи (поток, использование, размещение)
  - task1_data.sql      — те же данные в виде INSERT для PostgreSQL (DDL — в task1_schema.sql)
Запуск: python generate_model.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

OBJECT_TYPES = [
    # code, name, description
    ("MT", "Магистральный трубопровод", "Корень иерархии"),
    ("SITE", "Технологическая площадка", "Площадка, на которой размещены НПС разных ТУ и общий РП (напр. ЛПДС)"),
    ("TU", "Технологический участок", "Перекачка «из резервуара в резервуар»"),
    ("GNPS", "Головная НПС", "Начало ТУ; НПС + ПНС + (ссылка на) РП"),
    ("NPS", "Промежуточная НПС", "Поддержание давления на ТУ"),
    ("LU", "Линейный участок (ЛЧ)", "Труба между соседними НПС/КП"),
    ("KP", "Контрольный пункт ЛЧ", "Через 10-30 км: линейная задвижка + 2 датчика давления"),
    ("END", "Конечный пункт ТУ", "Конец ТУ, РП приема"),
    ("RP", "Резервуарный парк", ""),
    ("RVS", "Резервуар", "Резервуар вертикальный стальной"),
    ("PNS", "Подпорная насосная станция", "1..10 параллельных ПА"),
    ("PA", "Подпорный агрегат", ""),
    ("NS", "Насосная станция (магистральная)", "4 последовательных МНА"),
    ("MNA", "Магистральный насосный агрегат", ""),
    ("OK", "Обратный клапан", ""),
    ("SARD", "Система автоматического регулирования давления", "2 параллельные заслонки"),
    ("SARD_LINE", "Нитка САРД", ""),
    ("ZASL", "Регулирующая заслонка", ""),
    ("FGU_BLOCK", "Блок фильтров-грязеуловителей", ""),
    ("FGU", "Фильтр-грязеуловитель", ""),
    ("KPP_SOD", "Камера пуска-приема СОД", "Вход/выход НПС"),
    ("KAM_PRIEM", "Камера приема СОД", ""),
    ("KAM_PUSK", "Камера пуска СОД", ""),
    ("ZD", "Задвижка", ""),
    ("DD", "Датчик давления", ""),
]

# Допустимый состав: родительский тип -> дочерний тип, min, max (None = без ограничения)
TYPE_RULES = [
    ("MT", "TU", 1, None), ("MT", "SITE", 0, None),
    ("SITE", "RP", 0, None),
    ("TU", "GNPS", 1, 1), ("TU", "NPS", 0, None), ("TU", "LU", 1, None), ("TU", "END", 1, 1),
    ("GNPS", "PNS", 1, 1), ("GNPS", "RP", 0, 1),
    ("GNPS", "KPP_SOD", 1, 1), ("GNPS", "FGU_BLOCK", 1, 1), ("GNPS", "NS", 1, 1), ("GNPS", "SARD", 1, 1),
    ("NPS", "KPP_SOD", 1, 1), ("NPS", "FGU_BLOCK", 1, 1), ("NPS", "NS", 1, 1), ("NPS", "SARD", 1, 1),
    ("PNS", "PA", 1, 10), ("PA", "ZD", 2, 2),
    ("NS", "MNA", 4, 4), ("MNA", "ZD", 2, 2), ("MNA", "OK", 1, 1),
    ("SARD", "SARD_LINE", 2, 2), ("SARD_LINE", "ZASL", 1, 1), ("SARD_LINE", "ZD", 2, 2),
    ("FGU_BLOCK", "FGU", 1, None), ("FGU", "ZD", 2, 2),
    ("KPP_SOD", "KAM_PRIEM", 1, 1), ("KPP_SOD", "KAM_PUSK", 1, 1), ("KPP_SOD", "ZD", 1, None),
    ("LU", "KP", 0, None), ("KP", "ZD", 1, 1), ("KP", "DD", 2, 2),
    ("END", "RP", 1, 1), ("RP", "RVS", 1, None),
]

# Км расстановки КП взяты с мнемосхемы (рис. 3, выделенный красным фрагмент)
TU1 = {
    "lu1": [282, 289, 304, 321, 336, 352, 365, 386, 387, 390, 392, 414, 437, 454, 478, 499],
    "lu2": [6, 30, 54, 58, 63, 91, 100, 108, 110, 114],
}
TU2 = {
    "lu1": [15, 17, 27, 29, 55, 80, 82, 99, 102, 116, 137, 149, 166],
    "lu2": [214, 236, 265, 279, 294, 295, 313, 320, 321, 328, 329, 351, 369, 389, 416],
}

objects = {}   # id -> obj
children = {}  # parent_id -> [ids]
links = []     # {from, to, type}


def add(oid, otype, name, parent=None, km=None, seq=None, params=None):
    obj = {"id": oid, "type": otype, "name": name, "parent_id": parent}
    if km is not None:
        obj["km"] = km
    if seq is not None:
        obj["seq"] = seq
    if params:
        obj["parameters"] = params
    objects[oid] = obj
    children.setdefault(parent, []).append(oid)
    return oid


def link(a, b, ltype):
    links.append({"from": a, "to": b, "type": ltype})


P_PRESS = [{"code": "P", "name": "Давление", "unit": "кгс/см2"}]
P_VALVE = [
    {"code": "POS", "name": "Положение (степень открытия)", "unit": "%"},
    {"code": "STATE", "name": "Состояние (откр/закр/промежут./авария)", "unit": "enum"},
]
P_PUMP = [
    {"code": "STATE", "name": "Состояние (работа/резерв/ремонт)", "unit": "enum"},
    {"code": "I", "name": "Ток электродвигателя", "unit": "А"},
]


def add_valve(oid, name, parent, seq):
    return add(oid, "ZD", name, parent, seq=seq, params=P_VALVE)


def add_rp(oid, name, parent, n_tanks):
    add(oid, "RP", name, parent)
    for i in range(1, n_tanks + 1):
        add("%s.RVS%d" % (oid, i), "RVS", "РВС-%d" % i, oid, seq=i,
            params=[{"code": "LEVEL", "name": "Уровень взлива", "unit": "мм"}])
    return oid


def add_station_core(st, seq_start=1, is_head=False):
    """Общий для ГНПС и промежуточной НПС состав (рис. 2): КПП СОД, ФГУ, НС, САРД."""
    s = seq_start
    # 3 — КПП СОД (вход и выход НПС)
    kpp = add(st + ".KPP_SOD", "KPP_SOD", "КПП СОД", st, seq=s); s += 1
    add(kpp + ".PRIEM", "KAM_PRIEM", "Камера приема СОД", kpp, seq=1)
    add(kpp + ".PUSK", "KAM_PUSK", "Камера пуска СОД", kpp, seq=2)
    for i in range(1, 7):
        add_valve("%s.ZD%d" % (kpp, i), "Задвижка %d узла КПП СОД" % i, kpp, 2 + i)
    # 4 — блок ФГУ: 2 параллельные нитки, задвижка - фильтр - задвижка
    fgu = add(st + ".FGU", "FGU_BLOCK", "Блок ФГУ", st, seq=s); s += 1
    for i in (1, 2):
        f = add("%s.F%d" % (fgu, i), "FGU", "ФГУ-%d" % i, fgu, seq=i,
                params=[{"code": "DP", "name": "Перепад давления на фильтре", "unit": "кгс/см2"}])
        add_valve(f + ".ZD_IN", "Задвижка на входе ФГУ-%d" % i, f, 1)
        add_valve(f + ".ZD_OUT", "Задвижка на выходе ФГУ-%d" % i, f, 2)
    # 1 — НС: 4 последовательно соединенных МНА, у каждого 2 задвижки и ОК на обводе
    ns = add(st + ".NS", "NS", "Магистральная насосная станция", st, seq=s); s += 1
    for i in range(1, 5):
        m = add("%s.MNA%d" % (ns, i), "MNA", "МНА-%d" % i, ns, seq=i, params=P_PUMP)
        add_valve(m + ".ZD_IN", "Задвижка на входе МНА-%d" % i, m, 1)
        add_valve(m + ".ZD_OUT", "Задвижка на выходе МНА-%d" % i, m, 2)
        add(m + ".OK", "OK", "Обратный клапан МНА-%d" % i, m, seq=3)
    for i in range(1, 4):
        link("%s.MNA%d" % (ns, i), "%s.MNA%d" % (ns, i + 1), "FLOW")  # последовательное соединение
    # 2 — САРД: 2 параллельные нитки, задвижка - заслонка - задвижка
    sard = add(st + ".SARD", "SARD", "САРД", st, seq=s); s += 1
    for i in (1, 2):
        ln = add("%s.L%d" % (sard, i), "SARD_LINE", "Нитка САРД %d" % i, sard, seq=i)
        add_valve(ln + ".ZD_IN", "Задвижка до заслонки %d" % i, ln, 1)
        add(ln + ".ZASL", "ZASL", "Регулирующая заслонка %d" % i, ln, seq=2, params=P_VALVE)
        add_valve(ln + ".ZD_OUT", "Задвижка после заслонки %d" % i, ln, 3)
    # Технологическая цепочка внутри НПС: вход КПП СОД -> ФГУ -> НС -> САРД -> выход КПП СОД.
    # КПП СОД одновременно вход и выход, поэтому, чтобы граф потока оставался ацикличным,
    # у промежуточной НПС фиксируем его как вход, а у ГНПС (где нефть приходит из РП) — как выход.
    if is_head:
        link(sard, kpp, "FLOW")
    else:
        link(kpp, fgu, "FLOW")
    link(fgu, ns, "FLOW")
    link(ns, sard, "FLOW")
    return s


def add_kp(lu, km, seq):
    kp = add("%s.KP%d" % (lu, km), "KP", "КП-%d" % km, lu, km=km, seq=seq)
    add(kp + ".DD_BEFORE", "DD", "Датчик давления до задвижки", kp, seq=1, params=P_PRESS)
    add_valve(kp + ".ZD", "Линейная задвижка", kp, 2)
    add(kp + ".DD_AFTER", "DD", "Датчик давления после задвижки", kp, seq=3, params=P_PRESS)
    link(kp + ".DD_BEFORE", kp + ".ZD", "FLOW")
    link(kp + ".ZD", kp + ".DD_AFTER", "FLOW")
    return kp


def build_tu(mt, n, kms, head_rp, head_site, nps_site, n_pa, n_end_tanks):
    tu = add("%s.TU%d" % (mt, n), "TU", "ТУ-%d" % n, mt, seq=n)
    seq = 1
    chain = [head_rp]  # технологическая цепочка ТУ «из резервуара в резервуар»

    # ГНПС: состав НПС + ПНС; РП — общий, поэтому только ссылка USES
    g = add("%s.GNPS%d" % (tu, n), "GNPS", "ГНПС-%d" % n, tu, seq=seq); seq += 1
    pns = add(g + ".PNS", "PNS", "Подпорная насосная станция", g, seq=1)
    for i in range(1, n_pa + 1):
        pa = add("%s.PA%d" % (pns, i), "PA", "ПА-%d" % i, pns, seq=i, params=P_PUMP)
        add_valve(pa + ".ZD_IN", "Задвижка на входе ПА-%d" % i, pa, 1)
        add_valve(pa + ".ZD_OUT", "Задвижка на выходе ПА-%d" % i, pa, 2)
    add_station_core(g, seq_start=2, is_head=True)
    link(g, head_rp, "USES")
    link(g, head_site, "LOCATED_AT")
    link(head_rp, pns, "FLOW")       # из РП нефть забирают подпорные агрегаты
    link(pns, g + ".FGU", "FLOW")    # и подают на ФГУ -> МНС
    chain.append(g)

    lu1 = add("%s.LU1" % tu, "LU", "ЛУ ГНПС-%d – НПС-2" % n, tu, seq=seq); seq += 1
    for i, km in enumerate(kms["lu1"], 1):
        chain.append(add_kp(lu1, km, i))

    nps = add("%s.NPS2" % tu, "NPS", "НПС-2 (ТУ-%d)" % n, tu, seq=seq); seq += 1
    add_station_core(nps)
    link(nps, nps_site, "LOCATED_AT")
    chain.append(nps)

    lu2 = add("%s.LU2" % tu, "LU", "ЛУ НПС-2 – КП ТУ-%d" % n, tu, seq=seq); seq += 1
    for i, km in enumerate(kms["lu2"], 1):
        chain.append(add_kp(lu2, km, i))

    end = add("%s.END" % tu, "END", "Конечный пункт ТУ-%d" % n, tu, seq=seq)
    rp_end = add_rp(end + ".RP", "РП конечного пункта ТУ-%d" % n, end, n_end_tanks)
    chain.append(rp_end)

    for a, b in zip(chain, chain[1:]):
        link(a, b, "FLOW")


# ---------------- сборка ----------------
MT = "MT1"
add(MT, "MT", "Магистральный трубопровод (выделенный участок рис. 3)")
head_site = add(MT + ".SITE_HEAD", "SITE", "Головная площадка (ГНПС-1, ГНПС-2)", MT, seq=1)
nps2_site = add(MT + ".SITE_NPS2", "SITE", "Площадка НПС-2 (НПС-2 ТУ-1, НПС-2 ТУ-2)", MT, seq=2)
# Общий РП: композиционно принадлежит площадке, а ГНПС ссылаются на него связью USES
shared_rp = add_rp(head_site + ".RP", "Общий РП головной площадки", head_site, 2)

build_tu(MT, 1, TU1, shared_rp, head_site, nps2_site, n_pa=3, n_end_tanks=2)
build_tu(MT, 2, TU2, shared_rp, head_site, nps2_site, n_pa=3, n_end_tanks=2)


# ---------------- выгрузка JSON (вложенное дерево) ----------------
def tree(oid):
    o = dict(objects[oid])
    o.pop("parent_id")
    kids = children.get(oid, [])
    if kids:
        o["children"] = [tree(k) for k in kids]
    return o


doc = {
    "model": "Участок МН с двумя параллельными ТУ (рис. 3)",
    "notes": [
        "children — композиция (строгое дерево: у каждого объекта ровно один родитель)",
        "links.FLOW — направление потока нефти (кто выше/ниже по течению)",
        "links.USES — объект использует общий (разделяемый) объект, не являясь его родителем",
        "links.LOCATED_AT — размещение объекта на технологической площадке",
        "km — километр трассы; нумерация км на ТУ может начинаться заново, поэтому порядок задается seq и FLOW",
    ],
    "object_types": [{"code": c, "name": n, "description": d} for c, n, d in OBJECT_TYPES],
    "type_rules": [{"parent": p, "child": c, "min": mn, "max": mx} for p, c, mn, mx in TYPE_RULES],
    "tree": tree(MT),
    "links": links,
}
with open(os.path.join(HERE, "task1_section.json"), "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)


# ---------------- выгрузка SQL ----------------
def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


order = []


def walk(oid):
    order.append(oid)
    for k in children.get(oid, []):
        walk(k)


walk(MT)
lines = ["-- Сгенерировано generate_model.py. Сначала выполнить task1_schema.sql", "BEGIN;"]
for c, n, d in OBJECT_TYPES:
    lines.append("INSERT INTO object_type(type_code, name, description) VALUES (%s, %s, %s);" % (q(c), q(n), q(d)))
for p, c, mn, mx in TYPE_RULES:
    lines.append("INSERT INTO object_type_rule(parent_type, child_type, min_count, max_count) VALUES (%s, %s, %s, %s);"
                 % (q(p), q(c), q(mn), q(mx)))
for oid in order:
    o = objects[oid]
    lines.append(
        "INSERT INTO object(object_code, type_code, name, parent_id, km, seq_no) VALUES "
        "(%s, %s, %s, (SELECT object_id FROM object WHERE object_code = %s), %s, %s);"
        % (q(oid), q(o["type"]), q(o["name"]), q(o["parent_id"]), q(o.get("km")), q(o.get("seq")))
    )
for oid in order:
    for p in objects[oid].get("parameters", []):
        lines.append(
            "INSERT INTO parameter(object_id, code, name, unit, label) VALUES "
            "((SELECT object_id FROM object WHERE object_code = %s), %s, %s, %s, %s);"
            % (q(oid), q(p["code"]), q(p["name"]), q(p["unit"]), q(oid + "|" + p["code"]))
        )
for l in links:
    lines.append(
        "INSERT INTO object_link(from_object_id, to_object_id, link_type) VALUES "
        "((SELECT object_id FROM object WHERE object_code = %s), (SELECT object_id FROM object WHERE object_code = %s), %s);"
        % (q(l["from"]), q(l["to"]), q(l["type"]))
    )
lines.append("COMMIT;")
with open(os.path.join(HERE, "task1_data.sql"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("objects:", len(objects), "links:", len(links),
      "params:", sum(len(o.get("parameters", [])) for o in objects.values()))
