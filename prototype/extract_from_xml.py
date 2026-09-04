"""
Machine Expert (PLCopen XML) proje export'undan modul registry + komut
enum'larini ayiklayan prototip script.

Kaynak: LMC_PacDrive.xml (SR02_GroupTransferModule vb. iceren gercek proje)
"""
import re
import json
from collections import OrderedDict

PATH = r"C:\Users\baris.menderes\Desktop\LMC_PacDrive.xml"

with open(PATH, "r", encoding="utf-8-sig") as f:
    text = f.read()

# ── 1) Modul registry — c_udi<ModuleName> = UDINT sabit. Bu tarz sabitler
# projede pek cok yerde (framework boilerplate: c_udiNumberOfGroups vb.)
# tekrar ediyor — GERCEK modul listesini, art arda 1'den baslayip 1'er
# artan bir dizi olusturan komsu <variable> bloklarini bularak ayirt
# ediyoruz (Master=1, Multibelt=2, ... MultiCarrier=9 gibi). Bu heuristik
# projeye ozel isim bilmeden calisir, baska bir export'ta da islevli olur.
tum_c_udi = list(re.finditer(
    r'<variable name="(c_udi[A-Za-z]+)">\s*<type>\s*<UDINT\s*/>\s*</type>\s*'
    r'<initialValue>\s*<simpleValue value="(\d+)"',
    text,
))

en_uzun_dizi = []
mevcut_dizi = []
for m in tum_c_udi:
    ad, deger = m.group(1), int(m.group(2))
    beklenen = (mevcut_dizi[-1][1] + 1) if mevcut_dizi else 1
    if deger == beklenen:
        mevcut_dizi.append((ad, deger))
    else:
        if len(mevcut_dizi) > len(en_uzun_dizi):
            en_uzun_dizi = mevcut_dizi
        mevcut_dizi = [(ad, deger)] if deger == 1 else []
if len(mevcut_dizi) > len(en_uzun_dizi):
    en_uzun_dizi = mevcut_dizi

modules = OrderedDict(en_uzun_dizi)

# ── 2) Projenin kendi ET_Cmd enum'u (modul-seviyesi komutlar, dataType) ──
et_cmd_block = re.search(
    r'<dataType name="ET_Cmd">.*?</values>', text, re.S,
)
et_cmd_values = []
if et_cmd_block:
    for m in re.finditer(r'<value name="(\w+)" value="(-?\d+)"', et_cmd_block.group(0)):
        et_cmd_values.append({"name": m.group(1), "value": int(m.group(2))})

# ── 3) AXM.ET_Cmd.* — PLC motion kütüphanesinden gelen, projede
# TANIMLANMAYAN (kullanilan) enum — deger degil, sadece isim cikarabiliriz. ──
axm_cmds = sorted(set(re.findall(r'AXM\.ET_Cmd\.(\w+)', text)))

# ── 4) Eksen (axis/drive) listesi — _MotorsTorkControl action'i TUM
# makinenin fiziksel eksenlerini G_lrMotorsCurrentTork[1..12] ile birebir
# sirali dolasiyor; bu, projedeki EN GUVENILIR "tum eksenler" listesi
# (baska yerlerdeki DRV_* kullanimlari kismi/tekrarli, bu blok tam ve tek). ──
tork_block = re.search(r'_MotorsTorkControl.*?END_IF', text, re.S)
axes = []
if tork_block:
    for m in re.finditer(r'ABS\((DRV_[A-Za-z0-9_]+)\.Current\)', tork_block.group(0)):
        axes.append(m.group(1))

# Her ekseni, ismi eksen adinin ICINDE GECEN en uzun modul adiyla eslestir
# (ör. DRV_RobotKoliAlma_Q -> RobotKoliAlma, DRV_GroupTransferX -> GroupTransfer).
module_names = [k.replace("c_udi", "") for k in modules]
axes_by_module = {name: [] for name in module_names}
unmatched_axes = []
for drv in axes:
    aday = drv[len("DRV_"):]
    en_iyi = max(
        (m for m in module_names if aday.replace("_", "").lower().startswith(m.lower())),
        key=len, default=None,
    )
    if en_iyi:
        axes_by_module[en_iyi].append(drv)
    else:
        unmatched_axes.append(drv)

sonuc = {
    "modules": [
        {
            "name": k.replace("c_udi", ""), "udi_const": k, "udi_value": v,
            "axes": axes_by_module.get(k.replace("c_udi", ""), []),
        }
        for k, v in modules.items()
    ],
    "unmatched_axes": unmatched_axes,
    "project_et_cmd": et_cmd_values,
    "axm_et_cmd_used": axm_cmds,
}

print(json.dumps(sonuc, indent=2, ensure_ascii=False))
