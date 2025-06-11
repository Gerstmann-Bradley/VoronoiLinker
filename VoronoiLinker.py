# !!! Disclaimer: Use the contents of this file at your own risk !!!
# 100% of the content of this file contains malicious code!!

bl_info = {'name':"Voronoi Linker", 'author':"ugorek",
           'version':(5,0,2), 'blender':(4,0,2), 'created':"2024.03.06",
           'info_supported_blvers': "b4.0.2 – b4.0.2",
           'description':"Various utilities for nodes connecting, based on distance field.", 'location':"Node Editor",
           'warning':"", 
           'category':"Node",
           'wiki_url':"https://github.com/ugorek000/VoronoiLinker/wiki", 'tracker_url':"https://github.com/ugorek000/VoronoiLinker/issues"}

from builtins import len as length
import bpy, ctypes, rna_keymap_ui, bl_keymap_utils
import blf, gpu, gpu_extras.batch

from math import pi, cos, sin
from mathutils import Vector as Vec
Vec2 = Col4 = Vec

import platform
from time import perf_counter, perf_counter_ns
import copy

dict_classes = {}
dict_vtClasses = {}

voronoiAddonName = bl_info['name'].replace(" ","")
class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = voronoiAddonName

list_kmiDefs = []
dict_setKmiCats = {'grt':set(), 'oth':set(), 'spc':set(), 'qqm':set(), 'cus':set()}

def SmartAddToRegAndAddToKmiDefs(cls, txt, dict_props={}):
    dict_numToKey = {"1":'ONE', "2":'TWO', "3":'THREE', "4":'FOUR', "5":'FIVE', "6":'SIX', "7":'SEVEN', "8":'EIGHT', "9":'NINE', "0":'ZERO'}
    dict_classes[cls] = True
    dict_vtClasses[cls] = True
    list_kmiDefs.append( (cls.bl_idname, dict_numToKey.get(txt[4:], txt[4:]), txt[0]=="S", txt[1]=="C", txt[2]=="A", txt[3]=="+", dict_props) )

isWin = platform.system()=='Windows'

viaverIsBlender4 = bpy.app.version[0]==4 #imp

voronoiAnchorCnName = "Voronoi_Anchor" 
voronoiAnchorDtName = "Voronoi_Anchor_Dist"
voronoiSkPreviewName = "voronoi_preview"
voronoiPreviewResultNdName = "SavePreviewResult"

def GetUserKmNe():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']

#It may be worth someday adding the tool for modification in the process of the tool itself, for example, the ALT option for ALT D for VQDT. Now even more relevant for VWT.

#Somewhere in the comments, the phrase "editor type" can be used-the same as "type of wood"; This refers to 4 classic built -in editors, and they are also types of trees.

#For some tools there are the same constants among themselves, but with their prefixes; It is spaced for convenience so as not to "rent" from other tools.

#Actual needs for VL, currently available at the moment (?) Via oops:
# 1. Is Geovewer active (by heading) and/or active-testing right now? (At a low level, not reading from Spreadsheet)
# 2. An unambiguous definition for the context of the editor, through which the NOD is higher than the level, the user entered the current group.
# 3. How to distinguish common class Enum from unique enum for this nod?
# 4. Change the type of field that he previously examines for geo-viewer.
# 5. The height of the mock -up of the socket (I had regretted for a long time that I added DRAW SOCKETRA in general (only aesthetics saves this from removal)).
# 6. A newly created interface through the API now has to go through all existing trees, and look for its "copies" to install it `Default_value`; I simultaneously imitating a classic non-API way.
# 7. Full access on interface panels with all buns. See | 4 |.

#Table (theoretical) of the usefulness of tools in addon trees (by default - useful):
# Vlt
# VPT partially
# VPAT partially
# VMT No?
# Vqmt no
# VRT
# Vst
# Vht
# VMLT
# Vest
# Vlrt
# Vqdt no
# Vict no!
# Vltt
# Vwt
# VLNST No?
# Vrnt

#TODO0VVV Process all combinations in n^3: space_data.tree_type and space_data.edit_tree.bl_idname; classic, lost, and added; tied and not attached to the editor.
# ^ And then the performance of all tools in them. And then check in the existing tree the interaction of a lost socket in a lost nod for all tools.

class TryAndPass():
    def __enter__(self):
        pass
    def __exit__(self, *_):
        return True

#Names within the framework of the code of this addon:
#SK - SOCKET
#SKF-SOCTENT interface
#SKIN - input socket (SKI)
#SKOUT - output socket (SKO)
#SKFIN-input socket interface
#skfout-output socket interface
#skfa - a collection of wood interfaces (Tree.interface.items_tree), including Simrep
#SKFT - the basis of wood interfaces (Tree.interface)
#ND - NOD
#rr - REAROUT
##
#blid - Bl_idname
#blab - Bl_Label
#DNF - IDentifier
##
#Unused variables are named with "_ pulling."

dict_timeAvg = {}
dict_timeOutside = {}
#    with ToTimeNs("aaa"):
class ToTimeNs(): #Сдаюсь. Я не знаю, почему так лагает на больших деревьях. Но судя по замерам, это где-то за пределами VL.
    def __init__(self, name):
        self.name = name
        tpcn = perf_counter_ns()
        dict_timeOutside[name] = tpcn-dict_timeOutside.setdefault(name, 0)
        dict_timeAvg.setdefault(name, [0, 0])
        self.tmn = tpcn
    def __enter__(self):
        pass
    def __exit__(self, *_):
        tpcn = perf_counter_ns()
        nsExec = tpcn-self.tmn
        list_avg = dict_timeAvg[self.name]
        list_avg[0] += 1
        list_avg[1] += nsExec
        txt1 = "{:,}".format(nsExec).rjust(13)
        txt2 = "{:,}".format(dict_timeOutside[self.name]).rjust(13)
        txt3 = "{:,}".format(int(list_avg[1]/list_avg[0]))
        txt = " ".join(("", self.name, txt1, "~~~", txt2, "===", txt3))
        dict_timeOutside[self.name] = tpcn

#TODO1V6 with an active tool PRTSCR spam in the `Warn console ... pyrna_enum_to_py: ... '171' Matches nom in 'Event'`.

from bpy.app.translations import pgettext_iface as TranslateIface

dict_vlHhTranslations = {}

dict_vlHhTranslations['ru_RU'] = {'author':"ugorek",    'vl':(5,0,0), 'created':"2024.02.29", 'trans':{'a':{}, 'Op':{}}} #self
dict_vlHhTranslations['zh_CN'] = {'author':"chenpaner", 'vl':(4,0,0), 'created':"2023.12.15", 'trans':{'a':{}, 'Op':{}}} #https://github.com/ugorek000/VoronoiLinker/issues/21
#dict_vlHhTranslations['aa_AA'] = #Кто же будет вторым?. И как скоро?

for dk in dict_vlHhTranslations:
    exec(dk+f" = '{dk}'") #Когда будут языки с @variantcode (наверное никогда), тогда и можно будет париться.

class VlTrMapForKey():
    def __init__(self, key, *, tc='a'):
        self.key = key
        self.data = {}
        self.tc = tc
    def __enter__(self):
        return self.data
    def __exit__(self, *_):
        for dk, dv in self.data.items():
            dict_vlHhTranslations[dk]['trans'][self.tc][self.key] = dv

def TxtClsBlabToolSett(cls):
    return cls.bl_label+" tool settings"

list_translationClasses = []

txtAddonVer = ".".join([str(v) for v in bl_info['version']])
txt_addonVerDateCreated = f"Version {txtAddonVer} created {bl_info['created']}"

txt_copySettAsPyScript = "Copy addon settings as .py script"
txt_FloatQuickMath = "Float Quick Math"
txt_VectorQuickMath = "Vector Quick Math"
txt_BooleanQuickMath = "Boolean Quick Math"
txt_ColorQuickMode = "Color Quick Mode"

prefsTran = None

class TranClsItemsUtil():
    def __init__(self, tup_items):
        if type(tup_items[0])==tuple:
            self.data = dict([(li[0], li[1:]) for li in tup_items])
        else:
            self.data = tup_items
    def __getattr__(self, att):
        if type(self.data)==tuple:
            match att:
                case 'name':
                    return self.data[0]
                case 'description':
                    return self.data[1]
            assert False
        else:
            return TranClsItemsUtil(self.data[att]) #`toolProp.ENUM1.name`
    def __getitem__(self, key):
        return TranClsItemsUtil(self.data[key]) #`toolProp['ENUM1'].name`
class TranAnnotFromCls():
    def __init__(self, annot):
        self.annot = annot
    def __getattr__(self, att):
        result = self.annot.keywords[att]
        return result if att!='items' else TranClsItemsUtil(result)
def GetAnnotFromCls(cls, key): #Так вот где они прятались, в аннотациях. А я то уж потерял надежду, думал вручную придётся.
    return TranAnnotFromCls(cls.__annotations__[key])

def GetPrefsRnaProp(att, inx=-1):
    prop = prefsTran.rna_type.properties[att]
    return prop if inx==-1 else getattr(prop,'enum_items')[inx]

dict_toolLangSpecifDataPool = {}

def DisplayMessage(title, text, icon='NONE'):
    def PopupMessage(self, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')

def GetSkLabelName(sk):
    return sk.label if sk.label else sk.name
def CompareSkLabelName(sk1, sk2, isIgnoreCase=False):
    if isIgnoreCase:
        return GetSkLabelName(sk1).upper()==GetSkLabelName(sk2).upper()
    else:
        return GetSkLabelName(sk1)==GetSkLabelName(sk2)

def RecrGetNodeFinalLoc(nd):
    return nd.location+RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location

def GetListOfNdEnums(nd):
    return [pr for pr in nd.rna_type.properties if not(pr.is_readonly or pr.is_registered)and(pr.type=='ENUM')]

def SelectAndActiveNdOnly(ndTar):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar
    ndTar.select = True

dict_typeSkToBlid = {
        'SHADER':    'NodeSocketShader',
        'RGBA':      'NodeSocketColor',
        'VECTOR':    'NodeSocketVector',
        'VALUE':     'NodeSocketFloat',
        'STRING':    'NodeSocketString',
        'INT':       'NodeSocketInt',
        'BOOLEAN':   'NodeSocketBool',
        'ROTATION':  'NodeSocketRotation',
        'GEOMETRY':  'NodeSocketGeometry',
        'OBJECT':    'NodeSocketObject',
        'COLLECTION':'NodeSocketCollection',
        'MATERIAL':  'NodeSocketMaterial',
        'TEXTURE':   'NodeSocketTexture',
        'IMAGE':     'NodeSocketImage',
        'CUSTOM':    'NodeSocketVirtual'}
def SkConvertTypeToBlid(sk):
    return dict_typeSkToBlid.get(sk.type, "Vl_Unknow")

set_utilTypeSkFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}

def IsClassicSk(sk):
    set_classicSocketsBlid = {'NodeSocketShader',  'NodeSocketColor',   'NodeSocketVector','NodeSocketFloat',     'NodeSocketString',  'NodeSocketInt',    'NodeSocketBool',
                              'NodeSocketRotation','NodeSocketGeometry','NodeSocketObject','NodeSocketCollection','NodeSocketMaterial','NodeSocketTexture','NodeSocketImage'}
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return SkConvertTypeToBlid(sk) in set_classicSocketsBlid

set_utilEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}

def IsClassicTreeBlid(blid):
    set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}
    return blid in set_quartetClassicTreeBlids


class PieRootData:
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
    pieDisplaySocketColor = 0
    pieAlignment = 0
    uiScale = 1.0
def SetPieData(self, toolData, prefs, col):
    def GetPiePref(name):
        return getattr(prefs, self.vlTripleName.lower()+name)
    toolData.isSpeedPie = GetPiePref("PieType")=='SPEED'
    toolData.pieScale = GetPiePref("PieScale") #todo1v6 уже есть toolData.prefs, так что можно аннигилировать; и перевозюкать всё это пограмотнее. А ещё комментарий в SolderClsToolNames().
    toolData.pieDisplaySocketTypeInfo = GetPiePref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = GetPiePref("PieDisplaySocketColor")
    toolData.pieAlignment = GetPiePref("PieAlignment")
    toolData.uiScale = self.uiScale
    toolData.prefs = prefs
    prefs.vaDecorColSkBack = col #Важно перед vaDecorColSk; см. VaUpdateDecorColSk().
    prefs.vaDecorColSk = col

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""

def VlrtRememberLastSockets(sko, ski):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        #ski без sko для VLRT бесполезен
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)
def NewLinkHhAndRemember(sko, ski):
    DoLinkHh(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)


def GetOpKmi(self, event): #Todo00 есть ли концепция или способ правильнее?
    #Оператор может иметь несколько комбинаций вызова, все из которых будут одинаковы по ключу в `keymap_items`, поэтому перебираем всех вручную
    blid = getattr(bpy.types, self.bl_idname).bl_idname
    for li in GetUserKmNe().keymap_items:
        if li.idname==blid:
            #Заметка: Искать и по соответствию самой клавише тоже, модификаторы тоже могут быть одинаковыми у нескольких вариантах вызова.
            if (li.type==event.type)and(li.shift_ui==event.shift)and(li.ctrl_ui==event.ctrl)and(li.alt_ui==event.alt):
                #Заметка: Могут быть и два идентичных хоткеев вызова, но Blender будет выполнять только один из них (по крайней мере для VL), тот, который будет первее в списке.
                return li # Эта функция также выдаёт только первого в списке.
def GetSetOfKeysFromEvent(event, isSide=False):
    set_keys = {event.type}
    if event.shift:
        set_keys.add('RIGHT_SHIFT' if isSide else 'LEFT_SHIFT')
    if event.ctrl:
        set_keys.add('RIGHT_CTRL' if isSide else 'LEFT_CTRL')
    if event.alt:
        set_keys.add('RIGHT_ALT' if isSide else 'LEFT_ALT')
    if event.oskey:
        set_keys.add('OSKEY' if isSide else 'OSKEY')
    return set_keys


def FtgGetTargetOrNone(ftg):
    return ftg.tar if ftg else None

def MinFromFtgs(ftg1, ftg2):
    if (ftg1)or(ftg2): #Если хотя бы один из них существует.
        if not ftg2: #Если одного из них не существует,
            return ftg1
        elif not ftg1: # то остаётся однозначный выбор для второго.
            return ftg2
        else: #Иначе выбрать ближайшего.
            return ftg1 if ftg1.dist<ftg2.dist else ftg2
    return None

def CheckUncollapseNodeAndReNext(nd, self, *, cond, flag=None): #Как же я презираю свёрнутые ноды.
    if (nd.hide)and(cond):
        nd.hide = False #Заметка: Осторожнее с вечным циклом в топологии NextAssignmentTool.
        #Алерт! type='DRAW_WIN' вызывает краш для некоторых редких деревьев со свёрнутыми нодами! Было бы неплохо забагрепортить бы это, если бы ещё знать как это отловить.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        #todo0 стоит перерисовывать только один раз, если было раскрыто несколько нодов подряд; но без нужды. Если таковое случилось, то у этого инструмента хреновая топология поиска.
        self.NextAssignmentRoot(flag)

class LyAddQuickInactiveCol():
    def __init__(self, where, att='row', align=True, active=False):
        self.ly = getattr(where, att)(align=align)
        self.ly.active = active
    def __enter__(self):
        return self.ly
    def __exit__(self, *_):
        pass

def LyAddLeftProp(where, who, att, active=True):
    #where.prop(who, att); return
    row = where.row()
    row.alignment = 'LEFT'
    row.prop(who, att)
    row.active = active

def LyAddDisclosureProp(where, who, att, *, txt=None, active=True, isWide=False): #Заметка: Не может на всю ширину, если where -- row.
    tgl = getattr(who, att)
    rowMain = where.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #+":"*tgl
    rowProp.prop(who, att, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
    rowProp.active = active
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, att, text=" ", emboss=False)
    return tgl

def LyAddNoneBox(where):
    box = where.box()
    box.label()
    box.scale_y = 0.5
def LyAddHandSplitProp(where, who, att, *, text=None, active=True, returnAsLy=False, forceBoolean=0):
    spl = where.row().split(factor=0.42, align=True)
    spl.active = active
    row = spl.row(align=True)
    row.alignment = 'RIGHT'
    pr = who.rna_type.properties[att]
    isNotBool = pr.type!='BOOLEAN'
    isForceBoolean = not not forceBoolean
    row.label(text=pr.name*(isNotBool^isForceBoolean) if not text else text)
    if (not active)and(pr.type=='FLOAT')and(pr.subtype=='COLOR'):
        LyAddNoneBox(spl)
    else:
        if not returnAsLy:
            txt = "" if forceBoolean!=2 else ("True" if getattr(who, att) else "False")
            spl.prop(who, att, text=txt if isNotBool^isForceBoolean else None)
        else:
            return spl

def LyAddNiceColorProp(where, who, att, align=False, txt="", ico='NONE', decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else TranslateIface(who.rna_type.properties[att].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, att, text="", icon=ico)
    rowProp.active = decor//2%2

def LyAddKeyTxtProp(where, prefs, att):
    rowProp = where.row(align=True)
    LyAddNiceColorProp(rowProp, prefs, att)
    #Todo0 я так и не врубился как пользоваться вашими prop event'ами, жуть какая-то. Помощь извне не помешала бы.
    with LyAddQuickInactiveCol(rowProp) as row:
        row.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, att)

def LyAddLabeledBoxCol(where, *, text="", active=False, scale=1.0, align=True):
    colMain = where.column(align=True)
    box = colMain.box()
    box.scale_y = 0.5
    row = box.row(align=True)
    row.alignment = 'CENTER'
    row.label(text=text)
    row.active = active
    box = colMain.box()
    box.scale_y = scale
    return box.column(align=align)

def LyAddTxtAsEtb(where, txt):
    row = where.row(align=True)
    row.label(icon='ERROR')
    col = row.column(align=True)
    for li in txt.split("\n")[:-1]:
        col.label(text=li, translate=False)
def LyAddEtb(where): #"Вы дебагов фиксите? Нет, только нахожу."
    import traceback
    LyAddTxtAsEtb(where, traceback.format_exc())

def PowerArr4(arr, *, pw=1/2.2): #def PowerArrToVec(arr, *, pw=1/2.2): return Vec(map(lambda a: a**pw, arr))
    return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def OpaqueCol3Tup4(col, *, al=1.0):
    return (col[0], col[1], col[2], al)
def MaxCol4Tup4(col):
    return (max(col[0], 0), max(col[1], 0), max(col[2], 0), max(col[3], 0))
def GetSkColorRaw(sk):
    if sk.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        return sk.draw_color(bpy.context, sk.node) #Заметка: Если нужно будет избавиться от всех `bpy.` и пронести честный путь всех context'ов, то сначала подумать об этом.
    elif hasattr(sk,'draw_color_simple'):
        return sk.draw_color_simple()
    else:
        return (1, 0, 1, 1)
def GetSkColSafeTup4(sk): #Не брать прозрачность от сокетов; и избавляться от отрицательных значений, что могут быть у аддонских сокетов.
    return OpaqueCol3Tup4(MaxCol4Tup4(GetSkColorRaw(sk)))
dict_skTypeHandSolderingColor = { #Для VQMT.
    'BOOLEAN':    (0.800000011920929,   0.6499999761581421,  0.8399999737739563,  1.0),
    'COLLECTION': (0.9599999785423279,  0.9599999785423279,  0.9599999785423279,  1.0),
    'RGBA':       (0.7799999713897705,  0.7799999713897705,  0.1599999964237213,  1.0),
    'VALUE':      (0.6299999952316284,  0.6299999952316284,  0.6299999952316284,  1.0),
    'GEOMETRY':   (0.0,                 0.8399999737739563,  0.6399999856948853,  1.0),
    'IMAGE':      (0.38999998569488525, 0.2199999988079071,  0.38999998569488525, 1.0),
    'INT':        (0.3499999940395355,  0.550000011920929,   0.36000001430511475, 1.0),
    'MATERIAL':   (0.9200000166893005,  0.46000000834465027, 0.5099999904632568,  1.0),
    'OBJECT':     (0.9300000071525574,  0.6200000047683716,  0.36000001430511475, 1.0),
    'ROTATION':   (0.6499999761581421,  0.38999998569488525, 0.7799999713897705,  1.0),
    'SHADER':     (0.38999998569488525, 0.7799999713897705,  0.38999998569488525, 1.0),
    'STRING':     (0.4399999976158142,  0.699999988079071,   1.0,                 1.0),
    'TEXTURE':    (0.6200000047683716,  0.3100000023841858,  0.6399999856948853,  1.0),
    'VECTOR':     (0.38999998569488525, 0.38999998569488525, 0.7799999713897705,  1.0),
    'CUSTOM':     (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 1.0) }
