import sys
from xml.sax.saxutils import quoteattr as q
out=[];n=[0]
def nid():
    n[0]+=1; return f"c{n[0]}"
rows={}
CW=[50,125,100,45,170]; W=sum(CW)
def cell(rid,x,w,val,extra=''):
    out.append(f'<mxCell id="{nid()}" parent="{rid}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;whiteSpace=wrap;html=1;{extra}" value={q(val)} vertex="1"><mxGeometry x="{x}" width="{w}" height="30" as="geometry"><mxRectangle width="{w}" height="30" as="alternateBounds"/></mxGeometry></mxCell>')
def table(key,title,x,y,fields,fill,stroke):
    tid=nid(); h=60+30*len(fields)
    out.append(f'<mxCell id="{tid}" parent="1" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;fillColor={fill};strokeColor={stroke};" value={q(title)} vertex="1"><mxGeometry x="{x}" y="{y}" width="{W}" height="{h}" as="geometry"/></mxCell>')
    fields=[('Ключ','Поле','Тип','Обяз.','Описание')]+list(fields)
    for i,f in enumerate(fields):
        if i==0:
            rid=nid(); out.append(f'<mxCell id="{rid}" parent="{tid}" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=1;" value="" vertex="1"><mxGeometry y="30" width="{W}" height="30" as="geometry"/></mxCell>')
            x=0
            for w,v in zip(CW,f): cell(rid,x,w,v,'fontStyle=2;fontSize=10;fontColor=#555555;'); x+=w
            continue
        (k,name,typ,note)=f
        nn = typ.endswith(' NN') or k=='PK'; typ=typ.replace(' NN','')
        rid=nid(); rows[(key,name)]=rid
        pk = k=='PK'
        out.append(f'<mxCell id="{rid}" parent="{tid}" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom={1 if pk else 0};" value="" vertex="1"><mxGeometry y="{30+30*i}" width="{W}" height="30" as="geometry"/></mxCell>')
        cell(rid,0,CW[0],k,'fontStyle=1;' if pk else '')
        cell(rid,CW[0],CW[1],name,'align=left;spacingLeft=6;'+('fontStyle=5;' if pk else ''))
        cell(rid,CW[0]+CW[1],CW[2],typ,'align=left;spacingLeft=4;fontColor=#555555;fontSize=11;')
        cell(rid,CW[0]+CW[1]+CW[2],CW[3],'да' if nn else '','align=center;fontSize=11;')
        cell(rid,CW[0]+CW[1]+CW[2]+CW[3],CW[4],note,'align=left;spacingLeft=4;fontSize=11;')
def edge(s,t,ex,en,pts):
    style=f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=11;startArrow=ERmandOne;startFill=0;endArrow=ERoneToMany;endFill=0;exitX={ex};exitY=0.5;exitDx=0;exitDy=0;entryX={en};entryY=0.5;entryDx=0;entryDy=0;"
    p='<Array as="points">'+''.join(f'<mxPoint x="{a}" y="{b}"/>' for a,b in pts)+'</Array>'
    out.append(f'<mxCell id="{nid()}" parent="1" edge="1" source="{rows[s]}" target="{rows[t]}" style="{style}" value=""><mxGeometry relative="1" as="geometry">{p}</mxGeometry></mxCell>')