for dk, dv in dict_skTypeHandSolderingColor.items():
    dict_skTypeHandSolderingColor[dk] = PowerArr4(dv, pw=2.2)

class SoldThemeCols:
    dict_mapNcAtt = {0: 'input_node',        1:  'output_node',  3: 'color_node',
                     4: 'vector_node',       5:  'filter_node',  6: 'group_node',
                     8: 'converter_node',    9:  'matte_node',   10:'distor_node',
                     12:'pattern_node',      13: 'texture_node', 32:'script_node',
                     33:'group_socket_node', 40: 'shader_node',  41:'geometry_node',
                     42:'attribute_node',    100:'layout_node'}
def SolderThemeCols(themeNe):
    def GetNiceColNone(col4):
        return Col4(PowerArr4(col4, pw=1/1.75))
        #return Col4(col4)*1.5
    def MixThCol(col1, col2, fac=0.4): #\source\blender\editors\space_node\node_draw.cc : node_draw_basis() : "Header"
        return col1*(1-fac)+col2*fac
    SoldThemeCols.node_backdrop4 = Col4(themeNe.node_backdrop)
    SoldThemeCols.node_backdrop4pw = GetNiceColNone(SoldThemeCols.node_backdrop4) #Для Ctrl-F: оно используется, см ниже `+"4pw"`.
    for pr in themeNe.bl_rna.properties:
        dnf = pr.identifier
        if dnf.endswith("_node"):
            col4 = MixThCol(SoldThemeCols.node_backdrop4, Col4(OpaqueCol3Tup4(getattr(themeNe, dnf))))
            setattr(SoldThemeCols, dnf+"4", col4)
            setattr(SoldThemeCols, dnf+"4pw", GetNiceColNone(col4))
            setattr(SoldThemeCols, dnf+"3", Vec(col4[:3])) #Для vptRvEeIsSavePreviewResults.
def GetNdThemeNclassCol(ndTar):
    if ndTar.bl_idname=='ShaderNodeMix':
        match ndTar.data_type:
            case 'RGBA':   return SoldThemeCols.color_node4pw
            case 'VECTOR': return SoldThemeCols.vector_node4pw
            case _:        return SoldThemeCols.converter_node4pw
    else:
        return getattr(SoldThemeCols, SoldThemeCols.dict_mapNcAtt.get(BNode.GetFields(ndTar).typeinfo.contents.nclass, 'node_backdrop')+"4pw")

def GetBlackAlphaFromCol(col, *, pw):
    return ( 1.0-max(max(col[0], col[1]), col[2]) )**pw

tup_whiteCol4 = (1.0, 1.0, 1.0, 1.0)

class VlDrawData():
    shaderLine = None
    shaderArea = None
    worldZoom = 0.0
    def DrawPathLL(self, vpos, vcol, *, wid):
        gpu.state.blend_set('ALPHA') #Рисование текста сбрасывает метку об альфе, поэтому устанавливается каждый раз.
        self.shaderLine.bind()
        self.shaderLine.uniform_float('lineWidth', wid)
        self.shaderLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
        gpu_extras.batch.batch_for_shader(self.shaderLine, type='LINE_STRIP', content={'pos':vpos, 'color':vcol}).draw(self.shaderLine)
    def DrawAreaFanLL(self, vpos, col):
        gpu.state.blend_set('ALPHA')
        self.shaderArea.bind()
        self.shaderArea.uniform_float('color', col)
        #todo2v6 выяснить как или сделать сглаживание для полигонов тоже.
        gpu_extras.batch.batch_for_shader(self.shaderArea, type='TRI_FAN', content={'pos':vpos}).draw(self.shaderArea)
    def VecUiViewToReg(self, vec):
        vec = vec*self.uiScale
        return Vec2( self.view_to_region(vec.x, vec.y, clip=False) )
    ##
    def DrawRectangle(self, bou1, bou2, col):
        self.DrawAreaFanLL(( (bou1[0],bou1[1]), (bou2[0],bou1[1]), (bou2[0],bou2[1]), (bou1[0],bou2[1]) ), col)
    def DrawCircle(self, loc, rad, *, resl=54, col=tup_whiteCol4):
        #Первая вершина гордо в центре, остальные по кругу. Нужно чтобы артефакты сглаживания были красивыми в центр, а не наклонёнными в куда-то бок
        self.DrawAreaFanLL(( (loc[0],loc[1]), *[ (loc[0]+rad*cos(cyc*2.0*pi/resl), loc[1]+rad*sin(cyc*2.0*pi/resl)) for cyc in range(resl+1) ] ), col)
    def DrawRing(self, pos, rad, *, wid, resl=16, col=tup_whiteCol4, spin=0.0):
        vpos = tuple( ( rad*cos(cyc*2*pi/resl+spin)+pos[0], rad*sin(cyc*2*pi/resl+spin)+pos[1] ) for cyc in range(resl+1) )
        self.DrawPathLL(vpos, (col,)*(resl+1), wid=wid)
    def DrawWidePoint(self, loc, *, radHh, col1=Col4(tup_whiteCol4), col2=tup_whiteCol4, resl=54):
        colFacOut = Col4((0.5, 0.5, 0.5, 0.4))
        self.DrawCircle(loc, radHh+3.0, resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh,     resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh/1.5, resl=resl, col=col2)
    def __init__(self, context, cursorLoc, uiScale, prefs):
        self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        self.shaderArea = gpu.shader.from_builtin('UNIFORM_COLOR')
        #self.shaderLine.uniform_float('lineSmooth', True) #Нет нужды, по умолчанию True.
        self.fontId = blf.load(prefs.dsFontFile) #Постоянная установка шрифта нужна чтобы шрифт не исчезал при смене темы оформления.
        ##
        self.whereActivated = context.space_data
        self.uiScale = uiScale
        self.view_to_region = context.region.view2d.view_to_region
        self.cursorLoc = cursorLoc
        ##
        for pr in prefs.bl_rna.properties:
            if pr.identifier.startswith("ds"):
                setattr(self, pr.identifier, getattr(prefs, pr.identifier))
        match prefs.dsDisplayStyle:
            case 'CLASSIC':    self.dsFrameDisplayType = 2
            case 'SIMPLIFIED': self.dsFrameDisplayType = 1
            case 'ONLY_TEXT':  self.dsFrameDisplayType = 0
        ##
        self.dsUniformColor = Col4(PowerArr4(self.dsUniformColor))
        self.dsUniformNodeColor = Col4(PowerArr4(self.dsUniformNodeColor))
        self.dsCursorColor = Col4(PowerArr4(self.dsCursorColor))

def DrawWorldStick(drata, pos1, pos2, col1, col2):
    drata.DrawPathLL( (drata.VecUiViewToReg(pos1), drata.VecUiViewToReg(pos2)), (col1, col2), wid=drata.dsLineWidth )
def DrawVlSocketArea(drata, sk, bou, col):
    loc = RecrGetNodeFinalLoc(sk.node)
    pos1 = drata.VecUiViewToReg(Vec2( (loc.x,               bou[0]) ))
    pos2 = drata.VecUiViewToReg(Vec2( (loc.x+sk.node.width, bou[1]) ))
    if drata.dsIsColoredSkArea:
        col[3] = drata.dsSocketAreaAlpha #Заметка: Сюда всегда приходит плотный цвет; так что можно не домножать, а перезаписывать.
    else:
        col = drata.dsUniformColor
    drata.DrawRectangle(pos1, pos2, col)
def DrawVlWidePoint(drata, loc, *, col1=Col4(tup_whiteCol4), col2=tup_whiteCol4, resl=54, forciblyCol=False): #"forciblyCol" нужен только для DrawDebug'а.
    if not(drata.dsIsColoredPoint or forciblyCol):
        col1 = col2 = drata.dsUniformColor
    drata.DrawWidePoint(drata.VecUiViewToReg(loc), radHh=( (6*drata.dsPointScale*drata.worldZoom)**2+10 )**0.5, col1=col1, col2=col2, resl=resl)

def DrawMarker(drata, loc, col, *, style):
    fac = GetBlackAlphaFromCol(col, pw=1.5)*0.625 #todo1v6 неэстетично выглядящие цвета маркера между ярким и чёрным; нужно что-нибудь с этим придумать.
    colSh = (fac, fac, fac, 0.5) #Тень
    colHl = (0.65, 0.65, 0.65, max(max(col[0],col[1]),col[2])*0.9/(3.5, 5.75, 4.5)[style]) #Прозрачная белая обводка
    colMt = (col[0], col[1], col[2], 0.925) #Цветная основа
    resl = (16, 16, 5)[style]
    ##
    drata.DrawRing((loc[0]+1.5, loc[1]+3.5), 9.0, wid=3.0, resl=resl, col=colSh)
    drata.DrawRing((loc[0]-3.5, loc[1]-5.0), 9.0, wid=3.0, resl=resl, col=colSh)
    def DrawMarkerBacklight(spin, col):
        resl = (16, 4, 16)[style]
        drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
        drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
    DrawMarkerBacklight(pi/resl, colHl) #Маркер рисуется с артефактами "дырявых пикселей". Закостылить их дублированной отрисовкой с вращением.
    DrawMarkerBacklight(0.0,     colHl) #Но из-за этого нужно уменьшать альфу белой обводки в два раза.
    drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=1.0, resl=resl, col=colMt)
    drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=1.0, resl=resl, col=colMt)
def DrawVlMarker(drata, loc, *, ofsHh, col):
    vec = drata.VecUiViewToReg(loc)
    dir = 1 if ofsHh[0]>0 else -1
    ofsX = dir*( (20*drata.dsIsDrawText+drata.dsDistFromCursor)*1.5+drata.dsFrameOffset )+4
    col = col if drata.dsIsColoredMarker else drata.dsUniformColor
    DrawMarker(drata, (vec[0]+ofsHh[0]+ofsX, vec[1]+ofsHh[1]), col, style=drata.dsMarkerStyle)

def DrawFramedText(drata, pos1, pos2, txt, *, siz, adj, colTx, colFr, colBg):
    pos1x = ps1x = pos1[0]
    pos1y = ps1y = pos1[1]
    pos2x = ps2x = pos2[0]
    pos2y = ps2y = pos2[1]
    blur = 5
    #Рамка для текста:
    match drata.dsFrameDisplayType:
        case 2: #Красивая рамка
            gradResl = 12
            gradStripHei = (pos2y-pos1y)/gradResl
            #Градиентный прозрачностью фон:
            LFx = lambda x,a,b: ((x+b)/(b+1))**0.6*(1-a)+a
            for cyc in range(gradResl):
                drata.DrawRectangle( (pos1x, pos1y+cyc*gradStripHei),
                                     (pos2x, pos1y+cyc*gradStripHei+gradStripHei),
                                     (colBg[0]/2, colBg[1]/2, colBg[2]/2, LFx(cyc/gradResl,0.2,0.05)*colBg[3]) )
            #Яркая основная обводка:
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), (colFr,)*5, wid=1.0) #Омг, если colFr[0]==-1, то результат будет содержать комплексные числа. Чзх там происходит?
            #Дополнительная мягкая обводка (вместе с уголками), придающая красоты:
            ps1x += .25
            ps1y += .25
            ps2x -= .25
            ps2y -= .25
            ofs = 2.0
            vpos = (  (ps1x, ps1y-ofs),  (ps2x, ps1y-ofs),  (ps2x+ofs, ps1y),  (ps2x+ofs, ps2y),
                      (ps2x, ps2y+ofs),  (ps1x, ps2y+ofs),  (ps1x-ofs, ps2y),  (ps1x-ofs, ps1y),  (ps1x, ps1y-ofs)  )
            drata.DrawPathLL( vpos, ((colFr[0], colFr[1], colFr[2], 0.375),)*9, wid=1.0)
        case 1: #Для тех, кому не нравится красивая рамка. И чем им она не понравилась?.
            drata.DrawRectangle( (pos1x, pos1y), (pos2x, pos2y), (colBg[0]/2.4, colBg[1]/2.4, colBg[2]/2.4, 0.8*colBg[3]) )
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), ((0.1, 0.1, 0.1, 0.95),)*5, wid=1.0)
    #Текст:
    fontId = drata.fontId
    blf.size(fontId, siz)
    dim = blf.dimensions(fontId, txt)
    cen = ( (pos1x+pos2x)/2, (pos1y+pos2y)/2 )
    blf.position(fontId, cen[0]-dim[0]/2, cen[1]+adj, 0)
    blf.enable(fontId, blf.SHADOW)
    #Подсветка для тёмных сокетов:
    blf.shadow_offset(fontId, 1, -1)
    blf.shadow(fontId, blur, 1.0, 1.0, 1.0, GetBlackAlphaFromCol(colTx, pw=3.0)*0.75)
    blf.color(fontId, 0.0, 0.0, 0.0, 0.0)
    blf.draw(fontId, txt)
    #Сам текст:
    if drata.dsIsAllowTextShadow:
        col = drata.dsShadowCol
        blf.shadow_offset(fontId, drata.dsShadowOffset[0], drata.dsShadowOffset[1])
        blf.shadow(fontId, (0, 3, 5)[drata.dsShadowBlur], col[0], col[1], col[2], col[3])
    else:
        blf.disable(fontId, blf.SHADOW)
    blf.color(fontId, colTx[0], colTx[1], colTx[2], 1.0)
    blf.draw(fontId, txt)
    return (pos2x-pos1x, pos2y-pos1y)

def DrawWorldText(drata, pos, ofsHh, text, *, colText, colBg, fontSizeOverwrite=0): #fontSizeOverwrite нужен только для vptRvEeSksHighlighting.
    siz = drata.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite
    blf.size(drata.fontId, siz)
    #Высота от "текста по факту" не вычисляется, потому что тогда каждая рамка каждый раз будет разной высоты.
    #Спецсимвол нужен, как "общий случай", чтобы покрыть максимальную высоту. Остальные символы нужны для особых шрифтов, что могут быть выше чем "█".
    dimDb = (blf.dimensions(drata.fontId, text)[0], blf.dimensions(drata.fontId, "█GJKLPgjklp!?")[1])
    pos = drata.VecUiViewToReg(pos)
    frameOffset = drata.dsFrameOffset
    ofsGap = 10
    pos = (pos[0]-(dimDb[0]+frameOffset+ofsGap)*(ofsHh[0]<0)+(frameOffset+1)*(ofsHh[0]>-1), pos[1]+frameOffset)
    #Я уже нахрен забыл, что я намудрил и как оно работает; но оно работает -- вот и славно, "работает -- не трогай":
    placePosY = round( (dimDb[1]+frameOffset*2)*ofsHh[1] ) #Без округления красивость горизонтальных линий пропадет.
    pos1 = (pos[0]+ofsHh[0]-frameOffset,               pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofsHh[0]+ofsGap+dimDb[0]+frameOffset, pos[1]+placePosY+dimDb[1]+frameOffset)
    ##
    return DrawFramedText(drata, pos1, pos2, text, siz=siz, adj=dimDb[1]*drata.dsManualAdjustment, colTx=PowerArr4(colText, pw=1/1.975), colFr=PowerArr4(colBg, pw=1/1.5), colBg=colBg)

def DrawVlSkText(drata, pos, ofsHh, ftg, *, fontSizeOverwrite=0): #Заметка: `pos` всегда ради drata.cursorLoc, но см. vptRvEeSksHighlighting.
    if not drata.dsIsDrawText:
        return (1, 0) #'1' нужен для сохранения информации направления для позиции маркеров.
    if drata.dsIsColoredText:
        colText = GetSkColSafeTup4(ftg.tar)
        colBg = MaxCol4Tup4(GetSkColorRaw(ftg.tar))
    else:
        colText = colBg = drata.dsUniformColor
    return DrawWorldText(drata, pos, ofsHh, ftg.soldText, colText=colText, colBg=colBg, fontSizeOverwrite=fontSizeOverwrite)

def DrawDebug(self, drata):
    def DebugTextDraw(pos, txt, r, g, b):
        blf.size(0,18)
        blf.position(0, pos[0]+10,pos[1], 0)
        blf.color(0, r,g,b,1.0)
        blf.draw(0, txt)
    DebugTextDraw(drata.VecUiViewToReg(drata.cursorLoc), "Cursor position here.", 1, 1, 1)
    if not self.tree:
        return
    col = Col4((1.0, 0.5, 0.5, 1.0))
    list_ftgNodes = self.ToolGetNearestNodes()
    if not list_ftgNodes:
        return
    DrawWorldStick(drata, drata.cursorLoc, list_ftgNodes[0].pos, col, col)
    for cyc, li in enumerate(list_ftgNodes):
        DrawVlWidePoint(drata, li.pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(li.pos), str(cyc)+" Node goal here", col.x, col.y, col.z)
    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(list_ftgNodes[0].tar)
    if list_ftgSksIn:
        col = Col4((0.5, 1, 0.5, 1))
        DrawVlWidePoint(drata, list_ftgSksIn[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksIn[0].pos), "Nearest socketIn here", 0.5, 1, 0.5)
    if list_ftgSksOut:
        col = Col4((0.5, 0.5, 1, 1))
        DrawVlWidePoint(drata, list_ftgSksOut[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksOut[0].pos), "Nearest socketOut here", 0.75, 0.75, 1)

def TemplateDrawNodeFull(drata, ftgNd, *, side=1): #Шаблон переосмыслен; ура. Теперь он стал похожим на все остальные.. По крайней мере нет спагетти-кода из прошлых версий.
    #todo1v6 шаблон только по одному ftg, нет разбивки по слоям, два вызова будут рисовать точку с палкой от одного над текстом другого.
    if ftgNd:
        ndTar = ftgNd.tar
        if drata.dsIsColoredNodes: #Что ж.. всё-таки теперь у нода есть цвет; благодаря ctypes.
            colLn = GetNdThemeNclassCol(ndTar)
            colPt = colLn
            colTx = colLn
        else:
            colUnc = drata.dsUniformNodeColor
            colLn = colUnc if drata.dsIsColoredLine else drata.dsUniformColor
            colPt = colUnc if drata.dsIsColoredPoint else drata.dsUniformColor
            colTx = colUnc if drata.dsIsColoredText else drata.dsUniformColor
        if drata.dsIsDrawLine:
            DrawWorldStick(drata, drata.cursorLoc, ftgNd.pos, colLn, colLn)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, ftgNd.pos, col1=colPt, col2=colPt)
        if (drata.dsIsDrawText)and(drata.dsIsDrawNodeNameLabel):
            DrawWorldText(drata, drata.cursorLoc, (drata.dsDistFromCursor*side, -0.5), ndTar.label if ndTar.label else ndTar.bl_rna.name, colText=colTx, colBg=colTx)
    elif drata.dsIsDrawPoint:
        col = tup_whiteCol4 #Единственный оставшийся неопределённый цвет. 'dsCursorColor' здесь по задумке не подходит (весь аддон ради сокетов, ок да?.).
        DrawVlWidePoint(drata, drata.cursorLoc, col1=Col4(col), col2=col)

#Высокоуровневый шаблон рисования для сокетов. Теперь в названии есть "Sk", поскольку ноды полноценно вошли в VL.
#Пользоваться этим шаблоном невероятно кайфово, после того хардкора что был в старых версиях (даже не заглядывайте туда, там около-ад).
def TemplateDrawSksToolHh(drata, *args_ftgSks, sideMarkHh=1, isDrawText=True, isClassicFlow=False, isDrawMarkersMoreTharOne=False): #Ура, шаблон переосмыслен. По ощущениям, лучше не стало.
    def GetPosFromFtg(ftg):
        return ftg.pos+Vec2((drata.dsPointOffsetX*ftg.dir, 0.0))
    list_ftgSks = [ar for ar in args_ftgSks if ar]
    cursorLoc = drata.cursorLoc
    #Отсутствие целей
    if not list_ftgSks: #Удобно получается использовать шаблон только ради ныне несуществующего DrawDoubleNone() путём отправки в args_ftgSks `None, None`.
        col = drata.dsCursorColor if drata.dsIsColoredPoint else drata.dsUniformColor
        isPair = length(args_ftgSks)==2
        vec = Vec2((drata.dsPointOffsetX*0.75, 0)) if (isPair)and(isClassicFlow) else Vec2((0.0, 0.0))
        if (isPair)and(drata.dsIsDrawLine)and(drata.dsIsAlwaysLine):
            DrawWorldStick(drata, cursorLoc-vec, cursorLoc+vec, col, col)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, cursorLoc-vec, col1=col, col2=col)
            if (isPair)and(isClassicFlow):
                DrawVlWidePoint(drata, cursorLoc+vec, col1=col, col2=col)
        return
    #Линия классического потока
    if (isClassicFlow)and(drata.dsIsDrawLine)and(length(list_ftgSks)==2):
        ftg1 = list_ftgSks[0]
        ftg2 = list_ftgSks[1]
        if ftg1.dir*ftg2.dir<0: #Для VMLT, чтобы не рисовать для двух его сокетов, что оказались с одной стороны.
            if drata.dsIsColoredLine:
                col1 = GetSkColSafeTup4(ftg1.tar)
                col2 = GetSkColSafeTup4(ftg2.tar)
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg1), GetPosFromFtg(ftg2), col1, col2)
    #Основное:
    isOne = length(list_ftgSks)==1
    for ftg in list_ftgSks:
        if (drata.dsIsDrawLine)and( (not isClassicFlow)or(isOne and drata.dsIsAlwaysLine) ):
            if drata.dsIsColoredLine:
                col1 = GetSkColSafeTup4(ftg.tar)
                col2 = drata.dsCursorColor if (isOne+(drata.dsCursorColorAvailability-1))>0 else col1
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg), cursorLoc, col1, col2)
        if drata.dsIsDrawSkArea:
            DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Col4(GetSkColSafeTup4(ftg.tar)))
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, GetPosFromFtg(ftg), col1=Col4(MaxCol4Tup4(GetSkColorRaw(ftg.tar))), col2=Col4(GetSkColSafeTup4(ftg.tar)))
    #Текст
    if isDrawText: #Текст должен быть над всеми остальными ^.
        list_ftgSksIn = [ftg for ftg in list_ftgSks if ftg.dir<0]
        list_ftgSksOut = [ftg for ftg in list_ftgSks if ftg.dir>0]
        soldOverrideDir = abs(sideMarkHh)>1 and (1 if sideMarkHh>0 else -1)
        for list_ftgs in list_ftgSksIn, list_ftgSksOut: #"Накапливать", гениально! Головная боль со спагетти-кодом исчезла.
            hig = length(list_ftgs)-1
            for cyc, ftg in enumerate(list_ftgs):
                ofsY = 0.75*hig-1.5*cyc
                dir = soldOverrideDir if soldOverrideDir else ftg.dir*sideMarkHh
                frameDim = DrawVlSkText(drata, cursorLoc, (drata.dsDistFromCursor*dir, ofsY-0.5), ftg)
                if (drata.dsIsDrawMarker)and( (ftg.tar.vl_sold_is_final_linked_cou)and(not isDrawMarkersMoreTharOne)or(ftg.tar.vl_sold_is_final_linked_cou>1) ):
                    DrawVlMarker(drata, cursorLoc, ofsHh=(frameDim[0]*dir, frameDim[1]*ofsY), col=GetSkColSafeTup4(ftg.tar))
    #Точка под курсором для классического потока
    if (isClassicFlow and isOne)and(drata.dsIsDrawPoint):
        DrawVlWidePoint(drata, cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor)

#Todo0SF Головная боль с "проскальзывающими кадрами"!! Debug, Collapse, Alt, и вообще везде.