def note(x,y,w,h,text):
    out.append(f'<mxCell id="{nid()}" parent="1" vertex="1" style="shape=note;size=14;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacing=8;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" value={q(text)}><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
X1,X2,X3=40,590,1140
table('type','Тип объекта (object_type)',X1,80,[
 ('PK','type_id','bigint','уникальный id типа'),
 ('UK','type_code','varchar(50) NN','код: TU, NPS, ZD…'),
 ('','name','varchar(255) NN','название типа'),
 ('','description','text','пояснение')],"#d5e8d4","#82b366")
table('rule','Правило состава (object_type_rule)',X1,330,[
 ('PK','rule_id','bigint','уникальный id правила'),
 ('FK','parent_type_id','bigint NN','тип родителя'),
 ('FK','child_type_id','bigint NN','тип потомка'),
 ('','min_count','integer NN','минимум потомков'),
 ('','max_count','integer','максимум; пусто = без предела')],"#d5e8d4","#82b366")
table('obj','Объект (object)',X2,80,[
 ('PK','object_id','bigint','уникальный id объекта'),
 ('FK','parent_id','bigint','родитель; пусто у корня'),
 ('FK','type_id','bigint NN','тип объекта'),
 ('UK','object_code','varchar(255) NN','код: MT1.TU2.LU1.KP116'),
 ('','name','varchar(255) NN','название'),
 ('','km','numeric(8,3)','километр трассы (для ЛЧ)'),
 ('','seq_no','integer','порядок по ходу нефти'),
 ('','valid_from','timestamptz NN','действует с'),
 ('','valid_to','timestamptz','действует по'),
 ('','attrs','jsonb','паспортные данные')],"#dae8fc","#6c8ebf")
table('link','Связь объектов (object_link)',X3,80,[
 ('PK','link_id','bigint','уникальный id связи'),
 ('FK','from_object_id','bigint NN','от какого объекта'),
 ('FK','to_object_id','bigint NN','к какому объекту'),
 ('','link_type','varchar(50) NN','FLOW / USES / LOCATED_AT')],"#ffe6cc","#d79b00")
table('par','Параметр (parameter)',X3,330,[
 ('PK','parameter_id','bigint','уникальный id сигнала'),
 ('FK','object_id','bigint NN','чей это сигнал'),
 ('','code','varchar(50) NN','P, POS, STATE…'),
 ('','name','varchar(255) NN','название'),
 ('','unit','varchar(50)','единица измерения'),
 ('UK','label','varchar(255)','путь атрибута в PI AF'),
 ('','nic','varchar(50)','id сигнала в источнике')],"#e1d5e7","#9673a6")
edge(('type','type_id'),('obj','type_id'),1,0,[(555,155),(555,215)])
edge(('type','type_id'),('rule','parent_type_id'),0,0,[(22,155),(22,435)])
edge(('type','type_id'),('rule','child_type_id'),0,0,[(8,155),(8,465)])
edge(('obj','object_id'),('obj','parent_id'),0,0,[(572,155),(572,185)])
edge(('obj','object_id'),('link','from_object_id'),1,0,[(1112,155),(1112,185)])
edge(('obj','object_id'),('link','to_object_id'),1,0,[(1124,155),(1124,215)])
edge(('obj','object_id'),('par','object_id'),1,0,[(1100,155),(1100,435)])
note(X1,560,W,200,"<b>Обозначения</b><br>PK — первичный ключ, уникальный id строки.<br>FK — внешний ключ, ссылка на PK другой таблицы.<br>UK — значение уникально в таблице.<br>«Обяз.» — поле обязательно для заполнения (NOT NULL).<br>Типы данных PostgreSQL: идентификаторы и ссылки — bigint, коды — varchar(50), названия — varchar(255).<br><br><b>Справочники</b><br>Тип объекта — список видов: МТ, ТУ, ГНПС, НПС, ЛЧ, КП, РП, резервуар, ПНС, ПА, НС, МНА, ОК, САРД, заслонка, ФГУ, КПП СОД, задвижка, датчик давления.<br>Правило состава — кто в кого входит и сколько штук: НС → МНА ровно 4, ПНС → ПА от 1 до 10. Пара (parent_type_id, child_type_id) уникальна.")
note(X2,460,W,170,"<b>Объект — дерево «входит в состав»</b><br>Одна таблица на все объекты. parent_id ссылается на object_id этой же таблицы, поэтому родителем может быть объект любого типа.<br>Пример: ТУ-1 → ГНПС-1 → НС → МНА-1 → задвижка.<br><br>Родитель: строка с object_id = наш parent_id.<br>Потомки: строки, у которых parent_id = наш object_id.<br>У корня (МТ) parent_id пустой.")
note(X3,650,W,190,"<b>Связи вне дерева</b><br>У объекта один родитель, но есть отношения, которые в дерево не укладываются:<br>USES — ГНПС-1 и ГНПС-2 используют общий РП;<br>LOCATED_AT — НПС двух ТУ стоят на одной площадке;<br>FLOW — объект from стоит перед объектом to по ходу нефти.<br>Тройка (from_object_id, to_object_id, link_type) уникальна.<br><br><b>Параметр</b> — сигналы объекта (давление, положение задвижки). Пара (object_id, code) уникальна. Мост к заданию 2.")
out.append('<mxCell id="title" parent="1" vertex="1" style="text;html=1;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;" value="Задание 1. ER-диаграмма информационной модели участка МН (PostgreSQL)"><mxGeometry x="40" y="20" width="800" height="30" as="geometry"/></mxCell>')
xml='<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net">\n  <diagram name="ER-диаграмма" id="er1">\n    <mxGraphModel dx="1400" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">\n      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n        '+'\n        '.join(out)+'\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n'
open(sys.argv[1],'w',encoding='utf-8').write(xml)