class TestDraw:
    @classmethod
    def GetNoise(cls, w):
        from mathutils.noise import noise
        return noise((cls.time, w, cls.rand))
    @classmethod
    def Toggle(cls, context, tgl):
        import random
        stNe = bpy.types.SpaceNodeEditor
        if tgl:
            cls.rand = random.random()*32.0
            cls.time = 0.0
            cls.state = [0.5, 0.5, 0.5, 0.5]
            stNe.nsReg = stNe.nsReg if hasattr(stNe,'nsReg') else -2
            stNe.nsCur = stNe.nsReg
            stNe.handle = stNe.draw_handler_add(cls.CallbackDrawTest, (context,), 'WINDOW', 'POST_PIXEL')
        elif hasattr(stNe,'handle'):
            stNe.draw_handler_remove(stNe.handle, 'WINDOW')
            del stNe.handle
            del stNe.nsCur
            del stNe.nsReg
    @classmethod
    def CallbackDrawTest(cls, context):
        from math import atan2
        stNe = bpy.types.SpaceNodeEditor
        if stNe.nsCur!=stNe.nsReg:
            #Выключить и включить заново:
            Prefs().dsIsTestDrawing = False
            #Чума топология!
            Prefs().dsIsTestDrawing = True
            return #Не знаю, обязательно ли выходить.
        drata = VlDrawData(context, context.space_data.cursor_location, context.preferences.system.dpi/72, Prefs())
        cls.ctView2d = View2D.GetFields(context.region.view2d)
        drata.worldZoom = cls.ctView2d.GetZoom()
        ##
        for cyc in range(4):
            noise = cls.GetNoise(cyc)
            fac = 1.0# if cyc<4 else (1.0 if noise>0 else cls.state[cyc])
            cls.state[cyc] = min(max(cls.state[cyc]+noise, 0.0), 1.0)*fac
        ##
        drata.DrawPathLL(( (0,0),(1000,1000) ), (tup_whiteCol4, tup_whiteCol4), wid=0.0)
        for cycWid in range(9):
            ofsWid = cycWid*45
            for cycAl in range(4):
                col = (1,1,1,.25*(1+cycAl))
                ofsAl = cycAl*8
                for cyc5 in range(2):
                    ofs5x = 65*cyc5
                    ofs5y = 0.5*cyc5
                    drata.DrawPathLL(( (100+ofs5x,100+ofsWid+ofsAl+ofs5y),(165+ofs5x,100+ofsWid+ofsAl+ofs5y) ), (col, col), wid=0.5*(1+cycWid))
        ##
        col = Col4(cls.state)
        drata.cursorLoc = context.space_data.cursor_location
        cursorReg = drata.VecUiViewToReg(drata.cursorLoc)
        vec = cursorReg-Vec2((500,500))
        drata.DrawRing((500,500), vec.length, wid=cursorReg.x/200, resl=max(3, int(cursorReg.y/20)), col=tup_whiteCol4, spin=pi/2-atan2(vec.x, vec.y))
        #Бардак:
        center = Vec2((context.region.width/2, context.region.height/2))
        txt = "a.¯\_(- _-)_/¯"
        DrawFramedText(drata, (300,300), (490,330), txt, siz=24, adj=(555-525)*-.2, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        txt = bpy.context.window_manager.clipboard
        txt = txt[0] if txt else "a."
        DrawFramedText(drata, (375,170), (400,280), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        DrawFramedText(drata, (410,200), (435,250), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        #DrawFramedText(drata, (445,200), (470,250), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        loc = context.space_data.edit_tree.view_center
        col2 = col.copy()
        col2.w = max(0, (cursorReg.y-center.y/2)/150)
        DrawWorldText(drata, loc, (-1, 2), "█GJKLPgjklp!?", colText=col, colBg=col)
        DrawWorldText(drata, loc, (-1, .33), "abcdefghijklmnopqrstuvwxyz", colText=tup_whiteCol4, colBg=col)
        DrawWorldText(drata, loc, (0, -.33), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", colText=col2, colBg=col2)
        vec = Vec2((0,-192/drata.worldZoom))
        DrawWorldText(drata, loc+vec, (0, 0), "абфуabfy", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (200, 0), "аa", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (300, 0), "абab", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (500, 0), "ауay", colText=col, colBg=col)
        DrawMarker(drata, center+Vec2((-50,-60)), col, style=0)
        DrawMarker(drata, center+Vec2((-100,-60)), col, style=1)
        DrawMarker(drata, center+Vec2((-150,-60)), col, style=2)
        drata.DrawPathLL( (center+Vec2((0,-60)), center+Vec2((100,-60))), (OpaqueCol3Tup4(col), OpaqueCol3Tup4(col)), wid=drata.dsLineWidth )
        drata.DrawPathLL( (center+Vec2((100,-60)), center+Vec2((200,-60))), (OpaqueCol3Tup4(col), OpaqueCol3Tup4(col, al=0.0)), wid=drata.dsLineWidth )
        drata.DrawWidePoint(center+Vec2((0,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=Col4(OpaqueCol3Tup4(col)), col2=Col4(OpaqueCol3Tup4(col)))
        drata.DrawWidePoint(center+Vec2((100,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=col, col2=Col4(OpaqueCol3Tup4(col)))
        import gpu_extras.presets; gpu_extras.presets.draw_circle_2d((256,256),(1,1,1,1),10)
        ##
        cls.time += 0.01
        bpy.context.space_data.backdrop_zoom = bpy.context.space_data.backdrop_zoom #Огонь. Но есть ли более "прямой" способ? Хвалёный area.tag_redraw() что-то не работает.

class VoronoiOpTool(bpy.types.Operator):
    bl_options = {'UNDO'} #Вручную созданные линки undo'тся, так что и в VL ожидаемо тоже. И вообще для всех.
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' #Не знаю, зачем это нужно, но пусть будет.

class VoronoiToolFillers: #-1
    usefulnessForCustomTree = None
    usefulnessForUndefTree = None
    usefulnessForNoneTree = None
    canDrawInAddonDiscl = None
    canDrawInAppearance = None
    def CallbackDrawTool(self, drata): pass
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): pass
    def ModalTool(self, event, prefs): pass
    #def MatterPurposePoll(self): return None
    def MatterPurposeTool(self, event, prefs, tree): pass
    def InitToolPre(self, event): return {}
    def InitTool(self, event, prefs, tree): return {}
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs): pass

class VoronoiToolRoot(VoronoiOpTool, VoronoiToolFillers): #0
    usefulnessForUndefTree = False
    usefulnessForNoneTree = False
    canDrawInAddonDiscl = True
    canDrawInAppearance = False
    #Всегда неизбежно происходит кликанье в редакторе деревьев, где обитают ноды, поэтому для всех инструментов
    isPassThrough: bpy.props.BoolProperty(name="Pass through node selecting", default=False, description="Clicking over a node activates selection, not the tool")
    def CallbackDrawRoot(self, drata, context):
        if drata.whereActivated!=context.space_data: #Нужно, чтобы рисовалось только в активном редакторе, а не во всех у кого открыто то же самое дерево.
            return
        drata.worldZoom = self.ctView2d.GetZoom() #Получает каждый раз из-за EdgePan'а и колеса мыши. Раньше можно было бы обойтись и одноразовой пайкой.
        if self.prefs.dsIsFieldDebug:
            DrawDebug(self, drata)
        if self.tree: #Теперь для никакого дерева признаки жизни можно не подавать; выключено в связи с головной болью топологии, и пропуска инструмента для передачи хоткея в аддонских деревьях (?).
            self.CallbackDrawTool(drata)
    def ToolGetNearestNodes(self, includePoorNodes=False):
        return GetNearestNodesFtg(self.tree.nodes[:], self.cursorLoc, self.uiScale, includePoorNodes)
    def ToolGetNearestSockets(self, nd):
        return GetNearestSocketsFtg(nd, self.cursorLoc, self.uiScale)
    def NextAssignmentRoot(self, flag):
        if self.tree:
            try:
                self.NextAssignmentTool(flag, self.prefs, self.tree)
            except:
                EdgePanData.isWorking = False #Сейчас актуально только для VLT. Возможно стоит сделать ~self.ErrorToolProc, и в VLT "давать заднюю".
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
                raise
    def ModalMouseNext(self, event, prefs):
        match event.type:
            case 'MOUSEMOVE':
                self.NextAssignmentRoot(False)
            case self.kmi.type|'ESC':
                if event.value=='RELEASE':
                    return True
        return False
    def modal(self, context, event):
        context.area.tag_redraw()
        if num:=(event.type=='WHEELUPMOUSE')-(event.type=='WHEELDOWNMOUSE'):
            self.ctView2d.cur.Zooming(self.cursorLoc, 1.0-num*0.15)
        self.ModalTool(event, self.prefs)
        if not self.ModalMouseNext(event, self.prefs):
            return {'RUNNING_MODAL'}
        #* Здесь начинается завершение инструмента *
        EdgePanData.isWorking = False
        if event.type=='ESC': #Собственно то, что и должна делать клавиша побега.
            return {'CANCELLED'}
        with TryAndPass(): #Он может оказаться уже удалённым, см. второй такой.
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
        tree = self.tree
        if not tree:
            return {'FINISHED'}
        RestoreCollapsedNodes(tree.nodes)
        if (tree)and(tree.bl_idname=='NodeTreeUndefined'): #Если дерево нодов от к.-н. аддона исчезло, то остатки имеют NodeUndefined и NodeSocketUndefined.
            return {'CANCELLED'} #Через api линки на SocketUndefined всё равно не создаются, да и делать в этом дереве особо нечего; поэтому выходим.
        ##
        if not self.MatterPurposePoll():
            return {'CANCELLED'}
        if result:=self.MatterPurposeTool(event, self.prefs, tree):
            return result
        return {'FINISHED'}
    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        self.tree = tree
        editorBlid = context.space_data.tree_type #Без нужды для `self.`?.
        self.isInvokeInClassicTree = IsClassicTreeBlid(editorBlid)
        if not(self.usefulnessForCustomTree or self.isInvokeInClassicTree):
            return {'PASS_THROUGH'} #'CANCELLED'?.
        if (not self.usefulnessForUndefTree)and(editorBlid=='NodeTreeUndefined'):
            return {'CANCELLED'} #Покидается с целью не-рисования.
        if not(self.usefulnessForNoneTree or tree):
            return {'FINISHED'}
        #Одинаковая для всех инструментов обработка пропуска выделения
        if (self.isPassThrough)and(tree)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): #Проверка на дерево вторым, для эстетической оптимизации.
            #Если хоткей вызова инструмента совпадает со снятием выделения, то выделенный строчкой выше нод будет де-выделен обратно после передачи эстафеты (но останется активным).
            #Поэтому для таких ситуаций нужно снять выделение, чтобы снова произошло переключение обратно на выделенный.
            tree.nodes.active.select = False #Но без условий, для всех подряд. Ибо ^иначе будет всегда выделение без переключения; и у меня нет идей, как бы я парился с распознаванием таких ситуаций.
            return {'PASS_THROUGH'}
        ##
        self.kmi = GetOpKmi(self, event)
        if not self.kmi:
            return {'CANCELLED'} #Если в целом что-то пошло не так, или оператор был вызван через кнопку макета.
        #Если в keymap в вызове оператора не указаны его свойства, они читаются от последнего вызова; поэтому их нужно устанавливать обратно по умолчанию.
        #Имеет смысл делать это как можно раньше; актуально для VQMT и VEST.
        for li in self.rna_type.properties:
            if li.identifier!='rna_type':
                #Заметка: Определить установленность в kmi -- наличие `kmi.properties[li.identifier]`.
                setattr(self, li.identifier, getattr(self.kmi.properties, li.identifier)) #Ради этого мне пришлось реверсинженерить Blender с отладкой. А ларчик просто открывался..
        ##
        self.prefs = Prefs() #"А ларчик просто открывался".
        self.uiScale = context.preferences.system.dpi/72
        self.cursorLoc = context.space_data.cursor_location #Это class Vector, копируется по ссылке; так что можно установить (привязать) один раз здесь и не париться.
        self.drata = VlDrawData(context, self.cursorLoc, self.uiScale, self.prefs)
        SolderThemeCols(context.preferences.themes[0].node_editor) #Так же, как и с fontId; хоть и в большинстве случаев тема не будет меняться во время всего сеанса.
        self.region = context.region
        self.ctView2d = View2D.GetFields(context.region.view2d)
        if self.prefs.vIsOverwriteZoomLimits:
            self.ctView2d.minzoom = self.prefs.vOwZoomMin
            self.ctView2d.maxzoom = self.prefs.vOwZoomMax
        ##
        if result:=self.InitToolPre(event): #Для 'Pre' менее актуально что-то возвращать.
            return result
        if result:=self.InitTool(event, self.prefs, tree): #Заметка: См. топологию: возвращение ничего равносильно возвращению `{'RUNNING_MODAL'}`.
            return result
        EdgePanInit(self, context.area)
        ##
        self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(self.CallbackDrawRoot, (self.drata, context,), 'WINDOW', 'POST_PIXEL')
        if tree: #Заметка: См. местную топологию, сам инструмент могёт, но каждый из них явно выключен для отсутствующих деревьев.
            SolderSkLinks(self.tree)
            SaveCollapsedNodes(tree.nodes)
            self.NextAssignmentRoot(True) #А всего-то нужно было перенести перед modal_handler_add(). #https://projects.blender.org/blender/blender/issues/113479
        ##
        context.area.tag_redraw() #Нужно, чтобы нарисовать при активации найденного при активации; при этом местный порядок не важен.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class VoronoiToolSk(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def InitToolPre(self, event):
        self.fotagoSk = None

class VoronoiToolPairSk(VoronoiToolSk): #2
    isCanBetweenFields: bpy.props.BoolProperty(name="Can between fields", default=True, description="Tool can connecting between different field types")
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1)
    def SkBetweenFieldsCheck(self, sk1, sk2):
        #Заметка: Учитывая предназначение и название этой функции, sk1 и sk2 в любом случае должны быть из полей, и только из них.
        return (sk1.type in set_utilTypeSkFields)and( (self.isCanBetweenFields)and(sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
    def InitToolPre(self, event):
        self.fotagoSk0 = None
        self.fotagoSk1 = None

class VoronoiToolTripleSk(VoronoiToolPairSk): #3
    def ModalTool(self, event, prefs):
        if (self.isStartWithModf)and(not self.canPickThird): #Кто будет всерьёз переключаться на выбор третьего сокета путём нажатия и отжатия к-н. модификатора?.
            # Ибо это адски дорого; коль уж выбрали хоткей без модификаторов, довольствуйтесь обрезанными возможностями. Или сделайте это себе сами.
            self.canPickThird = not(event.shift or event.ctrl or event.alt)
    def InitToolPre(self, event):
        self.fotagoSk2 = None
        self.canPickThird = False
        self.isStartWithModf = (event.shift)or(event.ctrl)or(event.alt)

class VoronoiToolNd(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawNodeFull(drata, self.fotagoNd)
    def MatterPurposePoll(self):
        return not not self.fotagoNd
    def InitToolPre(self, event):
        self.fotagoNd = None

class VoronoiToolPairNd(VoronoiToolSk): #2
    def MatterPurposePoll(self):
        return self.fotagoNd0 and self.fotagoNd1
    def InitToolPre(self, event):
        self.fotagoNd0 = None
        self.fotagoNd1 = None

class VoronoiToolAny(VoronoiToolSk, VoronoiToolNd): #2
    @staticmethod
    def TemplateDrawAny(drata, ftg, *, cond):
        if cond:
            TemplateDrawNodeFull(drata, ftg)
        else:
            TemplateDrawSksToolHh(drata, ftg)
    def MatterPurposePoll(self):
        return self.fotagoAny
    def InitToolPre(self, event):
        self.fotagoAny = None

class EdgePanData:
    area = None #Должен был быть 'context', но он всё время None.
    ctCur = None
    #Накостылил по-быстрому:
    isWorking = False
    view2d = None
    cursorPos = Vec2((0,0))
    uiScale = 1.0
    center = Vec2((0,0))
    delta = 0.0 #Ох уж эти ваши дельты.
    zoomFac = 0.5
    speed = 1.0

def EdgePanTimer():
    delta = perf_counter()-EdgePanData.delta
    vec = EdgePanData.cursorPos*EdgePanData.uiScale
    field0 = Vec2(EdgePanData.view2d.view_to_region(vec.x, vec.y, clip=False))
    zoomWorld = (EdgePanData.view2d.view_to_region(vec.x+1000, vec.y, clip=False)[0]-field0.x)/1000
    #Ещё немного реймарчинга:
    field1 = field0-EdgePanData.center
    field2 = Vec2(( abs(field1.x), abs(field1.y) ))
    field2 = field2-EdgePanData.center+Vec2((10, 10)) #Слегка уменьшить границы для курсора, находящегося вплотную к краю экрана.
    field2 = Vec2(( max(field2.x, 0), max(field2.y, 0) ))
    ##
    xi, yi, xa, ya = EdgePanData.ctCur.GetRaw()
    speedZoomSize = Vec2((xa-xi, ya-yi))/2.5*delta #125 без дельты.
    field1 = field1.normalized()*speedZoomSize*((zoomWorld-1)/1.5+1)*EdgePanData.speed*EdgePanData.uiScale
    if (field2.x!=0)or(field2.y!=0):
        EdgePanData.ctCur.TranslateScaleFac((field1.x, field1.y), fac=EdgePanData.zoomFac)
    EdgePanData.delta = perf_counter() #"Отправляется в неизвестность" перед следующим заходом.
    EdgePanData.area.tag_redraw()
    return 0.0 if EdgePanData.isWorking else None
def EdgePanInit(self, area):
    EdgePanData.area = area
    EdgePanData.ctCur = self.ctView2d.cur
    EdgePanData.isWorking = True
    EdgePanData.cursorPos = self.cursorLoc
    EdgePanData.uiScale = self.uiScale
    EdgePanData.view2d = self.region.view2d
    EdgePanData.center = Vec2((self.region.width/2, self.region.height/2))
    EdgePanData.delta = perf_counter() #..А ещё есть "слегка-границы".
    EdgePanData.zoomFac = 1.0-self.prefs.vEdgePanFac
    EdgePanData.speed = self.prefs.vEdgePanSpeed
    bpy.app.timers.register(EdgePanTimer, first_interval=0.0)

# *Я в конце 2022*: Уу, какой мимимишный аддончик у меня получился на 157 строчки кода.
# *Я в конце 2023*: ААаа чёрт возьми, что тут происходит??

class StructBase(ctypes.Structure):
    _subclasses = []
    __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    @staticmethod
    def _init_structs():
        functype = type(lambda: None)
        for cls in StructBase._subclasses:
            fields = []
            for field, value in cls.__annotations__.items():
                if isinstance(value, functype):
                    value = value()
                fields.append((field, value))
            if fields:
                cls._fields_ = fields
            cls.__annotations__.clear()
        StructBase._subclasses.clear()
    @classmethod
    def GetFields(cls, tar):
        return cls.from_address(tar.as_pointer())

class BNodeSocketRuntimeHandle(StructBase): #\source\blender\makesdna\DNA_node_types.h
    if isWin:
        _pad0:        ctypes.c_char*8
    declaration:  ctypes.c_void_p
    changed_flag: ctypes.c_uint32
    total_inputs: ctypes.c_short
    _pad1:        ctypes.c_char*2
    location:     ctypes.c_float*2
class BNodeStack(StructBase):
    vec:        ctypes.c_float*4
    min:        ctypes.c_float
    max:        ctypes.c_float
    data:       ctypes.c_void_p
    hasinput:   ctypes.c_short
    hasoutput:  ctypes.c_short
    datatype:   ctypes.c_short
    sockettype: ctypes.c_short
    is_copy:    ctypes.c_short
    external:   ctypes.c_short
    _pad:       ctypes.c_char*4
class BNodeSocket(StructBase):
    next:                   ctypes.c_void_p #lambda: ctypes.POINTER(BNodeSocket)
    prev:                   ctypes.c_void_p #lambda: ctypes.POINTER(BNodeSocket)
    prop:                   ctypes.c_void_p
    identifier:             ctypes.c_char*64
    name:                   ctypes.c_char*64
    storage:                ctypes.c_void_p
    in_out:                 ctypes.c_short
    typeinfo:               ctypes.c_void_p
    idname:                 ctypes.c_char*64
    default_value:          ctypes.c_void_p
    _pad:                   ctypes.c_char*4
    label:                  ctypes.c_char*64
    description:            ctypes.c_char*64
    if (viaverIsBlender4)and(bpy.app.version_string!='4.0.0 Alpha'):
        short_label:            ctypes.c_char*64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index:               ctypes.c_int
    link:                   ctypes.c_void_p
    ns:                     BNodeStack
    runtime:                ctypes.POINTER(BNodeSocketRuntimeHandle)

class BNodeType(StructBase): #\source\blender\blenkernel\BKE_node.h
    idname:         ctypes.c_char*64
    type:           ctypes.c_int
    ui_name:        ctypes.c_char*64
    ui_description: ctypes.c_char*256
    ui_icon:        ctypes.c_int
    if bpy.app.version>=(4,0,0):
        char:           ctypes.c_void_p
    width:          ctypes.c_float
    minwidth:       ctypes.c_float
    maxwidth:       ctypes.c_float
    height:         ctypes.c_float
    minheight:      ctypes.c_float
    maxheight:      ctypes.c_float
    nclass:         ctypes.c_int16 #https://github.com/ugorek000/ManagersNodeTree
class BNode(StructBase): #Для VRT.
    next:    lambda: ctypes.POINTER(BNode)
    prev:    lambda: ctypes.POINTER(BNode)
    inputs:     ctypes.c_void_p*2
    outputs:    ctypes.c_void_p*2
    name:       ctypes.c_char*64
    identifier: ctypes.c_int
    flag:       ctypes.c_int
    idname:     ctypes.c_char*64
    typeinfo:   ctypes.POINTER(BNodeType)
    type:       ctypes.c_int16
    ui_order:   ctypes.c_int16
    custom1:    ctypes.c_int16
    custom2:    ctypes.c_int16
    custom3:    ctypes.c_float
    custom4:    ctypes.c_float
    id:         ctypes.c_void_p
    storage:    ctypes.c_void_p
    prop:       ctypes.c_void_p
    parent:     ctypes.c_void_p
    locx:       ctypes.c_float
    locy:       ctypes.c_float
    width:      ctypes.c_float
    height:     ctypes.c_float
    offsetx:    ctypes.c_float
    offsety:    ctypes.c_float
    label:      ctypes.c_char*64
    color:      ctypes.c_float*3
#Спасибо пользователю с ником "Oxicid", за этот кусок кода по части ctypes. "А что, так можно было?".
#Ох уж эти разрабы; пришлось самому добавлять возможность получать позиции сокетов. Месево от 'Blender 4.0 alpha' прижало к стенке и вынудило.
#..Это получилось сделать аш на питоне, неужели так сложно было пронести api?
#P.s. минута молчания в честь павших героев, https://projects.blender.org/blender/blender/pulls/117809.

def SkGetLocVec(sk):
    return Vec2(BNodeSocket.GetFields(sk).runtime.contents.location[:]) if (sk.enabled)and(not sk.hide) else Vec2((0, 0))
#Что ж, самое сложное пройдено. До технической возможности поддерживать свёрнутые ноды осталось всего ничего.
#Жаждущие это припрутся сюда по-быстрому с покерфейсом, возьмут что нужно, и модифицируют себе.
#Тот первый, кто это сделает, моё тебе послание: "Что ж, молодец. Теперь ты можешь сосаться к сокетам свёрнутого нода. Надеюсь у тебя счастья полные штаны".

class RectBase(StructBase):
    def GetRaw(self):
        return self.xmin, self.ymin, self.xmax, self.ymax
    def TranslateRaw(self, xy):
        self.xmin += xy[0]
        self.xmax += xy[0]
        self.ymin += xy[1]
        self.ymax += xy[1]
    def TranslateScaleFac(self, xy, fac=0.5):
        if xy[0]>0:
            self.xmin += xy[0]*fac
            self.xmax += xy[0]
        elif xy[0]<0:
            self.xmin += xy[0]
            self.xmax += xy[0]*fac
        ##
        if xy[1]>0:
            self.ymin += xy[1]*fac
            self.ymax += xy[1]
        elif xy[1]<0:
            self.ymin += xy[1]
            self.ymax += xy[1]*fac
    def Zooming(self, center=None, fac=1.0):
        if center:
            centerX = center[0]
            centerY = center[1]
        else:
            centerX = (self.xmax+self.xmin)/2
            centerY = (self.ymax+self.ymin)/2
        self.xmax = (self.xmax-centerX)*fac+centerX
        self.xmin = (self.xmin-centerX)*fac+centerX
        self.ymax = (self.ymax-centerY)*fac+centerY
        self.ymin = (self.ymin-centerY)*fac+centerY
class Rctf(RectBase):
    xmin: ctypes.c_float
    xmax: ctypes.c_float
    ymin: ctypes.c_float
    ymax: ctypes.c_float
class Rcti(RectBase):
    xmin: ctypes.c_int
    xmax: ctypes.c_int
    ymin: ctypes.c_int
    ymax: ctypes.c_int
class View2D(StructBase): #\source\blender\makesdna\DNA_view2d_types.h
    tot:       Rctf
    cur:       Rctf
    vert:      Rcti
    hor:       Rcti
    mask:      Rcti
    min:       ctypes.c_float*2
    max:       ctypes.c_float*2
    minzoom:   ctypes.c_float
    maxzoom:   ctypes.c_float
    scroll:    ctypes.c_short
    scroll_ui: ctypes.c_short
    keeptot:   ctypes.c_short
    keepzoom:  ctypes.c_short
    def GetZoom(self):
        return (self.mask.xmax-self.mask.xmin)/(self.cur.xmax-self.cur.xmin) #Благодаря keepzoom==3, можно читать только с одной оси.

StructBase._init_structs()

viaverSkfMethod = -1 #Переключатель-пайка под успешный способ взаимодействия. Можно было и распределить по карте с версиями, но у попытки "по факту" есть свои эстетические прелести.

#Заметка: ViaVer'ы не обновлялись.
def ViaVerNewSkf(tree, isSide, ess, name):
    if viaverIsBlender4: #Todo1VV переосмыслить топологию; глобальные функции с методами и глобальная переменная, указывающая на успешную из них; с "полной пайкой защёлкиванием".
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        socketType = ess if type(ess)==str else SkConvertTypeToBlid(ess)
        match viaverSkfMethod:
            case 1: skf = tree.interface.new_socket(name, in_out={'OUTPUT' if isSide else 'INPUT'}, socket_type=socketType)
            case 2: skf = tree.interface.new_socket(name, in_out='OUTPUT' if isSide else 'INPUT', socket_type=socketType)
    else:
        skf = (tree.outputs if isSide else tree.inputs).new(ess if type(ess)==str else ess.bl_idname, name)
    return skf
def ViaVerGetSkfa(tree, isSide):
    if viaverIsBlender4:
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        match viaverSkfMethod:
            case 1: return tree.interface.ui_items
            case 2: return tree.interface.items_tree
    else:
        return (tree.outputs if isSide else tree.inputs)
def ViaVerGetSkf(tree, isSide, name):
    return ViaVerGetSkfa(tree, isSide).get(name)
def ViaVerSkfRemove(tree, isSide, name):
    if viaverIsBlender4:
        tree.interface.remove(name)
    else:
        (tree.outputs if isSide else tree.inputs).remove(name)

class Equestrian():
    set_equestrianNodeTypes = {'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT', 'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT'}
    is_simrep = property(lambda a: a.type in {'SIM','REP'})
    @staticmethod
    def IsSocketDefinitely(ess):
        base = ess.bl_rna
        while base:
            dnf = base.identifier
            base = base.base
        if dnf=='NodeSocket':
            return True
        if dnf=='Node':
            return False
        return None
    @staticmethod
    def IsSimRepCorrectSk(node, skTar):
        if (skTar.bl_idname=='NodeSocketVirtual')and(node.type in {'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT'}):
            return False
        match node.type:
            case 'SIMULATION_INPUT':
                return skTar!=node.outputs[0]
            case 'SIMULATION_OUTPUT'|'REPEAT_INPUT':
                return skTar!=node.inputs[0]
            case _:
                return True #raise Exception("IsSimRepCorrectSk() was called not for SimRep")
    def IsContainsSkf(self, skfTar):
        for skf in self.skfa: #На это нет api (или по крайней мере я не нашёл), поэтому пришлось проверять соответствие "по факту".
            if skf==skfTar:
                return True
        return False
    def GetSkfFromSk(self, skTar):
        if skTar.node!=self.node:
            raise Exception(f"Equestrian node is not equal `{skTar.path_from_id()}`")
        match self.type:
            case 'SIM'|'REP':
                match self.type: #Проверить, если сокет является "встроенным" для SimRep'а.
                    case 'SIM':
                        if self.node.type=='SIMULATION_INPUT':
                            if skTar==self.node.outputs[0]:
                                raise Exception("Socket \"Delta Time\" does not have interface.")
                        else:
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Skip\" does not have interface.")
                    case 'REP':
                        if self.node.type=='REPEAT_INPUT':
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Iterations\" does not have interface.")
                for skf in self.skfa:
                    if skf.name==skTar.name:
                        return skf
                raise Exception(f"Interface not found from `{skTar.path_from_id()}`") #Если сокет был как-то переименован у нода напрямую, а не через интерфейсы.
            case 'CLASSIC'|'GROUP':
                for skf in self.skfa:
                    if (skf.item_type=='SOCKET')and(skf.identifier==skTar.identifier):
                        return skf
    def GetSkFromSkf(self, skfTar, *, isOut):
        if not self.IsContainsSkf(skfTar):
            raise Exception(f"Equestrian items does not contain `{skfTar}`")
        match self.type:
            case 'SIM'|'REP':
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.name==skfTar.name:
                        return sk
                raise Exception(f"Not found socket for `{skfTar}`")
            case 'CLASSIC'|'GROUP':
                if skfTar.item_type=='PANEL':
                    raise Exception(f"`Panel cannot be used for search: {skfTar}`")
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.identifier==skfTar.identifier:
                        return sk
                raise Exception(f"`Socket for node side not found: {skfTar}`")
    def NewSkfFromSk(self, skTar, isFlipSide=False):
        newName = GetSkLabelName(skTar)
        match self.type:
            case 'SIM':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','GEOMETRY'}: #todo1v6 неплохо было бы отреветь где они находятся, а не хардкодить.
                    raise Exception(f"Socket type is not supported by Simulation: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            case 'REP':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL'}:
                    raise Exception(f"Socket type is not supported by Repeating: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            case 'CLASSIC'|'GROUP':
                skfNew = self.skfa.data.new_socket(newName, socket_type=SkConvertTypeToBlid(skTar), in_out='OUTPUT' if (skTar.is_output^isFlipSide) else 'INPUT')
                skfNew.hide_value = skTar.hide_value
                if hasattr(skfNew,'default_value'):
                    skfNew.default_value = skTar.default_value
                    if hasattr(skfNew,'min_value'):
                        nd = skTar.node
                        if (nd.type in {'GROUP_INPUT', 'GROUP_OUTPUT'})or( (nd.type=='GROUP')and(nd.node_tree) ): #Если сокет от другой группы нодов, то полная копия.
                            skf = Equestrian(nd).GetSkfFromSk(skTar)
                            for pr in skfNew.rna_type.properties:
                                if not(pr.is_readonly or pr.is_registered):
                                    setattr(skfNew, pr.identifier, getattr(skf, pr.identifier))
                    #tovo2v6 карта замен блида сокета для `skfNew.subtype =`.
                    #Todo0 нужно придумать как внедриться до создания, чтобы у всех групп появился сокет со значением сразу же от sfk default. Как это делает сам Blender?
                    def FixInTree(tree):
                        for nd in tree.nodes:
                            if (nd.type=='GROUP')and(nd.node_tree==self.tree):
                                for sk in nd.inputs:
                                    if sk.identifier==skfNew.identifier:
                                        sk.default_value = skTar.default_value
                    for ng in bpy.data.node_groups:
                        if IsClassicTreeBlid(ng.bl_idname):
                            FixInTree(ng)
                    for att in ('materials','scenes','worlds','textures','lights','linestyles'): #Это все или я кого-то забыл?
                        for dt in getattr(bpy.data, att):
                            if dt.node_tree: #Для materials -- https://github.com/ugorek000/VoronoiLinker/issues/19; Я так и не понял, каким образом оно может быть None.
                                FixInTree(dt.node_tree)
                return skfNew
    def MoveBySkfs(self, skfFrom, skfTo, *, isSwap=False): #Можно было бы и взять на себя запары с "BySks", но это уже забота вызывающей стороны.
        match self.type:
            case 'SIM'|'REP':
                inxFrom = -1
                inxTo = -1
                #См. проверку наличия skf в GetSkFromSkf().
                for cyc, skf in enumerate(self.skfa):
                    if skf==skfFrom:
                        inxFrom = cyc
                    if skf==skfTo:
                        inxTo = cyc
                if inxFrom==-1:
                    raise Exception(f"Index not found from `{skfFrom}`")
                if inxTo==-1:
                    raise Exception(f"Index not found from `{skfTo}`")
                self.skfa.move(inxFrom, inxTo)
                if isSwap:
                    self.skfa.move(inxTo+(1-(inxTo>inxFrom)*2), inxFrom)
            case 'CLASSIC'|'GROUP':
                if not self.IsContainsSkf(skfFrom):
                    raise Exception(f"Equestrian tree is not equal for `{skfFrom}`")
                if not self.IsContainsSkf(skfTo):
                    raise Exception(f"Equestrian tree is not equal for `{skfTo}`")
                #Я не знаю способа, как по-нормальному(?) это реализовать честным образом без пересоединения от/к панелям. Хотя что-то мне подсказывает, что это единственный способ.
                list_panels = [ [None, None, None, None, ()] ]
                skfa = self.skfa
                #Запомнить панели:
                scos = {False:0, True:0}
                for skf in skfa:
                    if skf.item_type=='PANEL':
                        list_panels[-1][4] = (scos[False], scos[True])
                        list_panels.append( [None, skf.name, skf.description, skf.default_closed, (0, 0)] )
                        scos = {False:0, True:0}
                    else:
                        scos[skf.in_out=='OUTPUT'] += 1
                list_panels[-1][4] = (scos[False], scos[True])
                #Удалить панели:
                skft = skfa.data
                tgl = True
                while tgl:
                    tgl = False
                    for skf in skfa:
                        if skf.item_type=='PANEL':
                            skft.remove(skf)
                            tgl = True
                            break
                #Сделать перемещение:
                inxFrom = skfFrom.index
                inxTo = skfTo.index
                isDir = inxTo>inxFrom
                skft.move(skfa[inxFrom], inxTo+isDir)
                if isSwap:
                    skft.move(skfa[inxTo+(1-isDir*2)], inxFrom+(not isDir))
                #Восстановить панели:
                for li in list_panels[1:]:
                    li[0] = skft.new_panel(li[1], description=li[2], default_closed=li[3])
                scoSkf = 0
                scoPanel = length(list_panels)-1
                tgl = False
                for skf in reversed(skfa): #С конца, иначе по перемещённым в панели будет проходиться больше одного раза.
                    if skf.item_type=='SOCKET':
                        if (skf.in_out=='OUTPUT')and(not tgl):
                            tgl = True
                            scoSkf = 0
                            scoPanel = length(list_panels)-1
                        if scoSkf==list_panels[scoPanel][4][tgl]:
                            scoPanel -= 1
                            while (scoPanel>0)and(not list_panels[scoPanel][4][tgl]): #Панель может содержать ноль сокетов своей стороны.
                                scoPanel -= 1
                            scoSkf = 0
                        if scoPanel>0:
                            skft.move_to_parent(skf, list_panels[scoPanel][0], 0) #Из-за 'reversed(skfa)' отпала головная боль с позицией, и тут просто '0'; потрясающе удобное совпадение.
                        scoSkf += 1
    def __init__(self, snkd): #"snkd" = sk или nd.
        isSk = hasattr(snkd,'link_limit') #self.IsSocketDefinitely(snkd)
        ndEq = snkd.node if isSk else snkd
        if ndEq.type not in self.set_equestrianNodeTypes:
            raise Exception(f"Equestrian not found from `{snkd.path_from_id()}`")
        self.tree = snkd.id_data
        self.node = ndEq
        ndEq = getattr(ndEq,'paired_output', ndEq)
        match ndEq.type:
            case 'GROUP_OUTPUT'|'GROUP_INPUT':
                self.type = 'CLASSIC'
                self.skfa = ndEq.id_data.interface.items_tree
            case 'SIMULATION_OUTPUT':
                self.type = 'SIM'
                self.skfa = ndEq.state_items
            case 'REPEAT_OUTPUT':
                self.type = 'REP'
                self.skfa = ndEq.repeat_items
            case 'GROUP':
                self.type = 'GROUP'
                if not ndEq.node_tree:
                    raise Exception(f"Tree for nodegroup `{ndEq.path_from_id()}` not found, from `{snkd.path_from_id()}`")
                self.skfa = ndEq.node_tree.interface.items_tree

#dict_solderedSkLinksRaw = {}
#def SkGetSolderedLinksRaw(self): #.vl_sold_links_raw
#    return dict_solderedSkLinksRaw.get(self, [])

dict_solderedSkLinksFinal = {}
def SkGetSolderedLinksFinal(self): #.vl_sold_links_final
    return dict_solderedSkLinksFinal.get(self, [])

dict_solderedSkIsFinalLinkedCount = {}
def SkGetSolderedIsFinalLinkedCount(self): #.vl_sold_is_final_linked_cou
    return dict_solderedSkIsFinalLinkedCount.get(self, 0)

def SolderSkLinks(tree):
    def Update(dict_data, lk):
        dict_data.setdefault(lk.from_socket, []).append(lk)
        dict_data.setdefault(lk.to_socket, []).append(lk)
    #dict_solderedSkLinksRaw.clear()
    dict_solderedSkLinksFinal.clear()
    dict_solderedSkIsFinalLinkedCount.clear()
    for lk in tree.links:
        #Update(dict_solderedSkLinksRaw, lk)
        if (lk.is_valid)and not(lk.is_muted or lk.is_hidden):
            Update(dict_solderedSkLinksFinal, lk)
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.from_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.from_socket] += 1
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.to_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.to_socket] += 1

def RegisterSolderings():
    txtDoc = "Property from and only for VoronoiLinker addon."
    #bpy.types.NodeSocket.vl_sold_links_raw = property(SkGetSolderedLinksRaw)
    bpy.types.NodeSocket.vl_sold_links_final = property(SkGetSolderedLinksFinal)
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou = property(SkGetSolderedIsFinalLinkedCount)
    #bpy.types.NodeSocket.vl_sold_links_raw.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_links_final.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou.__doc__ = txtDoc
def UnregisterSolderings():
    #del bpy.types.NodeSocket.vl_sold_links_raw
    del bpy.types.NodeSocket.vl_sold_links_final
    del bpy.types.NodeSocket.vl_sold_is_final_linked_cou

#Обеспечивает поддержку свёрнутых нодов:
#Дождались таки... Конечно же не "честную поддержку". Я презираю свёрнутые ноды; и у меня нет желания шататься с округлостью, и соответствующе изменённым рисованием.
#Так что до введения api на позицию сокета, это лучшее что есть. Ждём и надеемся.
dict_collapsedNodes = {}
def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide
#Я не стал показывать развёрнутым только ближайший нод, а сделал этакий "след".
#Чтобы всё это не превращалось в хаос с постоянным "дёрганьем", и чтобы можно было провести, раскрыть, успокоиться, увидеть "текущую обстановку", проанализировать, и спокойно соединить что нужно.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, None): #Инструменты могут создавать ноды в процессе; например vptRvEeIsSavePreviewResults.
            nd.hide = dict_collapsedNodes[nd]

class Fotago(): #Found Target Goal, "а там дальше сами разберётесь".
    #def __getattr__(self, att): #Гениально. Второе после '(*args): return Vector((args))'.
    #    return getattr(self.target, att) #Но осторожнее, оно в ~5 раз медленнее.
    def __init__(self, target, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        #self.target = target
        self.tar = target
        #self.sk = target #Fotago.sk = property(lambda a:a.target)
        #self.nd = target #Fotago.nd = property(lambda a:a.target)
        self.blid = target.bl_idname #Fotago.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        #Далее нужно только для сокетов.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text #Нужен для поддержки перевода на другие языки. Получать перевод каждый раз при рисовании слишком не комильфо, поэтому паяется.

def GenFtgFromNd(nd, pos, uiScale): #Вычленено из GetNearestNodesFtg, изначально без нужды, но VLTT вынудил.
    def DistanceField(field0, boxbou): #Спасибо RayMarching'у, без него я бы до такого не допёр.
        field1 = Vec2(( (field0.x>0)*2-1, (field0.y>0)*2-1 ))
        field0 = Vec2(( abs(field0.x), abs(field0.y) ))-boxbou/2
        field2 = Vec2(( max(field0.x, 0.0), max(field0.y, 0.0) ))
        field3 = Vec2(( abs(field0.x), abs(field0.y) ))
        field3 = field3*Vec2((field3.x<=field3.y, field3.x>field3.y))
        field3 = field3*-( (field2.x+field2.y)==0.0 )
        return (field2+field3)*field1
    isReroute = nd.type=='REROUTE'
    #Технический размер рероута явно перезаписан в 4 раза меньше, чем он есть.
    #Насколько я смог выяснить, рероут в отличие от остальных нодов свои размеры при изменении uiScale не меняет. Так что ему не нужно делиться на 'uiScale'.
    ndSize = Vec2((4, 4)) if isReroute else nd.dimensions/uiScale
    #Для нода позицию в центр нода. Для рероута позиция уже в его визуальном центре
    ndCenter = RecrGetNodeFinalLoc(nd).copy() if isReroute else RecrGetNodeFinalLoc(nd)+ndSize/2*Vec2((1.0, -1.0))
    if nd.hide: #Для VHT, "шустрый костыль" из имеющихся возможностей.
        ndCenter.y += ndSize.y/2-10 #Нужно быть аккуратнее с этой записью(write), ибо оно может оказаться указателем напрямую, если выше нодом является рероут, (https://github.com/ugorek000/VoronoiLinker/issues/16).
    #Сконструировать поле расстояний
    vec = DistanceField(pos-ndCenter, ndSize)
    #Добавить в список отработанный нод
    return Fotago(nd, dist=vec.length, pos=pos-vec)
def GetNearestNodesFtg(nodes, samplePos, uiScale, includePoorNodes=True): #Выдаёт список ближайших нод. Честное поле расстояний.
    #Почти честное. Скруглённые уголки не высчитываются. Их отсутствие не мешает, а вычисление требует больше телодвижений. Поэтому выпендриваться нет нужды.
    #С другой стороны скруглённость актуальна для свёрнутых нод, но я их презираю, так что...
    ##
    #Рамки пропускаются, ибо ни одному инструменту они не нужны.
    #Ноды без сокетов -- как рамки; поэтому можно игнорировать их ещё на этапе поиска.
    return sorted([GenFtgFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.dist)

#Уж было я хотел добавить велосипедную структуру ускорения, но потом внезапно осознал, что ещё нужна информация и о "вторых ближайших". Так что кажись без полной обработки никуда.
#Если вы знаете, как можно это ускорить с сохранением информации, поделитесь со мной.
#С другой стороны, за всё время существования аддона не было ни одной стычки с производительностью, так что... только ради эстетики.
#А ещё нужно учитывать свёрнутые ноды, пропади они пропадом, которые могут раскрыться в процессе, наворачивая всю прелесть кеширования.

def GenFtgsFromPuts(nd, isSide, samplePos, uiScale): #Вынесено для vptRvEeSksHighlighting.
    #Заметка: Эта функция сама должна получить сторону от метки, ибо `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    list_result = []
    ndDim = Vec2(nd.dimensions/uiScale) #"nd.dimensions" уже содержат в себе корректировку на масштаб интерфейса, поэтому вернуть их обратно в мир.
    for sk in nd.outputs if isSide else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (sk.enabled)and(not sk.hide):
            pos = SkGetLocVec(sk)/uiScale #Чорт возьми, это офигенно. Долой велосипедный кринж прошлых версий.
            #Но api на высоту макета у сокета тем более нет, так что остаётся только точечно-костылить; пока не придумается что-то ещё.
            hei = 0
            if (not isSide)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if "VectorDirection" in str(sk.rna_type):
                    hei = 2
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not viaverIsBlender4) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3 #todo1v6 ctypes, flag==1024
            boxHeiBound = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = TranslateIface(GetSkLabelName(sk)) if sk.bl_idname!='NodeSocketVirtual' else TranslateIface("Virtual" if not sk.name else GetSkLabelName(sk))
            list_result.append(Fotago(sk, dist=(samplePos-pos).length, pos=pos, dir= 1 if sk.is_output else -1 , boxHeiBound=boxHeiBound, text=txt))
    return list_result
def GetNearestSocketsFtg(nd, samplePos, uiScale): #Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного. Всё верно, аддон назван именно из-за этого.
    #Если рероут, то имеем тривиальный вариант, не требующий вычисления; вход и выход всего одни, позиции сокетов -- он сам
    if nd.type=='REROUTE':
        loc = RecrGetNodeFinalLoc(nd)
        L = lambda a: Fotago(a, dist=(samplePos-loc).length, pos=loc, dir=1 if a.is_output else -1, boxHeiBound=(-1, -1), text=nd.label if nd.label else TranslateIface(a.name))
        return [L(nd.inputs[0])], [L(nd.outputs[0])]
    list_ftgSksIn = GenFtgsFromPuts(nd, False, samplePos, uiScale)
    list_ftgSksOut = GenFtgsFromPuts(nd, True, samplePos, uiScale)
    list_ftgSksIn.sort(key=lambda a:a.dist)
    list_ftgSksOut.sort(key=lambda a:a.dist)
    return list_ftgSksIn, list_ftgSksOut

#На самых истоках весь аддон создавался только ради этого инструмента. А то-то вы думаете названия одинаковые.
#Но потом я подахренел от обузданных возможностей, и меня понесло... понесло на создание мейнстримной троицы. Но этого оказалось мало, и теперь инструментов больше чем 7. Чума!
#Дублирующие комментарии есть только здесь (и в целом по убыванию). При спорных ситуациях обращаться к VLT для подражания, как к истине в последней инстанции.
class VoronoiLinkerTool(VoronoiToolPairSk): #Святая святых. То ради чего. Самый первый. Босс всех инструментов. Во славу великому полю расстояния!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSkOut, self.fotagoSkIn, sideMarkHh=-1, isClassicFlow=True)
    @staticmethod
    def SkPriorityIgnoreCheck(sk): #False -- игнорировать.
        #Эта функция была добавлена по запросам извне (как и VLNST).
        set_ndBlidsWithAlphaSk = {'ShaderNodeTexImage', 'GeometryNodeImageTexture', 'CompositorNodeImage', 'ShaderNodeValToRGB', 'CompositorNodeValToRGB'}
        if sk.node.bl_idname in set_ndBlidsWithAlphaSk:
            return sk.name!="Alpha" #sk!=sk.node.outputs[1]
        return True
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): #Todo0NA ToolAssignmentFirst, Next, /^Root/; несколько NA(), нод сокет на первый, нод сокет на второй.
        #В случае не найденного подходящего предыдущий выбор остаётся, отчего не получится вернуть курсор обратно и "отменить" выбор, что очень неудобно.
        self.fotagoSkIn = None #Поэтому обнуляется каждый раз перед поиском.
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    if (self.isFirstCling)or(ftg.blid!='NodeSocketVirtual')and( (not prefs.vltPriorityIgnoring)or(self.SkPriorityIgnoreCheck(ftg.tar)) ):
                        self.fotagoSkOut = ftg
                        break
            self.isFirstCling = True
            #Получить вход по условиям:
            skOut = FtgGetTargetOrNone(self.fotagoSkOut)
            if skOut: #Первый заход всегда isFirstActivation==True, однако нод может не иметь выходов.
                #Заметка: Нод сокета активации инструмента (isFirstActivation==True) в любом случае нужно разворачивать.
                #Свёрнутость для рероутов работает, хоть и не отображается визуально; но теперь нет нужды обрабатывать, ибо поддержка свёрнутости введена.
                CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
                #На этом этапе условия для отрицания просто найдут другой результат. "Прицепится не к этому, так к другому".
                for ftg in list_ftgSksIn:
                    #Заметка: Оператор `|=` всё равно заставляет вычисляться правый операнд.
                    skIn = ftg.tar
                    #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет с обеих сторон, минуя различные типы
                    tgl = self.SkBetweenFieldsCheck(skIn, skOut)or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(prefs.vltReroutesCanInAnyType)
                    #Работа с интерфейсами переехала в VIT, теперь только между виртуальными
                    tgl = (tgl)or( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') )
                    #Если имена типов одинаковые
                    tgl = (tgl)or(skIn.bl_idname==skOut.bl_idname) #Заметка: Включая аддонские сокеты.
                    #Если аддонские сокеты в классических деревьях -- можно и ко всем классическим, классическим можно ко всем аддонским
                    tgl = (tgl)or(self.isInvokeInClassicTree)and(IsClassicSk(skOut)^IsClassicSk(skIn))
                    #Заметка: SkBetweenFieldsCheck() проверяет только меж полями, поэтому явная проверка одинаковости `bl_idname`.
                    if tgl:
                        self.fotagoSkIn = ftg
                        break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
                #На этом этапе условия для отрицания сделают результат никаким. Типа "Ничего не нашлось"; и будет обрабатываться соответствующим рисованием.
                if self.fotagoSkIn:
                    if self.fotagoSkOut.tar.node==self.fotagoSkIn.tar.node: #Если для выхода ближайший вход -- его же нод
                        self.fotagoSkIn = None
                    elif self.fotagoSkOut.tar.vl_sold_is_final_linked_cou: #Если выход уже куда-то подсоединён, даже если это выключенные линки (но из-за пайки их там нет).
                        for lk in self.fotagoSkOut.tar.vl_sold_links_final:
                            if lk.to_socket==self.fotagoSkIn.tar: #Если ближайший вход -- один из подсоединений выхода, то обнулить => "желаемое" соединение уже имеется.
                                self.fotagoSkIn = None
                                #Используемый в проверке выше "self.fotagoSkIn" обнуляется, поэтому нужно выходить, иначе будет попытка чтения из несуществующего элемента следующей итерацией.
                                break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkIn, flag=False) #"Мейнстримная" обработка свёрнутости.
            break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
    def ModalMouseNext(self, event, prefs):
        if event.type==prefs.vltRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState: #Дублирование от ниже. Не знаю как придумать это за один заход.
                self.NextAssignmentRoot(True)
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState: #Заметка: Требует существования, забота вызывающей стороны.
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    if event.value=='RELEASE':
                        return True
        return False
    def MatterPurposePoll(self):
        return self.fotagoSkOut and self.fotagoSkIn
    def MatterPurposeTool(self, event, prefs, tree):
        sko = self.fotagoSkOut.tar
        ski = self.fotagoSkIn.tar
        ##
        tree.links.new(sko, ski) #Самая важная строчка снова стала низкоуровневой.
        ##
        if ski.is_multi_input: #Если мультиинпут, то реализовать адекватный порядок подключения.
            #Моя личная хотелка, которая чинит странное поведение, и делает его логически-корректно-ожидаемым. Накой смысол последние соединённые через api лепятся в начало?
            list_skLinks = []
            for lk in ski.vl_sold_links_final:
                #Запомнить все имеющиеся линки по сокетам, и удалить их:
                list_skLinks.append((lk.from_socket, lk.to_socket, lk.is_muted))
                tree.links.remove(lk)
            #До версии b3.5 обработка ниже нужна была, чтобы новый io группы дважды не создавался.
            #Теперь без этой обработки Блендер или крашнется, или линк из виртуального в мультиинпут будет невалидным
            if sko.bl_idname=='NodeSocketVirtual':
                sko = sko.node.outputs[-2]
            tree.links.new(sko, ski) #Соединить очередной первым.
            for li in list_skLinks: #Восстановить запомненные. #todo0VV для поддержки старых версий: раньше было [:-1], потому что последний в списке уже являлся желанным, что был соединён строчкой выше.
                tree.links.new(li[0], li[1]).is_muted = li[2]
        VlrtRememberLastSockets(sko, ski) #Запомнить сокеты для VLRT, которые теперь являются "последними использованными".
        if prefs.vltSelectingInvolved:
            for nd in tree.nodes:
                nd.select = False
            sko.node.select = True
            ski.node.select = True
            tree.nodes.active = sko.node #P.s. не знаю, почему именно он; можно было и от ski. А делать из этого опцию как-то так себе.
    def InitTool(self, event, prefs, tree):
        self.fotagoSkOut = None
        self.fotagoSkIn = None
        self.repickState = False
        self.isFirstCling = False #Для SkPriorityIgnoreCheck и перевобора на виртуальные.
        if prefs.vltDeselectAllNodes:
            bpy.ops.node.select_all(action='DESELECT')
            tree.nodes.active = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vltRepickKey')
        LyAddLeftProp(col, prefs,'vltReroutesCanInAnyType')
        LyAddLeftProp(col, prefs,'vltDeselectAllNodes')
        LyAddLeftProp(col, prefs,'vltPriorityIgnoring')
        LyAddLeftProp(col, prefs,'vltSelectingInvolved')

SmartAddToRegAndAddToKmiDefs(VoronoiLinkerTool, "###_RIGHTMOUSE") #"##A_RIGHTMOUSE"?
dict_setKmiCats['grt'].add(VoronoiLinkerTool.bl_idname)

fitVltPiDescr = "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vltRepickKey: bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    vltReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be connected to any type", default=True)
    vltDeselectAllNodes:     bpy.props.BoolProperty(name="Deselect all nodes on activate",        default=False)
    vltPriorityIgnoring:     bpy.props.BoolProperty(name="Priority ignoring",                     default=False, description=fitVltPiDescr)
    vltSelectingInvolved:    bpy.props.BoolProperty(name="Selecting involved nodes",              default=False)

dict_toolLangSpecifDataPool[VoronoiLinkerTool, ru_RU] = "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника."

#Fast mathematics.
#Get a GCD with the desired operation and automatic connection to the sockets, thanks to the power of VL'A.
#Unexpectedly for me it turned out that the pie could draw a regular layout. From which I added an additional type of pie "for control".
#And I myself will use it myself, because during the time that is saved with a double pie, somehow it still cannot be relaxed.

#The important aesthetic value of a double pie is visual non -reloading options. Instead of dumping everything at once, they show only 8 pieces at a time.

#Todo00 with the advent of popularity, see who uses a quick pie, and then annihize it as unnecessary; It was pointless to crucify about him. MB Poll (Voting) do on BA.
#Notice for me: keep the support of a double pie to the hell, for aesthetics. But I want to cut it every time more than D:

#It would be thoughtless to scatter them as it hit, so I tried to observe some logical sequence. For example, arranging pairs in meaning diametrically opposite.
#The blender pie has elements as follows: left, right, bottom, top, after which the classic constructive filling.
#"Compatible ..." - so that the vectors and mathematics have the same operations in the same places (except trigonometric).
#With the exception of primitives, where super obvious logic is traced (right - plus - add, left - minus - sub; everything is on the numerical axis), left and bottom are simpler than the back side.
#For example, Length is easier than Distance. All the rest are not obvious and not oriented as it turned out.

fitVstModeItems = ( ('SWAP', "Swap",     "All links from the first socket will be on the second, from the second on the first"),
                    ('ADD',  "Add",      "Add all links from the second socket to the first one"),
                    ('TRAN', "Transfer", "Move all links from the second socket to the first one with replacement") )
class VoronoiSwapperTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode:     bpy.props.EnumProperty(name="Mode", default='SWAP', items=fitVstModeItems)
    isCanAnyType: bpy.props.BoolProperty(name="Can swap with any socket type", default=False)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            #За основу были взяты критерии от Миксера.
            if isFirstActivation:
                ftgSkOut, ftgSkIn = None, None
                for ftg in list_ftgSksOut: #todo0NA да это же Findanysk!?
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkOut = ftg
                        break
                for ftg in list_ftgSksIn:
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkIn = ftg
                        break
                #Разрешить возможность "добавлять" и для входов тоже, но только для мультиинпутов, ибо очевидное
                if (self.toolMode=='ADD')and(ftgSkIn):
                    #Проверка по типу, но не по 'is_multi_input', чтобы из обычного в мультиинпут можно было добавлять.
                    if (ftgSkIn.blid not in ('NodeSocketGeometry','NodeSocketString')):#or(not ftgSkIn.tar.is_multi_input): #Без второго условия больше возможностей.
                        ftgSkIn = None
                self.fotagoSk0 = MinFromFtgs(ftgSkOut, ftgSkIn)
            #Здесь вокруг аккумулировалось много странных проверок с None и т.п. -- результат соединения вместе многих типа высокоуровневых функций, что я понаизобретал.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut if skOut0.is_output else list_ftgSksIn:
                    if ftg.blid=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.bl_idname==ftg.blid)or(self.SkBetweenFieldsCheck(skOut0, ftg.tar)):
                        self.fotagoSk1 = ftg
                    if self.fotagoSk1: #В случае успеха прекращать поиск.
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                    self.fotagoSk1 = None
                    break #Ломать для isCanAnyType, когда isFirstActivation==False и сокет оказался самокопией; чтобы не находил сразу два нода.
                if not self.isCanAnyType:
                    if not(self.fotagoSk1 or isFirstActivation): #Если нет результата, продолжаем искать.
                        continue
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            break
    def MatterPurposePoll(self):
        return self.fotagoSk0 and self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        skIo0 = self.fotagoSk0.tar
        skIo1 = self.fotagoSk1.tar
        match self.toolMode:
            case 'SWAP':
                #Поменять местами все соединения у первого и второго сокета:
                list_memSks = []
                if skIo0.is_output: #Проверка одинаковости is_output -- забота для NextAssignmentTool().
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  Чтобы линк от нода не создался сам в себя. Проверять нужно у всех и таковые не обрабатывать.
                            list_memSks.append(lk.to_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.to_node!=skIo0.node: # T 0  ^
                            tree.links.new(skIo0, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Для мультиинпутов удалить.
                                tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(skIo1, li)
                else:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            list_memSks.append(lk.from_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.from_node!=skIo0.node: # F 0  ^
                            tree.links.new(lk.from_socket, skIo0)
                            tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(li, skIo1)
            case 'ADD'|'TRAN':
                #Просто добавить линки с первого сокета на второй. Aka объединение, добавление.
                if self.toolMode=='TRAN':
                    #Тоже самое, как и добавление, только с потерей связей у первого сокета.
                    for lk in skIo1.vl_sold_links_final:
                        tree.links.remove(lk)
                if skIo0.is_output:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  ^
                            tree.links.new(skIo1, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Без этого lk всё равно указывает на "добавленный" линк, от чего удаляется. Поэтому явная проверка для мультиинпутов.
                                tree.links.remove(lk)
                else: #Добавлено ради мультиинпутов.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            tree.links.new(lk.from_socket, skIo1)
                            tree.links.remove(lk)
        #VST VLRT же без нужды, да ведь?

SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':'SWAP'})
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':'ADD'})
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "#CA_S", {'toolMode':'TRAN'})
dict_setKmiCats['oth'].add(VoronoiSwapperTool.bl_idname)

dict_toolLangSpecifDataPool[VoronoiSwapperTool, ru_RU] = """Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.
Для линка обмена не будет, если в итоге он окажется исходящим из своего же нода."""
dict_toolLangSpecifDataPool[VoronoiSwapperTool, zh_CN] = "Alt是批量替换输出端口,Shift是互换端口"

#Нужен только для наведения порядка и эстетики в дереве.
#Для тех, кого (например меня) напрягают "торчащие без дела" пустые сокеты выхода, или нулевые (чьё значение 0.0, чёрный, и т.п.) незадействованные сокеты входа.
fitVhtModeItems = ( ('NODE',      "Auto-node",    "Automatically processing of hiding of sockets for a node"),
                    ('SOCKET',    "Socket",       "Hiding the socket"),
                    ('SOCKETVAL', "Socket value", "Switching the visibility of a socket contents") )
class VoronoiHiderTool(VoronoiToolAny):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVhtModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE')
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoAny = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            self.fotagoAny = ftgNd
            match self.toolMode:
                case 'SOCKET'|'SOCKETVAL':
                    #Для режима сокетов обработка свёрнутости такая же, как у всех.
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
                    def GetNotLinked(list_ftgSks): #Findanysk.
                        for ftg in list_ftgSks:
                            if not ftg.tar.vl_sold_is_final_linked_cou:
                                return ftg
                    ftgSkIn = GetNotLinked(list_ftgSksIn)
                    ftgSkOut = GetNotLinked(list_ftgSksOut)
                    if self.toolMode=='SOCKET':
                        self.fotagoAny = MinFromFtgs(ftgSkOut, ftgSkIn)
                    else:
                        self.fotagoAny = ftgSkIn
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.
                case 'NODE':
                    #Для режима нод нет разницы, раскрывать все подряд под курсором, или нет.
                    if prefs.vhtIsToggleNodesOnDrag:
                        if self.firstResult is None:
                            #Если активация для нода ничего не изменила, то для остальных хочется иметь сокрытие, а не раскрытие. Но текущая концепция не позволяет,
                            # информации об этом тупо нет. Поэтому реализовал это точечно вовне (здесь), а не модификацией самой реализации.
                            LGetVisSide = lambda puts: [sk for sk in puts if sk.enabled and not sk.hide]
                            list_visibleSks = [LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]
                            self.firstResult = HideFromNode(prefs, nd, True)
                            HideFromNode(prefs, nd, self.firstResult, True) #Заметка: Изменить для нода (для проверки ниже), но не трогать 'self.firstResult'.
                            if list_visibleSks==[LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]:
                                self.firstResult = True
                        HideFromNode(prefs, nd, self.firstResult, True)
                        #См. в вики, почему опция isReDrawAfterChange была удалена.
                        #Todo0v6SF Единственное возможное решение, так это сделать изменение нода _после_ отрисовки одного кадра.
                        #^ Т.е. цепляться к новому ноду на один кадр, а потом уже обработать его сразу с поиском нового нода и рисовки к нему (как для примера в вики).
            break
    def MatterPurposeTool(self, event, prefs, tree):
        match self.toolMode:
            case 'NODE':
                if not prefs.vhtIsToggleNodesOnDrag:
                    #Во время сокрытия сокета нужно иметь информацию обо всех, поэтому выполняется дважды. В первый заход собирается, во второй выполняется.
                    HideFromNode(prefs, self.fotagoAny.tar, HideFromNode(prefs, self.fotagoAny.tar, True), True)
            case 'SOCKET':
                self.fotagoAny.tar.hide = True
            case 'SOCKETVAL':
                self.fotagoAny.tar.hide_value = not self.fotagoAny.tar.hide_value
    def InitTool(self, event, prefs, tree):
        self.firstResult = None #Получить действие у первого нода "свернуть" или "развернуть", а потом транслировать его на все остальные попавшиеся.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddHandSplitProp(col, prefs,'vhtHideBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtHideHiddenBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtNeverHideGeometry')
        LyAddHandSplitProp(col, prefs,'vhtIsUnhideVirtual', forceBoolean=2)
        LyAddLeftProp(col, prefs,'vhtIsToggleNodesOnDrag')

SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':'SOCKET'})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "##A_E", {'toolMode':'SOCKETVAL'})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "#C#_E", {'toolMode':'NODE'})
dict_setKmiCats['oth'].add(VoronoiHiderTool.bl_idname)

list_itemsProcBoolSocket = [('ALWAYS',"Always","Always"), ('IF_FALSE',"If false","If false"), ('NEVER',"Never","Never"), ('IF_TRUE',"If true","If true")]

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vhtHideBoolSocket:       bpy.props.EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=list_itemsProcBoolSocket)
    vhtHideHiddenBoolSocket: bpy.props.EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=list_itemsProcBoolSocket)
    vhtNeverHideGeometry:    bpy.props.EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False","False"), ('ONLY_FIRST',"Only first","Only first"), ('TRUE',"True","True") ))
    vhtIsUnhideVirtual:      bpy.props.BoolProperty(name="Unhide virtual sockets",           default=False)
    vhtIsToggleNodesOnDrag:  bpy.props.BoolProperty(name="Toggle nodes on drag",             default=True)

dict_toolLangSpecifDataPool[VoronoiHiderTool, ru_RU] = "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов."

def HideFromNode(prefs, ndTarget, lastResult, isCanDo=False): #Изначально лично моя утилита, была создана ещё до VL.
    set_equestrianHideVirtual = {'GROUP_INPUT','SIMULATION_INPUT','SIMULATION_OUTPUT','REPEAT_INPUT','REPEAT_OUTPUT'}
    scoGeoSks = 0 #Для CheckSkZeroDefaultValue().
    def CheckSkZeroDefaultValue(sk): #Shader и Virtual всегда True, Geometry от настроек аддона.
        match sk.type: #Отсортированы в порядке убывания сложности.
            case 'GEOMETRY':
                match prefs.vhtNeverHideGeometry: #Задумывалось и для out тоже, но как-то леновато, а ещё `GeometryNodeBoundBox`, так что...
                    case 'FALSE': return True
                    case 'TRUE': return False
                    case 'ONLY_FIRST':
                        nonlocal scoGeoSks
                        scoGeoSks += 1
                        return scoGeoSks!=1
            case 'VALUE':
                #Todo1v6 когда приспичит, или будет нечем заняться -- добавить список настраиваемых точечных сокрытий, через оценку с помощью питона.
                # ^ словарь[блид сокета]:{множество имён}. А ещё придумать, как пронести default_value.
                if (GetSkLabelName(sk) in {'Alpha', 'Factor'})and(sk.default_value==1): #Для некоторых float сокетов тоже было бы неплохо иметь точечную проверку.
                    return True
                return sk.default_value==0
            case 'VECTOR':
                if (GetSkLabelName(sk)=='Scale')and(sk.default_value[0]==1)and(sk.default_value[1]==1)and(sk.default_value[2]==1):
                    return True #Меня переодически напрягал 'GeometryNodeTransform', и в один прекрасной момент накопилось..
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #Заметка: `sk.default_value==(0,0,0)` не прокатит.
            case 'BOOLEAN':
                if not sk.hide_value: #Лень паять, всё обрабатывается в прямом виде.
                    match prefs.vhtHideBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match prefs.vhtHideHiddenBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
            case 'RGBA':
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #4-й компонент игнорируются, может быть любым.
            case 'INT':
                return sk.default_value==0
            case 'STRING'|'OBJECT'|'MATERIAL'|'COLLECTION'|'TEXTURE'|'IMAGE': #Заметка: STRING не такой же, как и остальные, но имеет одинаковую обработку.
                return not sk.default_value
            case _:
                return True
    if lastResult: #Результат предыдущего анализа, есть ли сокеты чьё состояние изменилось бы. Нужно для 'isCanDo'.
        def CheckAndDoForIo(puts, LMainCheck):
            success = False
            for sk in puts:
                if (sk.enabled)and(not sk.hide)and(not sk.vl_sold_is_final_linked_cou)and(LMainCheck(sk)): #Ядро сокрытия находится здесь, в первых двух проверках.
                    success |= not sk.hide #Здесь success означает будет ли оно скрыто.
                    if isCanDo:
                        sk.hide = True
            return success
        #Если виртуальные были созданы вручную, то не скрывать их. Потому что. Но если входов групп больше одного, то всё равно скрывать.
        #Изначальный смысл LVirtual -- "LCheckOver" -- проверка "над", точечные дополнительные условия. Но в ней скопились только для виртуальных, поэтому переназвал.
        isMoreNgInputs = False if ndTarget.type!='GROUP_INPUT' else length([True for nd in ndTarget.id_data.nodes if nd.type=='GROUP_INPUT'])>1
        LVirtual = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and #Смысл этой Labmda -- точечное не-сокрытие для тех, которые виртуальные,
                                   (sk.node.type in {'GROUP_INPUT','GROUP_OUTPUT'})and # у io-всадников,
                                   (sk!=( sk.node.outputs if sk.is_output else sk.node.inputs )[-1])and # и не последние (то ради чего),
                                   (not isMoreNgInputs) ) # и GROUP_INPUT в дереве всего один.
        #Ядро в трёх строчках ниже:
        success = CheckAndDoForIo(ndTarget.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LVirtual(sk)) ) #Для входов мейнстримная проверка их значений, и дополнительно виртуальные.
        if any(True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)): #Если хотя бы один сокет подсоединён вовне
            success |= CheckAndDoForIo(ndTarget.outputs, lambda sk: LVirtual(sk) ) #Для выводов актуально только проверка виртуальных, если их нодом оказался всадник.
        else:
            #Всё равно переключать последний виртуальный, даже если нет соединений вовне.
            if ndTarget.type in set_equestrianHideVirtual: #Заметка: 'GROUP_OUTPUT' бесполезен, у него всё прячется по значению.
                if ndTarget.outputs: #Вместо for, чтобы читать из последнего.
                    sk = ndTarget.outputs[-1]
                    if sk.bl_idname=='NodeSocketVirtual':
                        success |= not sk.hide #Так же, как и в CheckAndDoForIo().
                        if isCanDo:
                            sk.hide = True
        return success #Урожай от двух CheckAndDoForIo() изнутри.
    elif isCanDo: #Иначе раскрыть всё.
        success = False
        for puts in [ndTarget.inputs, ndTarget.outputs]:
            for sk in puts:
                success |= sk.hide #Здесь success означает будет ли оно раскрыто.
                sk.hide = (sk.bl_idname=='NodeSocketVirtual')and(not prefs.vhtIsUnhideVirtual)
        return success

#"Массовый линкер" -- как линкер, только много за раз (ваш кэп).
#См. вики на гитхабе, чтобы посмотреть 5 примеров использования массового линкера. Дайте мне знать, если обнаружите ещё одно необычное применение этому инструменту.

class VestData:
    list_enumProps = [] #Для пайки, и проверка перед вызовом, есть ли вообще что.
    nd = None
    boxScale = 1.0 #Если забыть установить, то хотя бы коробка не сколлапсируется в ноль.
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vestIsToggleNodesOnDrag: bpy.props.BoolProperty(name="Toggle nodes on drag", default=True)
    ##
    vestBoxScale:            bpy.props.FloatProperty(name="Box scale",           default=1.5, min=1.0, max=2.0, subtype="FACTOR")
    vestDisplayLabels:       bpy.props.BoolProperty(name="Display enum names",   default=True)
    vestDarkStyle:           bpy.props.BoolProperty(name="Dark style",           default=False)

#См.: VlrtData, VlrtRememberLastSockets() и NewLinkHhAndRemember().

def FindAnySk(nd, list_ftgSksIn, list_ftgSksOut): #Todo0NA нужно обобщение!, с лямбдой. И внешний цикл по спискам, а не два цикла.
    ftgSkOut, ftgSkIn = None, None
    for ftg in list_ftgSksOut:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)): #todo1v6 эта функция везде используется в паре с !=NodeSocketVirtual, нужно пределать топологию.
            ftgSkOut = ftg
            break
    for ftg in list_ftgSksIn:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
            ftgSkIn = ftg
            break
    return MinFromFtgs(ftgSkOut, ftgSkIn)

fitVitModeItems = ( ('COPY',   "Copy",   "Copy a socket name to clipboard"),
                    ('PASTE',  "Paste",  "Paste the contents of clipboard into an interface name"),
                    ('SWAP',   "Swap",   "Swap a two interfaces"),
                    ('FLIP',   "Flip",   "Move the interface to a new location, shifting everyone else"),
                    ('NEW',    "New",    "Create an interface using virtual sockets"),
                    ('CREATE', "Create", "Create an interface from a selected socket, and paste it into a specified location") )

class VlnstData:
    lastLastExecError = "" #Для пользовательского редактирования vlnstLastExecError, низя добавить или изменить, но можно удалить.
    isUpdateWorking = False
def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnstLastExecError = ""
    elif self.vlnstLastExecError:
        if self.vlnstLastExecError!=VlnstData.lastLastExecError: #Заметка: Остерегаться переполнения стека.
            self.vlnstLastExecError = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnstLastExecError: bpy.props.StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)

#Внезапно оказалось, что моя когдато-шняя идея для инструмента "Ленивое Продолжение" инкапсулировалось в этом инструменте. Вот так неожиданность.
#Этот инструмент, то же самое, как и ^ (где сокет и нод однозначно определял следующий нод), только для двух сокетов; и возможностей больше!

lzAny = '!any'
class LazyKey():
    def __init__(self, fnb, fst, fsn, fsg, snb=lzAny, sst=lzAny, ssn=lzAny, ssg=lzAny):
        self.firstNdBlid = fnb
        self.firstSkBlid = dict_typeSkToBlid.get(fst, fst)
        self.firstSkName = fsn
        self.firstSkGend = fsg
        self.secondNdBlid = snb
        self.secondSkBlid = dict_typeSkToBlid.get(sst, sst)
        self.secondSkName = ssn
        self.secondSkGend = ssg
class LazyNode():
    #Чёрная магия. Если в __init__(list_props=[]), то указание в одном nd.list_props += [..] меняет вообще у всех в lzSt. Нереально чёрная магия; ночные кошмары обеспечены.
    def __init__(self, blid, list_props, ofsPos=(0,0), hhoSk=0, hhiSk=0):
        self.blid = blid
        #list_props Содержит в себе обработку и сокетов тоже.
        #Указание на сокеты (в list_props и lzHh_Sk) -- +1 от индекса, а знак указывает сторону; => 0 не используется.
        self.list_props = list_props
        self.lzHhOutSk = hhoSk
        self.lzHhInSk = hhiSk
        self.locloc = Vec2(ofsPos) #"Local location"; и offset от центра мира.
class LazyStencil():
    def __init__(self, key, csn=2, name="", prior=0.0):
        self.lzkey = key
        self.prior = prior #Чем выше, тем важнее.
        self.name = name
        self.trees = {} #Это также похоже на часть ключа.
        self.isTwoSkNeeded = csn==2
        self.list_nodes = []
        self.list_links = [] #Порядковый нод / сокет, и такое же на вход.
        self.isSameLink = False
        self.txt_exec = ""

list_vlnstDataPool = []

#Database:
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VECTOR','Normal',False), 2, "Fast Color NormalMap")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeNormalMap', [], hhiSk=-2, hhoSk=1) )
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VALUE',lzAny,False), 2, "Lazy Non-Color data to float socket")
lzSt.trees = {'ShaderNodeTree'}
lzSt.isSameLink = True
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',False), 1, "NW TexCord Parody")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexImage', [(2,'hide',True)], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,0,1,0) ]
list_vlnstDataPool.append(lzSt)
lzSt = copy.deepcopy(lzSt)
lzSt.lzkey.firstSkName = "Base Color"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'VECTOR','Vector',False), 1, "NW TexCord Parody Half")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], hhoSk=-1, ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0) ]
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA',lzAny,True, lzAny,'SHADER',lzAny,False), 2, "Insert Emission")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeEmission', [], hhiSk=-1, hhoSk=1) )
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey('ShaderNodeBackground','RGBA','Color',False), 1, "World env texture", prior=1.0)
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexEnvironment', [], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeTexCoord', [('show_options',False)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,3,1,0) ]
list_vlnstDataPool.append(lzSt)
##

list_vlnstDataPool.sort(key=lambda a:a.prior, reverse=True)

def DoLazyStencil(tree, skFirst, skSecond, lzSten):
    list_result = []
    firstCenter = None
    for li in lzSten.list_nodes:
        nd = tree.nodes.new(li.blid)
        nd.location += li.locloc
        list_result.append(nd)
        for pr in li.list_props:
            if length(pr)==2:
                setattr(nd, pr[0], pr[1])
            else:
                setattr( (nd.outputs if pr[0]>0 else nd.inputs)[abs(pr[0])-1], pr[1], pr[2] )
        if li.lzHhOutSk:
            tree.links.new(nd.outputs[abs(li.lzHhOutSk)-1], skFirst if li.lzHhOutSk<0 else skSecond)
        if li.lzHhInSk:
            tree.links.new(skFirst if li.lzHhInSk<0 else skSecond, nd.inputs[abs(li.lzHhInSk)-1])
    #Для одного нода ещё и сгодилось бы, но учитывая большое разнообразие и гибкость, наверное лучше без NewLinkHhAndRemember(), соединять в сыром виде.
    for li in lzSten.list_links:
        tree.links.new(list_result[li[0]].outputs[li[1]], list_result[li[2]].inputs[li[3]])
    if lzSten.isSameLink:
        tree.links.new(skFirst, skSecond)
    return list_result
def LzCompare(a, b):
    return (a==b)or(a==lzAny)
def LzNodeDoubleCheck(zk, a, b): return LzCompare(zk.firstNdBlid,            a.bl_idname if a else "") and LzCompare(zk.secondNdBlid,            b.bl_idname if b else "")
def LzTypeDoubleCheck(zk, a, b): return LzCompare(zk.firstSkBlid, SkConvertTypeToBlid(a) if a else "") and LzCompare(zk.secondSkBlid, SkConvertTypeToBlid(b) if b else "") #Не 'type', а blid'ы; для аддонских деревьев.
def LzNameDoubleCheck(zk, a, b): return LzCompare(zk.firstSkName,      GetSkLabelName(a) if a else "") and LzCompare(zk.secondSkName,      GetSkLabelName(b) if b else "")
def LzGendDoubleCheck(zk, a, b): return LzCompare(zk.firstSkGend,            a.is_output if a else "") and LzCompare(zk.secondSkGend,            b.is_output if b else "")
def LzLazyStencil(prefs, tree, skFirst, skSecond):
    if not skFirst:
        return []
    ndOut = skFirst.node
    ndIn = skSecond.node if skSecond else None
    for li in list_vlnstDataPool:
        if (li.isTwoSkNeeded)^(not skSecond): #Должен не иметь второго для одного, или иметь для двух.
            if (not li.trees)or(tree.bl_idname in li.trees): #Должен поддерживать тип дерева.
                zk = li.lzkey
                if LzNodeDoubleCheck(zk, ndOut, ndIn): #Совпадение нод.
                    for cyc in (False, True):
                        skF = skFirst
                        skS = skSecond
                        if cyc: #Оба выхода и оба входа, но разные гендеры могут быть в разном порядке. Но перестановка имеет значение для содержания txt_exec'ов.
                            skF, skS = skSecond, skFirst
                        if LzTypeDoubleCheck(zk, skF, skS): #Совпадение Blid'ов сокетов.
                            if LzNameDoubleCheck(zk, skF, skS): #Имён/меток сокетов.
                                if LzGendDoubleCheck(zk, skF, skS): #Гендеров.
                                    result = DoLazyStencil(tree, skF, skS, li)
                                    if li.txt_exec:
                                        try:
                                            exec(li.txt_exec) #Тревога!1, А нет.. без паники, это внутреннее. Всё ещё всё в безопасности.
                                        except Exception as ex:
                                            VlnstData.lastLastExecError = str(ex)
                                            prefs.vlnstLastExecError = VlnstData.lastLastExecError
                                    return result
def VlnstLazyTemplate(prefs, tree, skFirst, skSecond, cursorLoc):
    list_nodes = LzLazyStencil(prefs, tree, skFirst, skSecond)
    if list_nodes:
        bpy.ops.node.select_all(action='DESELECT')
        firstOffset = cursorLoc-list_nodes[0].location
        for nd in list_nodes:
            nd.select = True
            nd.location += firstOffset
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')

class VoronoiDummyTool(VoronoiToolSk): #Шаблон для быстро-удобного(?) добавления нового инструмента.
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    usefulnessForCustomTree = True
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            ftgSkIn = list_ftgSksIn[0] if list_ftgSksIn else None
            ftgSkOut = list_ftgSksOut[0] if list_ftgSksOut else None
            self.fotagoSk = MinFromFtgs(ftgSkOut, ftgSkIn)
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk, flag=False)
            break
        #todo0NA Я придумал что делать с концепцией, когда имеются разные критерии от isFirstActivation'а, и второй находится сразу рядом после первого моментально. Явное (и насильное) сравнение на своего и отмена.
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def MatterPurposeTool(self, event, prefs, tree):
        sk = self.fotagoSk.tar
        sk.name = sk.name if (sk.name)and(sk.name[0]=="\"") else f'"{sk.name}"'
        sk.node.label = "Hi i am vdt. See source code"
        VlrtRememberLastSockets(sk if sk.is_output else None, None)
    def InitTool(self, event, prefs, tree):
        self.fotagoSk = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddNiceColorProp(col, prefs,'vdtDummy')

#SmartAddToRegAndAddToKmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})
dict_setKmiCats['grt'].add(VoronoiDummyTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vdtDummy: bpy.props.StringProperty(name="Dummy", default="Dummy")

dict_toolLangSpecifDataPool[VoronoiDummyTool, ru_RU] = """"Ой дурачёк"."""

# =======

def GetVlKeyconfigAsPy(): #Взято из 'bl_keymap_utils.io'. Понятия не имею, как оно работает.
    def Ind(num):
        return " "*num
    def keyconfig_merge(kc1, kc2):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1!=kc2:
            merged_keymaps.extend(
                (km, kc2)
                for km in kc2.keymaps
                if km.name not in kc1_names)
        return merged_keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.active
    class FakeKeyConfig:
        keymaps = []
    edited_kc = FakeKeyConfig()
    edited_kc.keymaps.append(GetUserKmNe())
    if kc!=wm.keyconfigs.default:
        export_keymaps = keyconfig_merge(edited_kc, kc)
    else:
        export_keymaps = keyconfig_merge(edited_kc, edited_kc)
    ##
    result = ""
    result += "list_keyconfigData = \\\n["
    sco = 0
    for km, _kc_x in export_keymaps:
        km = km.active()
        result += "("
        result += f"\"{km.name:s}\","+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"space_type\": '{km.space_type:s}'"
        result += f", \"region_type\": '{km.region_type:s}'"
        isModal = km.is_modal
        if isModal:
            result += ", \"modal\": True"
        result += "},"+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"items\":"+"\n"
        result += f"{Ind(3)}["
        for kmi in km.keymap_items:
            if not kmi.idname.startswith("node.voronoi_"):
                continue
            sco += 1
            if isModal:
                kmi_id = kmi.propvalue
            else:
                kmi_id = kmi.idname
            result += f"("
            kmi_args = bl_keymap_utils.io.kmi_args_as_data(kmi)
            kmi_data = bl_keymap_utils.io._kmi_attrs_or_none(4, kmi)
            result += f"\"{kmi_id:s}\""
            if kmi_data is None:
                result += f", "
            else:
                result += ",\n" f"{Ind(5)}"
            result += kmi_args
            if kmi_data is None:
                result += ", None),"+"\n"
            else:
                result += ","+"\n"
                result += f"{Ind(5)}" "{"
                result += kmi_data
                result += f"{Ind(6)}"
                result += "},\n" f"{Ind(5)}"
                result += "),"+"\n"
            result += f"{Ind(4)}"
        result += "],\n" f"{Ind(3)}"
        result += "},\n" f"{Ind(2)}"
        result += "),\n" f"{Ind(1)}"
    result += "]"+" #kmi count: "+str(sco)+"\n"
    result += "\n"
    result += "if True:"+"\n"
    result += "    import bl_keymap_utils"+"\n"
    result += "    import bl_keymap_utils.versioning"+"\n" #Чёрная магия; кажется, такая же как и с "gpu_extras".
    result += "    kc = bpy.context.window_manager.keyconfigs.active"+"\n"
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})"+"\n"
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result
def GetVaSettAsPy(prefs):
    set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'dsIsFieldDebug', 'dsIsTestDrawing', #tovo2v6 все ли?
                             'vaKmiMainstreamDiscl', 'vaKmiOtjersDiscl', 'vaKmiSpecialDiscl', 'vaKmiQqmDiscl', 'vaKmiCustomDiscl'}
    for cls in dict_vtClasses:
        set_ignoredAddonPrefs.add(cls.disclBoxPropName)
        set_ignoredAddonPrefs.add(cls.disclBoxPropNameInfo)
    txt_vasp = ""
    txt_vasp += "#Exported/Importing addon settings for Voronoi Linker v"+txtAddonVer+"\n"
    import datetime
    txt_vasp += f"#Generated "+datetime.datetime.now().strftime("%Y.%m.%d")+"\n"
    txt_vasp += "\n"
    txt_vasp += "import bpy\n"
    #Сконструировать изменённые настройки аддона:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{voronoiAddonName}'].preferences"+"\n\n"
    txt_vasp += "def SetProp(att, val):"+"\n"
    txt_vasp += "    if hasattr(prefs, att):"+"\n"
    txt_vasp += "        setattr(prefs, att, val)"+"\n\n"
    def AddAndProc(txt):
        nonlocal txt_vasp
        len = txt.find(",")
        txt_vasp += txt.replace(", ",","+" "*(42-len), 1)
    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            #'_BoxDiscl'ы не стал игнорировать, пусть будут.
            if pr.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(pr,'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(pr.default_array, getattr(prefs, pr.identifier)) if li[0]!=li[1]]
                else:
                    isDiff = pr.default!=getattr(prefs, pr.identifier)
                if (True)or(isDiff): #Наверное сохранять только разницу небезопасно, вдруг не сохранённые свойства изменят своё значение по умолчанию.
                    if isArray:
                        #txt_vasp += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                        list_vals = [str(li)+"," for li in getattr(prefs, pr.identifier)]
                        list_vals[-1] = list_vals[-1][:-1]
                        AddAndProc(f"SetProp('{pr.identifier}', ("+" ".join(list_vals)+"))\n")
                    else:
                        match pr.type:
                            case 'STRING': AddAndProc(f"SetProp('{pr.identifier}', \"{getattr(prefs, pr.identifier)}\")"+"\n")
                            case 'ENUM':   AddAndProc(f"SetProp('{pr.identifier}', '{getattr(prefs, pr.identifier)}')"+"\n")
                            case _:        AddAndProc(f"SetProp('{pr.identifier}', {getattr(prefs, pr.identifier)})"+"\n")
    #Сконструировать все VL хоткеи:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    #P.s. я не знаю, как обрабатывать только изменённые хоткеи; это выглядит слишком головной болью и дремучим лесом. #tovo0v6
    # Лень реверсинженерить '..\scripts\modules\bl_keymap_utils\io.py', поэтому просто сохранять всех.
    txt_vasp += GetVlKeyconfigAsPy() #Оно нахрен не работает; та часть, которая восстанавливает; сгенерированным скриптом ничего не сохраняется, только временный эффект.
    #Придётся ждать того героя, кто придёт и починит всё это.
    return txt_vasp

def GetFirstUpperLetters(txt):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)
def SolderClsToolNames():
    for cls in dict_vtClasses:
        cls.vlTripleName = GetFirstUpperLetters(cls.bl_label)+"T" #Изначально было создано "потому что прикольно", но теперь это нужно; см. SetPieData().
        cls.disclBoxPropName = cls.vlTripleName[:-1].lower()+"BoxDiscl"
        cls.disclBoxPropNameInfo = cls.disclBoxPropName+"Info"
SolderClsToolNames()

for cls in dict_vtClasses:
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropName}: bpy.props.BoolProperty(name=\"\", default=False)")
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropNameInfo}: bpy.props.BoolProperty(name=\"\", default=False)")

list_langDebEnumItems = []
for li in ["Free", "Special", "AddonPrefs"]+[cls.bl_label for cls in dict_vtClasses]:
    list_langDebEnumItems.append( (li.upper(), GetFirstUpperLetters(li), "") )

def VaUpdateTestDraw(self, context):
    TestDraw.Toggle(context, self.dsIsTestDrawing)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaLangDebDiscl: bpy.props.BoolProperty(name="Language bruteforce debug", default=False)
    vaLangDebEnum: bpy.props.EnumProperty(name="LangDebEnum", default='FREE', items=list_langDebEnumItems)
    dsIsFieldDebug: bpy.props.BoolProperty(name="Field debug", default=False)
    dsIsTestDrawing: bpy.props.BoolProperty(name="Testing draw", default=False, update=VaUpdateTestDraw)
    dsIncludeDev: bpy.props.BoolProperty(name="IncludeDev", default=False)

#Оставлю здесь маленький список моих личных "хотелок" (по хронологии интеграции), которые перекочевали из других моих личных аддонов в VL:
#Hider
#QuckMath и JustMathPie
#Warper
#RANTO

def Prefs():
    return bpy.context.preferences.addons[voronoiAddonName].preferences

class VoronoiOpAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    bl_description = "VL's addon tab" #todo1v6 придумать, как перевести для каждой вкладки разное.
    opt: bpy.props.StringProperty()
    def invoke(self, context, event):
        #if not self.opt: return {'CANCELLED'}
        prefs = Prefs()
        match self.opt:
            case 'GetPySett':
                context.window_manager.clipboard = GetVaSettAsPy(prefs)
            case 'AddNewKmi':
                GetUserKmNe().keymap_items.new("node.voronoi_",'D','PRESS').show_expanded = True
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

def LyAddThinSep(where, scaleY):
    row = where.row(align=True)
    row.separator()
    row.scale_y = scaleY

class KmiCat():
    def __init__(self, propName='', set_kmis=set(), set_idn=set()):
        self.propName = propName
        self.set_kmis = set_kmis
        self.set_idn = set_idn
        self.sco = 0
class KmiCats:
    pass

vaUpdateSelfTgl = False
def VaUpdateDecorColSk(self, _context):
    global vaUpdateSelfTgl
    if vaUpdateSelfTgl:
        return
    vaUpdateSelfTgl = True
    self.vaDecorColSk = self.vaDecorColSkBack
    vaUpdateSelfTgl = False

fitTabItems = ( ('SETTINGS',"Settings",""), ('APPEARANCE',"Appearance",""), ('DRAW',"Draw",""), ('KEYMAP',"Keymap",""), ('INFO',"Info","") )#, ('DEV',"Dev","")
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaUiTabs: bpy.props.EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=fitTabItems)
    vaInfoRestore:     bpy.props.BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    #Box disclosures:
    vaKmiMainstreamDiscl: bpy.props.BoolProperty(name="The Great Trio ", default=True) #Заметка: Пробел важен для переводов.
    vaKmiOtjersDiscl:     bpy.props.BoolProperty(name="Others ", default=False)
    vaKmiSpecialDiscl:    bpy.props.BoolProperty(name="Specials ", default=False)
    vaKmiQqmDiscl:        bpy.props.BoolProperty(name="Quick quick math ", default=False)
    vaKmiCustomDiscl:     bpy.props.BoolProperty(name="Custom ", default=True)
    ##
    vaDecorLy:        bpy.props.FloatVectorProperty(name="DecorForLayout",   default=(0.01, 0.01, 0.01),   min=0, max=1, size=3, subtype='COLOR')
    vaDecorColSk:     bpy.props.FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=VaUpdateDecorColSk)
    vaDecorColSkBack: bpy.props.FloatVectorProperty(name="vaDecorColSkBack", default=(1.0, 1.0, 1.0, 1.0), min = 0, max=1, size=4, subtype='COLOR')

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    dsIsDrawText:   bpy.props.BoolProperty(name="Text",        default=True) #Учитывая VHT и VEST, это уже больше просто для текста в рамке, чем для текста от сокетов.
    dsIsDrawMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsDrawPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsDrawLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsDrawSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsColoredText:   bpy.props.BoolProperty(name="Text",        default=True)
    dsIsColoredMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsColoredPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsColoredLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsColoredSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    dsIsColoredNodes:  bpy.props.BoolProperty(name="Nodes",       default=True)
    ##
    dsSocketAreaAlpha: bpy.props.FloatProperty(name="Socket area alpha", default=0.075, min=0.0, max=1.0, subtype="FACTOR")
    ##
    dsUniformColor:     bpy.props.FloatVectorProperty(name="Alternative uniform color", default=(0.632502, 0.408091, 0.174378, 0.9), min=0, max=1, size=4, subtype='COLOR') #0.65, 0.65, 0.65, 1.0
    dsUniformNodeColor: bpy.props.FloatVectorProperty(name="Alternative nodes color",   default=(0.069818, 0.054827, 0.629139, 0.9), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 0.9
    dsCursorColor:      bpy.props.FloatVectorProperty(name="Cursor color",              default=(0.730461, 0.539480, 0.964686, 1.0), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 1.0
    dsCursorColorAvailability: bpy.props.IntProperty(name="Cursor color availability", default=2, min=0, max=2, description="If a line is drawn to the cursor, color part of it in the cursor color.\n0 – Disable.\n1 – For one line.\n2 – Always")
    ##
    dsDisplayStyle: bpy.props.EnumProperty(name="Display frame style", default='CLASSIC', items=( ('CLASSIC',"Classic","Classic"), ('SIMPLIFIED',"Simplified","Simplified"), ('ONLY_TEXT',"Only text","Only text") ))
    dsFontFile:     bpy.props.StringProperty(name="Font file",    default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH') #"Пользователи Линукса негодуют".
    dsLineWidth:    bpy.props.FloatProperty( name="Line Width",   default=1.5, min=0.5, max=8.0, subtype="FACTOR")
    dsPointScale:   bpy.props.FloatProperty( name="Point scale",  default=1.0, min=0.0, max=3.0)
    dsFontSize:     bpy.props.IntProperty(   name="Font size",    default=28,  min=10,  max=48)
    dsMarkerStyle:  bpy.props.IntProperty(   name="Marker Style", default=0,   min=0,   max=2)
    ##
    dsManualAdjustment: bpy.props.FloatProperty(name="Manual adjustment",         default=-0.2, description="The Y-axis offset of text for this font") #https://blender.stackexchange.com/questions/312413/blf-module-how-to-draw-text-in-the-center
    dsPointOffsetX:     bpy.props.FloatProperty(name="Point offset X axis",       default=20.0,   min=-50.0, max=50.0)
    dsFrameOffset:      bpy.props.IntProperty(  name="Frame size",                default=0,      min=0,     max=24, subtype='FACTOR') #Заметка: Важно, чтобы это был Int.
    dsDistFromCursor:   bpy.props.FloatProperty(name="Text distance from cursor", default=25.0,   min=5.0,   max=50.0)
    ##
    dsIsAlwaysLine:        bpy.props.BoolProperty(name="Always draw line",      default=False, description="Draw a line to the cursor even from a single selected socket")
    dsIsSlideOnNodes:      bpy.props.BoolProperty(name="Slide on nodes",        default=False)
    dsIsDrawNodeNameLabel: bpy.props.BoolProperty(name="Display text for node", default=True)
    ##
    dsIsAllowTextShadow: bpy.props.BoolProperty(       name="Enable text shadow", default=True)
    dsShadowCol:         bpy.props.FloatVectorProperty(name="Shadow color",       default=(0.0, 0.0, 0.0, 0.5), min=0,   max=1,  size=4, subtype='COLOR')
    dsShadowOffset:      bpy.props.IntVectorProperty(  name="Shadow offset",      default=(2,-2),               min=-20, max=20, size=2)
    dsShadowBlur:        bpy.props.IntProperty(        name="Shadow blur",        default=2,                    min=0,   max=2)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    #Уж было я хотел добавить это, но потом мне стало таак лень. Это же нужно всё менять под "только сокеты", и критерии для нод неведомо как получать.
    #И выгода неизвестно какая, кроме эстетики. Так что ну его нахрен. "Работает -- не трогай".
    #А ещё реализация "только сокеты" где-то может грозить потенциальной кроличьей норой.
    vSearchMethod: bpy.props.EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") )) #Нигде не используется; и кажется, никогда не будет.
    vEdgePanFac: bpy.props.FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    vEdgePanSpeed: bpy.props.FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    vIsOverwriteZoomLimits: bpy.props.BoolProperty(name="Overwriting zoom limits", default=False)
    vOwZoomMin: bpy.props.FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    vOwZoomMax: bpy.props.FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    def LyDrawTabSettings(self, where):
        def LyAddAddonBoxDiscl(where, who, att, *, txt=None, isWide=False, align=False):
            colBox = where.box().column(align=True)
            if LyAddDisclosureProp(colBox, who, att, txt=txt, active=False, isWide=isWide):
                rowTool = colBox.row()
                rowTool.separator()
                return rowTool.column(align=align)
            return None
        colMain = where.column()
        LyAddThinSep(colMain, 0.1)
        for cls in dict_vtClasses:
            if cls.canDrawInAddonDiscl:
                if colDiscl:=LyAddAddonBoxDiscl(colMain, self, cls.disclBoxPropName, txt=TxtClsBlabToolSett(cls), align=True):
                    cls.LyDrawInAddonDiscl(colDiscl, self)
    def LyDrawTabAppearance(self, where):
        colMain = where.column()
        #LyAddHandSplitProp(LyAddLabeledBoxCol(colMain, text="Main"), self,'vSearchMethod')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'vEdgePanFac', text="Zoom factor")
        LyAddHandSplitProp(colBox, self,'vEdgePanSpeed', text="Speed")
        if (self.dsIncludeDev)or(self.vIsOverwriteZoomLimits):
            LyAddHandSplitProp(colBox, self,'vIsOverwriteZoomLimits', active=self.vIsOverwriteZoomLimits)
            if self.vIsOverwriteZoomLimits:
                LyAddHandSplitProp(colBox, self,'vOwZoomMin')
                LyAddHandSplitProp(colBox, self,'vOwZoomMax')
        ##
        for cls in dict_vtClasses:
            if cls.canDrawInAppearance:
                cls.LyDrawInAppearance(colMain, self)
    def LyDrawTabDraw(self, where):
        def LyAddPairProp(where, txt):
            row = where.row(align=True)
            row.prop(self, txt)
            row.active = getattr(self, txt.replace("Colored","Draw"))
        colMain = where.column()
        splDrawColor = colMain.box().split(align=True)
        splDrawColor.use_property_split = True
        colDraw = splDrawColor.column(align=True, heading='Draw')
        colDraw.prop(self,'dsIsDrawText')
        colDraw.prop(self,'dsIsDrawMarker')
        colDraw.prop(self,'dsIsDrawPoint')
        colDraw.prop(self,'dsIsDrawLine')
        colDraw.prop(self,'dsIsDrawSkArea')
        with LyAddQuickInactiveCol(colDraw, active=self.dsIsDrawText) as row:
            row.prop(self,'dsIsDrawNodeNameLabel', text="Node text") #"Text for node"
        colCol = splDrawColor.column(align=True, heading='Colored')
        LyAddPairProp(colCol,'dsIsColoredText')
        LyAddPairProp(colCol,'dsIsColoredMarker')
        LyAddPairProp(colCol,'dsIsColoredPoint')
        LyAddPairProp(colCol,'dsIsColoredLine')
        LyAddPairProp(colCol,'dsIsColoredSkArea')
        tgl = (self.dsIsDrawLine)or(self.dsIsDrawPoint)or(self.dsIsDrawText and self.dsIsDrawNodeNameLabel)
        with LyAddQuickInactiveCol(colCol, active=tgl) as row:
            row.prop(self,'dsIsColoredNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Special")
        #LyAddHandSplitProp(colBox, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
        LyAddHandSplitProp(colBox, self,'dsIsAlwaysLine')
        LyAddHandSplitProp(colBox, self,'dsIsSlideOnNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Colors")
        LyAddHandSplitProp(colBox, self,'dsSocketAreaAlpha', active=self.dsIsDrawSkArea)
        tgl = ( (self.dsIsDrawText   and not self.dsIsColoredText  )or
                (self.dsIsDrawMarker and not self.dsIsColoredMarker)or
                (self.dsIsDrawPoint  and not self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and not self.dsIsColoredLine  )or
                (self.dsIsDrawSkArea and not self.dsIsColoredSkArea) )
        LyAddHandSplitProp(colBox, self,'dsUniformColor', active=tgl)
        tgl = ( (self.dsIsDrawText   and self.dsIsColoredText  )or
                (self.dsIsDrawPoint  and self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and self.dsIsColoredLine  ) )
        LyAddHandSplitProp(colBox, self,'dsUniformNodeColor', active=(tgl)and(not self.dsIsColoredNodes))
        tgl1 = (self.dsIsDrawPoint and self.dsIsColoredPoint)
        tgl2 = (self.dsIsDrawLine  and self.dsIsColoredLine)and(not not self.dsCursorColorAvailability)
        LyAddHandSplitProp(colBox, self,'dsCursorColor', active=tgl1 or tgl2)
        LyAddHandSplitProp(colBox, self,'dsCursorColorAvailability', active=self.dsIsDrawLine and self.dsIsColoredLine)
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Customization")
        LyAddHandSplitProp(colBox, self,'dsDisplayStyle')
        LyAddHandSplitProp(colBox, self,'dsFontFile')
        if not self.dsFontFile.endswith((".ttf",".otf")):
            spl = colBox.split(factor=0.4, align=True)
            spl.label(text="")
            spl.label(text=txt_onlyFontFormat, icon='ERROR')
        LyAddThinSep(colBox, 0.5)
        LyAddHandSplitProp(colBox, self,'dsLineWidth')
        LyAddHandSplitProp(colBox, self,'dsPointScale')
        LyAddHandSplitProp(colBox, self,'dsFontSize')
        LyAddHandSplitProp(colBox, self,'dsMarkerStyle')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Advanced")
        LyAddHandSplitProp(colBox, self,'dsManualAdjustment')
        LyAddHandSplitProp(colBox, self,'dsPointOffsetX')
        LyAddHandSplitProp(colBox, self,'dsFrameOffset')
        LyAddHandSplitProp(colBox, self,'dsDistFromCursor')
        LyAddThinSep(colBox, 0.25) #Межгалкоевые отступы складываются, поэтому дополнительный отступ для выравнивания.
        LyAddHandSplitProp(colBox, self,'dsIsAllowTextShadow')
        colShadow = colBox.column(align=True)
        LyAddHandSplitProp(colShadow, self,'dsShadowCol', active=self.dsIsAllowTextShadow)
        LyAddHandSplitProp(colShadow, self,'dsShadowBlur') #Размытие тени разделяет их, чтобы не сливались вместе по середине.
        row = LyAddHandSplitProp(colShadow, self,'dsShadowOffset', returnAsLy=True).row(align=True)
        row.row().prop(self,'dsShadowOffset', text="X  ", translate=False, index=0, icon_only=True)
        row.row().prop(self,'dsShadowOffset', text="Y  ", translate=False, index=1, icon_only=True)
        colShadow.active = self.dsIsAllowTextShadow
        ##
        colDev = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.dsIsFieldDebug)or(self.dsIsTestDrawing):
            with LyAddQuickInactiveCol(colDev, active=self.dsIsFieldDebug) as row:
                row.prop(self,'dsIsFieldDebug')
            with LyAddQuickInactiveCol(colDev, active=self.dsIsTestDrawing) as row:
                row.prop(self,'dsIsTestDrawing')
    def LyDrawTabKeymaps(self, where):
        colMain = where.column()
        colMain.separator()
        rowLabelMain = colMain.row(align=True)
        rowLabel = rowLabelMain.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(icon='DOT')
        rowLabel.label(text="Node Editor")
        rowLabelPost = rowLabelMain.row(align=True)
        colList = colMain.column(align=True)
        kmUNe = GetUserKmNe()
        ##
        kmiCats = KmiCats()
        kmiCats.cus = KmiCat('vaKmiCustomDiscl',     set())
        kmiCats.qqm = KmiCat('vaKmiQqmDiscl',        set(), dict_setKmiCats['qqm'] )
        kmiCats.grt = KmiCat('vaKmiMainstreamDiscl', set(), dict_setKmiCats['grt'] )
        kmiCats.oth = KmiCat('vaKmiOtjersDiscl',     set(), dict_setKmiCats['oth'] )
        kmiCats.spc = KmiCat('vaKmiSpecialDiscl',    set(), dict_setKmiCats['spc'] )
        kmiCats.cus.LCond = lambda a: a.id<0 #Отрицательный ид для кастомных? Ну ладно. Пусть будет идентифицирующим критерием.
        kmiCats.qqm.LCond = lambda a: any(True for txt in {'quickOprFloat','quickOprVector','quickOprBool','quickOprColor','justPieCall','isRepeatLastOperation'} if getattr(a.properties, txt, None))
        kmiCats.grt.LCond = lambda a: a.idname in kmiCats.grt.set_idn
        kmiCats.oth.LCond = lambda a: a.idname in kmiCats.oth.set_idn
        kmiCats.spc.LCond = lambda a:True
        #В старых версиях аддона с другим методом поиска, на вкладке "keymap" порядок отображался в обратном порядке вызовов регистрации kmidef с одинаковыми `cls`.
        #Теперь сделал так. Как работал предыдущий метод -- понятия не имею.
        scoAll = 0
        for li in kmUNe.keymap_items:
            if li.idname.startswith("node.voronoi_"):
                for dv in kmiCats.__dict__.values():
                    if dv.LCond(li):
                        dv.set_kmis.add(li)
                        dv.sco += 1
                        break
                scoAll += 1 #Хоткеев теперь стало та-а-ак много, что неплохо было бы узнать их количество.
        if kmUNe.is_user_modified:
            rowRestore = rowLabelMain.row(align=True)
            with LyAddQuickInactiveCol(rowRestore, align=False) as row:
                row.prop(self,'vaInfoRestore', text="", icon='INFO', emboss=False)
            rowRestore.context_pointer_set('keymap', kmUNe)
            rowRestore.operator('preferences.keymap_restore', text="Restore")
        else:
            rowLabelMain.label()
        rowAddNew = rowLabelMain.row(align=True)
        rowAddNew.ui_units_x = 12
        rowAddNew.separator()
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='NONE').opt = 'AddNewKmi' #NONE  ADD
        def LyAddKmisCategory(where, cat):
            if not cat.set_kmis:
                return
            colListCat = where.row().column(align=True)
            txt = self.bl_rna.properties[cat.propName].name
            if not LyAddDisclosureProp(colListCat, self, cat.propName, txt=TranslateIface(txt)+f" ({cat.sco})", active=False, isWide=1-1):
                return
            for li in sorted(cat.set_kmis, key=lambda a:a.id):
                colListCat.context_pointer_set('keymap', kmUNe)
                rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, kmUNe, li, colListCat, 0) #Заметка: Если colListCat будет не colListCat, то возможность удаления kmi станет недоступной.
        LyAddKmisCategory(colList, kmiCats.cus)
        LyAddKmisCategory(colList, kmiCats.grt)
        LyAddKmisCategory(colList, kmiCats.oth)
        LyAddKmisCategory(colList, kmiCats.spc)
        LyAddKmisCategory(colList, kmiCats.qqm)
        rowLabelPost.label(text=f"({scoAll})", translate=False)

    def LyDrawTabInfo(self, where):
        def LyAddUrlHl(where, text, url, txtHl=""):
            row = where.row(align=True)
            row.alignment = 'LEFT'
            if txtHl:
                txtHl = "#:~:text="+txtHl
            row.operator('wm.url_open', text=text, icon='URL').url=url+txtHl
            row.label()
        colMain = where.column()
        with LyAddQuickInactiveCol(colMain, att='column') as row:
            row.alignment = 'LEFT'
            row.label(text=txt_addonVerDateCreated)
        colUrls = colMain.column()
        LyAddUrlHl(colUrls, "Check for updates yourself", "https://github.com/ugorek000/VoronoiLinker", txtHl="Latest%20version")
        colUrls.separator()
        row = colMain.row(align=True)
        row.alignment = 'LEFT'
        row.operator(VoronoiOpAddonTabs.bl_idname, text=txt_copySettAsPyScript, icon='COPYDOWN').opt = 'GetPySett' #SCRIPT  COPYDOWN
        ##
        colVlTools = colMain.column(align=True)
        ##
        colLangDebug = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.vaLangDebDiscl):
            with LyAddQuickInactiveCol(colLangDebug, active=self.vaLangDebDiscl) as row:
                row.prop(self,'vaLangDebDiscl')
        if self.vaLangDebDiscl:
            row = colLangDebug.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=f"[{langCode}]", translate=False)
            row.label(text="–", translate=False)
            if langCode in dict_vlHhTranslations:
                dict_copy = dict_vlHhTranslations[langCode].copy()
                del dict_copy['trans']
                row.label(text=repr(dict_copy), translate=False)
            else:
                with LyAddQuickInactiveCol(row) as row:
                    row.label(text="{}", translate=False)
            colLangDebug.row().prop(self,'vaLangDebEnum', expand=True)
            def LyAddAlertNested(where, text):
                with LyAddQuickInactiveCol(where) as row:
                    row.label(text=text, translate=False)
                row = where.row(align=True)
                row.label(icon='BLANK1')
                return row.column(align=True)
            def LyAddTran(where, label, text, *, dot="."):
                rowRoot = where.row(align=True)
                with LyAddQuickInactiveCol(rowRoot) as row:
                    row.alignment = 'LEFT'
                    row.label(text=label+": ", translate=False)
                row = rowRoot.row(align=True)
                col = row.column(align=True)
                text = TranslateIface(text)
                if text:
                    list_split = text.split("\n")
                    hig = length(list_split)-1
                    for cyc, li in enumerate(list_split):
                        col.label(text=li+(dot if cyc==hig else ""), translate=False)
            def LyAddTranDataForProp(where, pr, dot="."):
                colRoot = where.column(align=True)
                with LyAddQuickInactiveCol(colRoot) as row:
                    row.label(text=pr.identifier, translate=False)
                row = colRoot.row(align=True)
                row.label(icon='BLANK1')
                col2 = row.column(align=True)
                LyAddTran(col2, "Name", pr.name, dot="")
                if pr.description:
                    LyAddTran(col2, "Description", pr.description, dot=dot)
                if type(pr)==typeEnum:
                    for en in pr.enum_items:
                        LyAddTranDataForProp(col2, en, dot="")
            typeEnum = bpy.types.EnumProperty
            match self.vaLangDebEnum:
                case 'FREE':
                    txt = TranslateIface("Free")
                    col = LyAddAlertNested(colLangDebug, f"{txt}")
                    col.label(text="Virtual")
                    col.label(text="Colored")
                    col.label(text="Restore")
                    col.label(text="Add New")
                    col.label(text="Edge pan")
                    with LyAddQuickInactiveCol(col, att='column') as col0:
                        col0.label(text="Zoom factor")
                        col0.label(text="Speed")
                    col.label(text="Pie")
                    col.label(text="Box ")
                    col.label(text="Special")
                    col.label(text="Colors")
                    col.label(text="Customization")
                    col.label(text="Advanced")
                    col.label(text=txt_FloatQuickMath)
                    col.label(text=txt_VectorQuickMath)
                    col.label(text=txt_BooleanQuickMath)
                    col.label(text=txt_ColorQuickMode)
                    col.label(text=txt_vmtNoMixingOptions)
                    col.label(text=txt_vqmtThereIsNothing)
                    col.label(text=bl_info['description'])
                    col.label(text=txt_addonVerDateCreated)

                    col.label(text=txt_onlyFontFormat)
                    col.label(text=txt_copySettAsPyScript)
                    col.label(text=txt_сheckForUpdatesYourself)
                case 'SPECIAL':
                    txt = TranslateIface("Special")
                    col0 = LyAddAlertNested(colLangDebug, f"[{txt}]")
                    col1 = LyAddAlertNested(col0, "VMT")
                    for dv in dict_vmtMixerNodesDefs.values():
                        col1.label(text=dv[2])
                    col1 = LyAddAlertNested(col0, "VQMT")
                    for di in dict_vqmtQuickMathMain.items():
                        col2 = LyAddAlertNested(col1, di[0])
                        for ti in di[1]:
                            if ti[0]:
                                col2.label(text=ti[0])
                case 'ADDONPREFS':
                    col = LyAddAlertNested(colLangDebug, "[AddonPrefs]")
                    set_toolBoxDisctPropNames = set([cls.disclBoxPropName for cls in dict_vtClasses])|set([cls.disclBoxPropNameInfo for cls in dict_vtClasses])
                    set_toolBoxDisctPropNames.update({'vaLangDebEnum'})
                    for pr in self.bl_rna.properties[2:]:
                        if pr.identifier not in set_toolBoxDisctPropNames:
                            LyAddTranDataForProp(col, pr)
                case _:
                    dict_toolBlabToCls = {cls.bl_label.upper():cls for cls in dict_vtClasses}
                    set_alreadyDone = set() #Учитывая разделение с помощью vaLangDebEnum, уже бесполезно.
                    col0 = colLangDebug.column(align=True)
                    cls = dict_toolBlabToCls[self.vaLangDebEnum]
                    col1 = LyAddAlertNested(col0, cls.bl_label)
                    rna = eval(f"bpy.ops.{cls.bl_idname}.get_rna_type()") #Через getattr какого-то чёрта не работает `getattr(bpy.ops, cls.bl_idname).get_rna_type()`.
                    for pr in rna.properties[1:]: #Пропуск rna_type.
                        rowLabel = col1.row(align=True)
                        if pr.identifier not in set_alreadyDone:
                            LyAddTranDataForProp(rowLabel, pr)
                            set_alreadyDone.add(pr.identifier)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    def draw(self, context):
        def LyAddDecorLyColRaw(where, sy=0.05, sx=1.0, en=False):
            where.prop(self,'vaDecorLy', text="")
            where.scale_x = sx
            where.scale_y = sy #Если будет меньше, чем 0.05, то макет исчезнет, и угловатость пропадёт.
            where.enabled = en
        colLy = self.layout.column()
        colMain = colLy.column(align=True)
        colTabs = colMain.column(align=True)
        rowTabs = colTabs.row(align=True)
        #Переключение вкладок создано через оператор, чтобы случайно не сменить вкладку при ведении зажатой мышки, кой есть особый соблазн с таким большим количеством "isColored".
        #А также теперь они задекорены ещё больше под "вкладки", чего нельзя сделать с обычным макетом prop'а с 'expand=True'.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
            #Теперь ещё больше похожи на вкладки
            LyAddDecorLyColRaw(col.row(align=True)) #row.operator(VoronoiOpAddonTabs.bl_idname, text="", emboss=False) #Через оператор тоже работает.
            #col.scale_x = min(1.0, (5.5-cyc)/2)
        colBox = colTabs.column(align=True)
        #LyAddDecorLyColRaw(colBox.row(align=True))
        #LyAddDecorLyColRaw(colBox.row(align=True), sy=0.25) #Коробка не может сузиться меньше, чем своё пустое состояние. Пришлось искать другой способ..
        try:
            match self.vaUiTabs:
                case 'SETTINGS':
                    self.LyDrawTabSettings(colMain)
                case 'APPEARANCE':
                    self.LyDrawTabAppearance(colMain)
                case 'DRAW':
                    self.LyDrawTabDraw(colMain)
                case 'KEYMAP':
                    self.LyDrawTabKeymaps(colMain)
                case 'INFO':
                    self.LyDrawTabInfo(colMain)
        except Exception as ex:
            LyAddEtb(colMain) #colMain.label(text=str(ex), icon='ERROR', translate=False)

dict_classes[VoronoiOpAddonTabs] = True
dict_classes[VoronoiAddonPrefs] = True

list_addonKeymaps = []

isRegisterFromMain = False

def register():
    for dk in dict_classes:
        bpy.utils.register_class(dk)

    # Initialize preferences
    prefs = Prefs()
    if isRegisterFromMain:
        if hasattr(bpy.types.SpaceNodeEditor, 'handle'):
            bpy.types.SpaceNodeEditor.nsReg = perf_counter_ns()
    else:
        prefs.vlnstLastExecError = ""
        prefs.vaLangDebDiscl = False
        for cls in dict_vtClasses:
            setattr(prefs, cls.disclBoxPropNameInfo, False)
        prefs.dsIsTestDrawing = False

    # Register keymap items
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blid, key, shift, ctrl, alt, repeat, dict_props in list_kmiDefs:
        kmi = kmANe.keymap_items.new(idname=blid, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        kmi.active = blid != 'node.voronoi_dummy'
        if dict_props:
            for dk, dv in dict_props.items():
                setattr(kmi.properties, dk, dv)
        list_addonKeymaps.append(kmi)

    # Register node connection logic (soldering system)
    RegisterSolderings()

def unregister():
    # Unregister soldering logic
    UnregisterSolderings()

    # Remove keymap items
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for li in list_addonKeymaps:
        kmANe.keymap_items.remove(li)
    list_addonKeymaps.clear()

    # Unregister Blender classes
    for dk in dict_classes:
        bpy.utils.unregister_class(dk)

# For repeated script runs, disables existing keymaps to avoid duplicates.
def DisableKmis():
    kmUNe = GetUserKmNe()
    for li, *oi in list_kmiDefs:
        for kmiCon in kmUNe.keymap_items:
            if li == kmiCon.idname:
                kmiCon.active = False  # Deactivate duplicates
                kmiCon.active = True   # Reactivate original

if __name__ == "__main__":
    DisableKmis()
    isRegisterFromMain = True
    register()
