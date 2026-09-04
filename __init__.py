"""
tools/motionsetup/__init__.py
Motion Setup — CMD Table Builder engine.

STATE_NODE primitifinin CMD_TABLE bağlamındaki uygulaması: bir CMD table
sıralı bir "step" listesidir, her step {title, target_udi, cmd, timeout,
is_end} taşır. Bu modül bir step listesini, referans Init_CmdTables
POU'suyla (referans örnek modül üzerinden) yapısal olarak eşleşen ST
koduna çevirir.

Referans desen (gerçek proje kodundan, ExampleModule.Init_CmdTables):
  - İlk step  -> SEQ.FC_FirstStep(udiStepIndex, diStep);
  - Ara step, ÖNCEKİYLE AYNI diStep'te (paralel) -> SEQ.FC_SameStep(udiStepIndex, diStep);
  - Ara step, YENİ bir diStep'e geçiyor (sıralı) -> SEQ.FC_NextStep(udiStepIndex, diStep);
  - Son step  -> SEQ.FC_LastStep(udiStepIndex, diStep);
  - Her step için 6 alan ata: sTitle, udiModuleName, diStep, diCMD,
    timTimeOut, xEndCMD (bu sırayla, hizalı := ile)
  - Tablo bitince: SEQ.FC_FirstCmdTable + astListofCMDTables[...] 3 satır

SameStep gerçek örnekte doğrulandı: Prepare tablosunda RobotGripper +
RobotPickup + TopCloser + EntryReject + GroupTransfer hepsi AYNI adımda
paralel (SameStep) komut alıyor, sonra BoxTransfer yeni bir adıma
(NextStep) geçiyor. Yani "sıra" hem hangi modülün önce/sonra çalıştığını
HEM DE hangilerinin birlikte (paralel) çalıştığını ifade ediyor.

Standart 8 tablo (gerçek projede HER modülde birebir aynı isimlerle
tekrarlanıyor, tahmin değil): Prepare/Auto/Manual/Stop/Start/Abort/Hold/
BrakeRelease -> astPrepareTable/astAutoTable/astManualTable/astStopTable/
astStartTable/astAbortTable/astHoldTable/astBrakeReleaseTable.

Homing/başlangıç sırası CMD table'ın KENDİSİNDE (step listesi, kullanıcının
node-graph'ta dizdiği sıra) kodlanır — modül tipine sabitlenmiş bir kural
DEĞİLDİR (bkz. referans örnekte GroupTransferZ/X'in iki ayrı, sıralı step
olarak yer alması).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json as _json
from pathlib import Path as _Path

# ── Logic Editor'da kullanıcının kaydettiği özel bloklar ───────────────────
# Tool kendi kurulum klasöründe kalıcı bir JSON dosyasında saklanıyor (bind
# mount sayesinde restart'ları atlatıyor) — core'a hiçbir bağımlılık yok,
# AGENTS.md Madde 1 gereği tool kendi verisini kendi taşıyor.
_OZEL_BLOK_DOSYASI = _Path(__file__).parent / "custom_blocks.json"


def ozel_bloklari_oku() -> list[dict]:
    try:
        if _OZEL_BLOK_DOSYASI.exists():
            return _json.loads(_OZEL_BLOK_DOSYASI.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def ozel_bloklari_yaz(liste: list[dict]) -> None:
    _OZEL_BLOK_DOSYASI.write_text(_json.dumps(liste, ensure_ascii=False, indent=2), encoding="utf-8")


_GECERLI_CAGRI_TIPLERI = {"first", "same", "next", "last"}


@dataclass
class CmdStep:
    title: str
    target_udi: str        # ör. "c_udiGroupTransferZ" ya da "SEQ.Gc_udiAllSubModules"
    cmd: str                # "diCMD" alanına aynen yazılır, ör. "MC.ET_Cmd.Start"
    timeout: str = "T#0MS"
    cagri_tipi: str = "next"  # "first" | "same" | "next" | "last" — KULLANICI seçer,
                               # konumdan (ilk/son satır) OTOMATİK tahmin edilmez.
                               # first: SEQ.FC_FirstStep, same: SEQ.FC_SameStep (öncekiyle
                               # aynı diStep, paralel), next: SEQ.FC_NextStep (yeni diStep,
                               # sıralı), last: SEQ.FC_LastStep (tabloyu kapatır).
                               # NOT: xEndCMD alanı ayrı bir kullanıcı seçimi DEĞİL — tüm
                               # gerçek referans örneklerde xEndCMD := TRUE SADECE "last"
                               # step'te görülüyor, hiç sapma yok — bu yüzden xEndCMD
                               # doğrudan (cagri_tipi == "last")'dan türetiliyor.

    @classmethod
    def from_dict(cls, d: dict) -> "CmdStep":
        cagri = str(d.get("cagri_tipi") or "next").strip().lower()
        if cagri not in _GECERLI_CAGRI_TIPLERI:
            cagri = "next"
        return cls(
            title=str(d.get("title", "")).strip(),
            target_udi=str(d.get("target_udi", "")).strip(),
            cmd=str(d.get("cmd", "")).strip(),
            timeout=str(d.get("timeout") or "T#0MS").strip(),
            cagri_tipi=cagri,
        )


@dataclass
class CmdTable:
    title: str              # ör. "Prepare" / "Auto"
    cmd_enum: str            # astListofCMDTables[...].diCMD değeri, ör. "ET_Cmd.Prepare"
    array_name: str           # "astPrepareTable" / "astAutoTable"
    steps: list[CmdStep] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "CmdTable":
        return cls(
            title=str(d.get("title", "")).strip(),
            cmd_enum=str(d.get("cmd_enum", "")).strip(),
            array_name=str(d.get("array_name", "")).strip(),
            steps=[CmdStep.from_dict(s) for s in d.get("steps", [])],
        )


# Referans dosyada alanlar "astPrepareTable[udiStepIndex]." + alan adı + boşluk
# + ":=" şeklinde hizalanıyor. En uzun alan adı "udiModuleName" (13 karakter).
_FIELDS = ["sTitle", "udiModuleName", "diStep", "diCMD", "timTimeOut", "xEndCMD"]
_FIELD_WIDTH = max(len(f) for f in _FIELDS)


def _assign_line(array_name: str, field_name: str, value: str) -> str:
    prefix = f"{array_name}[udiStepIndex].{field_name}"
    pad = len(array_name) + len("[udiStepIndex].") + _FIELD_WIDTH
    return f"{prefix.ljust(pad)}:= {value};"


def _step_field_values(step: CmdStep) -> dict[str, str]:
    return {
        "sTitle": f"'{step.title}'",
        "udiModuleName": step.target_udi,
        "diStep": "diStep",
        "diCMD": step.cmd,
        "timTimeOut": step.timeout,
        "xEndCMD": "TRUE" if step.cagri_tipi == "last" else "FALSE",
    }


class CmdTableGecersiz(ValueError):
    pass


# ── Proje XML'inden topoloji ayıklama (Machine Expert / PLCopen XML export) ──
# Kaynak: kullanıcının gerçek LMC_PacDrive.xml export'u üzerinde geliştirildi
# ve doğrulandı — modül registry'si (c_udi<Modül> = ardışık 1..N sabitler) +
# eksen listesi (_MotorsTorkControl action'ındaki DRV_* referansları) + bazı
# eksenlerin kendi c_udi<Modül><Eksen> sabitine sahip olması (CMD table'da
# AYRI satır olarak hedeflenebilir) vs sahip olmaması (sadece modül
# seviyesinde hedeflenebilir, eksen detayı modülün kendi iç state
# machine'inde — sonraki faz).
import re as _re


def _en_uzun_ardisik_dizi(eslesmeler: list[tuple[str, int]]) -> list[tuple[str, int]]:
    en_uzun: list[tuple[str, int]] = []
    mevcut: list[tuple[str, int]] = []
    for ad, deger in eslesmeler:
        beklenen = (mevcut[-1][1] + 1) if mevcut else 1
        if deger == beklenen:
            mevcut.append((ad, deger))
        else:
            if len(mevcut) > len(en_uzun):
                en_uzun = mevcut
            mevcut = [(ad, deger)] if deger == 1 else []
    if len(mevcut) > len(en_uzun):
        en_uzun = mevcut
    return en_uzun


_VAR_BOLUM_RE = _re.compile(r'<(inputVars|outputVars|localVars|inOutVars)[^>]*>(.*?)</\1>', _re.S)
_VAR_GIRDI_RE = _re.compile(r'<variable name="([^"]+)">\s*<type>\s*(.*?)\s*</type>', _re.S)
_BASIT_TIP_RE = _re.compile(r'<(\w+)(?:\s[^>]*)?/>')
_TUREV_TIP_RE = _re.compile(r'<derived name="([^"]+)"\s*/>')


def _tip_adini_cikar(tip_xml: str) -> str:
    m = _BASIT_TIP_RE.search(tip_xml)
    if m:
        return m.group(1)
    m = _TUREV_TIP_RE.search(tip_xml)
    if m:
        return m.group(1)
    return "?"


_TXT_VAR_SATIR_RE = _re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:AT\s+\S+\s*)?:\s*([A-Za-z_][A-Za-z0-9_.]*)', _re.M)


def _metinsel_blok_degiskenleri(metin: str, anahtar: str) -> list[dict]:
    """Düz ST metninde (XML değil) 'VAR_INPUT ... END_VAR' gibi metinsel
    deklarasyon bloklarından değişken listesi çıkarır — IEC 61131-3'ün
    standart textual sözdizimi, tahmin değil. \\b sayesinde VAR_INPUT
    aranırken bare 'VAR' bloğuna, ya da tersine yanlışlıkla eşleşmez."""
    sonuc: list[dict] = []
    for m in _re.finditer(r'\b' + anahtar + r'\b(.*?)END_VAR', metin, _re.S | _re.I):
        for lm in _TXT_VAR_SATIR_RE.finditer(m.group(1)):
            sonuc.append({"name": lm.group(1), "type": lm.group(2)})
    return sonuc


def _metinsel_arayuz_ayikla(metin: str) -> dict:
    """XML bulunamadığında düşülen ikinci yol: kullanıcının doğrudan
    yapıştırdığı ST deklarasyon bloklarını (VAR_INPUT/VAR_OUTPUT/VAR/
    VAR_IN_OUT ... END_VAR) parse eder. Bunlar POU'nun gövdesinde DEĞİL,
    ayrı bir deklarasyon bölümünde bulunur — sadece mantık/gövde kodu
    yapıştırılmışsa (deklarasyon yoksa) üç liste de boş döner."""
    return {
        "inputs": _metinsel_blok_degiskenleri(metin, "VAR_INPUT"),
        "outputs": _metinsel_blok_degiskenleri(metin, "VAR_OUTPUT"),
        "locals": _metinsel_blok_degiskenleri(metin, "VAR_IN_OUT") + _metinsel_blok_degiskenleri(metin, "VAR"),
    }


def extract_pou_interface(xml_metni: str, pou_adi: str | None = None) -> dict:
    """Bir POU'nun girdi/çıktı/yerel değişken listesini çıkarır — iki yoldan
    biriyle: (1) gerçek PLCopen XML'de (tc6_0200 şeması) <interface>/
    inputVars/outputVars/localVars/inOutVars, (2) kullanıcının doğrudan
    yapıştırdığı düz ST metinsel deklarasyonu (VAR_INPUT/VAR_OUTPUT/VAR/
    VAR_IN_OUT ... END_VAR). İkisi de yoksa (ör. sadece gövde/mantık kodu
    yapıştırılmışsa) net bir "hata" alanıyla döner — asla exception
    fırlatmaz."""
    try:
        if "<pou " in xml_metni or "<interface>" in xml_metni:
            if pou_adi:
                m = _re.search(r'<pou name="' + _re.escape(pou_adi) + r'"[^>]*>(.*?)</pou>', xml_metni, _re.S)
            else:
                m = _re.search(r'<pou name="([^"]+)"[^>]*>(.*?)</pou>', xml_metni, _re.S)
            if not m:
                return {"inputs": [], "outputs": [], "locals": [], "hata": "Bu XML içinde belirtilen POU bulunamadı."}
            pou_blok = m.group(0)
            iface_m = _re.search(r'<interface>(.*?)</interface>', pou_blok, _re.S)
            if not iface_m:
                return {"inputs": [], "outputs": [], "locals": []}
            iface = iface_m.group(1)
            sonuc: dict = {"inputs": [], "outputs": [], "locals": []}
            anahtar_map = {"inputVars": "inputs", "outputVars": "outputs", "localVars": "locals", "inOutVars": "locals"}
            for sm in _VAR_BOLUM_RE.finditer(iface):
                etiket, govde = sm.group(1), sm.group(2)
                hedef = anahtar_map.get(etiket)
                if not hedef:
                    continue
                for vm in _VAR_GIRDI_RE.finditer(govde):
                    ad, tip_xml = vm.group(1), vm.group(2)
                    sonuc[hedef].append({"name": ad, "type": _tip_adini_cikar(tip_xml)})
            return sonuc

        sonuc = _metinsel_arayuz_ayikla(xml_metni)
        if not sonuc["inputs"] and not sonuc["outputs"] and not sonuc["locals"]:
            sonuc["hata"] = (
                "Bu metinde ne POU XML'i (<pou name=...>) ne de VAR_INPUT/"
                "VAR_OUTPUT/VAR deklarasyon bloğu bulundu — yapıştırdığın "
                "sadece gövde/mantık kodu olabilir; arayüz (değişken "
                "tanımları) ayrı bir bölümdür, onu da eklemen gerekir."
            )
        return sonuc
    except Exception as e:
        return {"inputs": [], "outputs": [], "locals": [], "hata": str(e)}


_ST_ANAHTAR_KELIME = {
    "IF", "THEN", "ELSE", "ELSIF", "END_IF", "AND", "OR", "NOT", "XOR", "MOD", "DIV",
    "CASE", "OF", "END_CASE", "FOR", "TO", "BY", "DO", "END_FOR", "WHILE", "END_WHILE",
    "REPEAT", "UNTIL", "END_REPEAT", "TRUE", "FALSE", "VAR", "VAR_INPUT", "VAR_OUTPUT",
    "VAR_IN_OUT", "END_VAR", "RETURN", "EXIT", "CONTINUE", "AT",
}
_IDENT_YOL_RE = _re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*')
_CAGRI_ADI_RE = _re.compile(r'([A-Za-z_][A-Za-z0-9_.]*)\s*\(')

# Gerçek Application.xml export'u üzerinde ölçüldü (tahmin değil): gerçek
# <inputVars>'ların %93'ü "i_", <outputVars>'ların %80'i "q_", <inOutVars>'ların
# %97'si "iq_" ile başlıyor. "Di_"/"Dq_" (dijital giriş/çıkış) ve "ton_" (TON
# zamanlayıcı örneği) kullanıcının kendi projesinden doğrulandı. Bu önekler,
# ham okuma/yazma kümesinden çok daha güvenilir bir sinyal — önce bunlara
# bakılır, yoksa okuma/yazma heuristiğine düşülür.
_ON_EK_GIRDI = ("Di", "i")
_ON_EK_CIKTI = ("Dq", "q")
# "G" (global) ve "FB"/"iFB"/"DB" (arayüz/instance referansı) BİLEREK burada
# YOK — gerçek kullanıcı raporu: G_x... atanan bir değişken gerçekte OUTPUT'tur
# (ör. G_xGroupTransferStartFromBeg), iFB_x....q_y gibi bir başka modülün
# arayüzünden OKUNAN bir alan gerçekte bu POU için INPUT'tur (ör.
# iFB_xAxis_xStops.q_xWaitingAtPos3) — ikisi de önek yerine normal okuma/
# yazma davranışına bırakılmalı, aksi halde "locals"a gizlenip listede hiç
# görünmüyorlardı.
_ON_EK_YEREL = ("c", "l", "Gc", "st", "ton", "tof", "ctu", "ctd", "vpq", "iq")


def _degisken_koku(ad: str) -> str:
    return ad.split(".")[0].split("_")[0]


def infer_io_from_body(metin: str) -> dict:
    """Deklarasyon YOK, sadece gövde/mantık kodu verildiğinde girdi/çıktı
    listesini çıkarır. Öncelik SIRASI: (1) projenin kendi önek konvansiyonu
    (_ON_EK_GIRDI/_ON_EK_CIKTI/_ON_EK_YEREL — gerçek veriyle doğrulandı,
    bkz. yukarı), (2) önek tanınmıyorsa okuma/yazma heuristiği (sadece
    okunan → girdi adayı, atanan → çıktı adayı). Yine de bir TAHMİN —
    çağıran taraf kullanıcıya böyle sunmalı. FB çağrılarındaki parametre
    isimleri (IN:=, PT:= gibi) ve çağrılan fonksiyon/FB adlarının kendisi
    değişken sayılmaz; "ton_" gibi FB-örneği önekleri de I/O'ya değil
    'locals'a düşer (bunlar Variables/Function-blocks alanına ait)."""
    try:
        temiz = _yorum_satirlarini_temizle(metin)
        # Tipli sabitler (T#2S, TIME#500MS, 16#FF gibi) '#' sonrası harf
        # içerdiği için identifier regex'i bunları "T" + "S" gibi hayalet
        # değişkenlere bölüyordu (gerçek kullanıcı raporu) — taramadan önce
        # tamamen çıkar.
        temiz = _re.sub(r'\b(?:T|TIME|DT|DATE|TOD|D|LTIME)#[0-9A-Za-z_]+|\b[0-9]+#[0-9A-Za-z_]+', ' ', temiz, flags=_re.I)
        # 'Vakum bekleniyor ..' gibi STRING SABİTLERİ (ör. Hmi_Status_X
        # atamaları) yorum değil — ama içeriği yine de gerçek kod değil,
        # serbest metin. İçini boşaltmazsak Türkçe kelimeler identifier
        # regex'ine takılıp hayalet değişken gibi görünüyordu (gerçek
        # kullanıcı raporu — bu, bu fonksiyona ÖZEL bir temizlik: CMD table
        # motorundaki _yorum_satirlarini_temizle'ye DOKUNMUYORUZ, çünkü
        # orada sTitle gibi alanlar için string içeriği KORUNMALI).
        temiz = _re.sub(r"'[^']*'", "''", temiz)
        cagri_adlari = set(m.group(1).split(".")[0] for m in _CAGRI_ADI_RE.finditer(temiz))

        # ÖNEMLİ: metni ';' ile PARÇALARA BÖLMÜYORUZ artık — IF/CASE/FOR gibi
        # noktalı virgülsüz kontrol satırlarına bitişik gerçek atamalar bu
        # yüzden kayboluyordu (gerçek kullanıcı raporu: "çok az oldu"). Bunun
        # yerine TÜM metni tek seferde tarıyoruz: her ":=" için o noktadaki
        # parantez DERİNLİĞİNE bakarak gerçek bir atama mı (derinlik 0) yoksa
        # bir FB çağrısının parametre bağlama satırı mı (IN:=, PT:= gibi,
        # derinlik > 0) olduğunu ayırt ediyoruz.
        yazilan: set[str] = set()
        parametre_adlari: set[str] = set()
        for m in _re.finditer(r'([A-Za-z_][A-Za-z0-9_.]*)\s*:=', temiz):
            ad = m.group(1)
            konum = m.start()
            derinlik = temiz.count("(", 0, konum) - temiz.count(")", 0, konum)
            if derinlik > 0:
                parametre_adlari.add(ad)
            elif _IDENT_YOL_RE.fullmatch(ad):
                yazilan.add(ad)
        # "Q=> xVar" gibi ÇIKTI bağlama sözdizimi (FB çağrısında bir çıkışı
        # bir değişkene bağlar) — "Q"/"ET" gibi FB pin adları ':=' değil '=>'
        # kullanır, önceki regex bunları yakalamıyordu ve sahte "girdi" gibi
        # görünüyorlardı (gerçek kullanıcı raporu: boş "Q=> , ET=>" satırı).
        for m in _re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*=>', temiz):
            parametre_adlari.add(m.group(1))

        okunan: set[str] = set()
        for m in _IDENT_YOL_RE.finditer(temiz):
            ad = m.group(0)
            kok = ad.split(".")[0]
            if kok.upper() in _ST_ANAHTAR_KELIME or kok in cagri_adlari or ad in parametre_adlari:
                continue
            # Bu geçiş, tam olarak bir atamanın SOL tarafındaki isim mi
            # (ör. "X := ..." içindeki X)? Öyleyse bunu "okunan" sayma —
            # aksi halde her yazılan değişken kendi atama satırında da
            # "okunmuş" görünür ve locals'a düşerdi (gerçek regresyon).
            sonrasi = temiz[m.end():]
            am = _re.match(r'\s*:=', sonrasi)
            if am:
                derinlik = temiz.count("(", 0, m.start()) - temiz.count(")", 0, m.start())
                if derinlik == 0:
                    continue
            okunan.add(ad)

        girdi: set[str] = set()
        cikti: set[str] = set()
        yerel: set[str] = set()
        for ad in yazilan | okunan:
            onek = _degisken_koku(ad)
            if onek in _ON_EK_YEREL:
                yerel.add(ad)
            elif onek in _ON_EK_CIKTI:
                cikti.add(ad)
            elif onek in _ON_EK_GIRDI:
                girdi.add(ad)
            elif ad in yazilan and ad in okunan:
                yerel.add(ad)
            elif ad in yazilan:
                cikti.add(ad)
            else:
                girdi.add(ad)

        return {
            "inputs": [{"name": a, "type": "?"} for a in sorted(girdi)],
            "outputs": [{"name": a, "type": "?"} for a in sorted(cikti)],
            "locals": [{"name": a, "type": "?"} for a in sorted(yerel)],
        }
    except Exception as e:
        return {"inputs": [], "outputs": [], "locals": [], "hata": str(e)}


def extract_topology(xml_metni: str) -> dict:
    """Machine Expert proje export XML'inden (PLCopen XML, tc6_0200) modül/
    eksen/komut topolojisini ayıklar. Hatalı/beklenmeyen bir yapı durumunda
    boş listelerle döner — asla exception fırlatmaz (kullanıcıya "içe
    aktarılamadı" demek, tüm tool'u kırmaktan iyidir)."""
    try:
        # 1) Modül registry — c_udi<Modül> = UDINT sabit, art arda 1..N.
        tum_c_udi = [
            (m.group(1), int(m.group(2)))
            for m in _re.finditer(
                r'<variable name="(c_udi[A-Za-z]+)">\s*<type>\s*<UDINT\s*/>\s*</type>\s*'
                r'<initialValue>\s*<simpleValue value="(\d+)"',
                xml_metni,
            )
        ]
        modul_dizisi = _en_uzun_ardisik_dizi(tum_c_udi)
        modul_udi_const = {ad: deger for ad, deger in modul_dizisi}
        modul_isimleri = [ad.replace("c_udi", "") for ad, _ in modul_dizisi]

        # 2) Projenin kendi ET_Cmd enum'u (modül-seviyesi komutlar).
        et_cmd_blok = _re.search(r'<dataType name="ET_Cmd">.*?</values>', xml_metni, _re.S)
        proje_et_cmd = []
        if et_cmd_blok:
            proje_et_cmd = [
                {"name": m.group(1), "value": int(m.group(2))}
                for m in _re.finditer(r'<value name="(\w+)" value="(-?\d+)"', et_cmd_blok.group(0))
            ]

        # 3) MC.ET_Cmd.* — kütüphane enum'u, sadece kullanım yerlerinden isim.
        axm_komutlar = sorted(set(_re.findall(r'AXM\.ET_Cmd\.(\w+)', xml_metni)))

        # 4) Eksen listesi — _MotorsTorkControl action'ı tüm fiziksel
        # eksenleri sırayla dolaşıyor, en güvenilir tam liste.
        tork_blok = _re.search(r'_MotorsTorkControl.*?END_IF', xml_metni, _re.S)
        drv_liste = []
        if tork_blok:
            drv_liste = [m.group(1) for m in _re.finditer(r'ABS\((DRV_[A-Za-z0-9_]+)\.Current\)', tork_blok.group(0))]

        # Her eksenin kendi c_udi<Modül><Eksen> sabiti var mı? (varsa CMD
        # table'da ayrı satır olarak hedeflenebilir).
        eksen_udi_const = {
            m.group(1): m.group(1)
            for m in _re.finditer(
                r'<variable name="(c_udi(?:' + "|".join(_re.escape(n) for n in modul_isimleri) + r')[A-Za-z0-9_]+)">',
                xml_metni,
            )
        } if modul_isimleri else {}

        modules = []
        eslesmeyen_eksenler = []
        for ad, deger in modul_dizisi:
            modul_adi = ad.replace("c_udi", "")
            eksenler = []
            for drv in drv_liste:
                aday = drv[len("DRV_"):].replace("_", "")
                if aday.lower().startswith(modul_adi.lower()):
                    eksen_adi = drv[len("DRV_"):]
                    udi_const = eksen_udi_const.get(f"c_udi{eksen_adi}") or eksen_udi_const.get(f"c_udi{eksen_adi.replace('_', '')}")
                    eksenler.append({
                        "name": eksen_adi, "drv_ref": drv,
                        "udi_const": udi_const, "addressable": bool(udi_const),
                    })
            modules.append({
                "name": modul_adi, "udi_const": ad, "udi_value": deger, "axes": eksenler,
            })

        eslesen_drv = {e["drv_ref"] for mod in modules for e in mod["axes"]}
        eslesmeyen_eksenler = [d for d in drv_liste if d not in eslesen_drv]

        return {
            "modules": modules,
            "unmatched_axes": eslesmeyen_eksenler,
            "project_et_cmd": proje_et_cmd,
            "axm_et_cmd_used": axm_komutlar,
        }
    except Exception as e:
        return {"modules": [], "unmatched_axes": [], "project_et_cmd": [], "axm_et_cmd_used": [], "hata": str(e)}


def generate_cmd_table(table: CmdTable, ilk_tablo: bool = True) -> str:
    """ilk_tablo=False: SEQ.FC_FirstCmdTable yerine SEQ.FC_NextCmdTable
    kullanılır — referans örnekte bir Init_CmdTables action'ında SADECE
    ilk tablo FirstCmdTable, ondan sonraki HER tablo NextCmdTable
    kullanıyor (Prepare=First, Auto/Manual/Stop/.../BrakeRelease=Next)."""
    if not table.title:
        raise CmdTableGecersiz("Tablo başlığı (title) boş olamaz.")
    if not table.cmd_enum:
        raise CmdTableGecersiz("Tablo cmd_enum alanı boş olamaz.")
    if not table.array_name:
        raise CmdTableGecersiz("Tablo array_name alanı boş olamaz.")
    if not table.steps:
        raise CmdTableGecersiz("En az bir step eklenmeli.")
    for i, s in enumerate(table.steps):
        if not s.title:
            raise CmdTableGecersiz(f"{i+1}. step'in başlığı (title) boş olamaz.")
        if not s.target_udi:
            raise CmdTableGecersiz(f"{i+1}. step'in hedef modülü (target_udi) boş olamaz.")
        if not s.cmd:
            raise CmdTableGecersiz(f"{i+1}. step'in komutu (cmd) boş olamaz.")

    # Çağrı tipi artık KULLANICI tarafından açıkça seçiliyor (first/same/
    # next/last) — konumdan tahmin edilmiyor. Framework'ün kendi kuralı
    # gereği sadece iki yapısal kısıt var: tam olarak bir "first" olmalı
    # ve o, listenin İLK elemanı olmalı; tam olarak bir "last" olmalı ve
    # o, listenin SON elemanı olmalı (ondan sonraki hiçbir step üretilen
    # kodda çalıştırılamaz çünkü tablo orada kapanıyor).
    n = len(table.steps)
    ilk_sayisi = sum(1 for s in table.steps if s.cagri_tipi == "first")
    son_sayisi = sum(1 for s in table.steps if s.cagri_tipi == "last")
    if ilk_sayisi != 1 or table.steps[0].cagri_tipi != "first":
        raise CmdTableGecersiz("Tam olarak bir step 'İlk Adım (First)' olmalı ve bu, listenin ilk sırasında olmalı.")
    if son_sayisi != 1 or table.steps[-1].cagri_tipi != "last":
        raise CmdTableGecersiz("Tam olarak bir step 'Son Adım (Last)' olmalı ve bu, listenin son sırasında olmalı.")
    for i, s in enumerate(table.steps):
        if 0 < i < n - 1 and s.cagri_tipi not in ("same", "next"):
            raise CmdTableGecersiz(f"{i+1}. step 'Aynı Adım' ya da 'Sıradaki Adım' olmalı (First/Last sadece ilk/son satırda kullanılabilir).")

    lines: list[str] = []
    # Referans dosyadaki bölüm başlığı deseni — her tablo kendi ayırıcı
    # çizgisi + isim yorumuyla başlıyor (bkz. "(*** Prepare ***)" örneği).
    lines.append("(" + "*" * 119 + ")")
    lines.append(f"(*** {table.title} ***)")
    lines.append("")

    _CAGRI_KOD = {
        "first": "SEQ.FC_FirstStep(udiStepIndex, diStep);",
        "same": "SEQ.FC_SameStep(udiStepIndex, diStep);",
        "next": "SEQ.FC_NextStep(udiStepIndex, diStep);",
        "last": "SEQ.FC_LastStep(udiStepIndex, diStep);",
    }
    for step in table.steps:
        lines.append(_CAGRI_KOD[step.cagri_tipi])

        values = _step_field_values(step)
        for f in _FIELDS:
            lines.append(_assign_line(table.array_name, f, values[f]))
        lines.append("")

    lines.append(f"SEQ.FC_{'First' if ilk_tablo else 'Next'}CmdTable(iq_udiTableIndex:= udiTableIndex);")
    lines.append(f"astListofCMDTables[udiTableIndex].sTitle              := '{table.title}';")
    lines.append(f"astListofCMDTables[udiTableIndex].diCMD               := {table.cmd_enum};")
    lines.append("astListofCMDTables[udiTableIndex].udiNumberOfCmdSteps := udiStepIndex;")

    return "\n".join(lines)


# ── Var olan Init_CmdTables'ı geriye-parse etme ────────────────────────────
# Kaynak: kullanıcının gerçek ExampleModule.xml export'u üzerinde
# doğrulandı (tüm 8 standart tablo + yorum satırına alınmış/devre dışı
# bırakılmış adımlar + "Brake Release" gibi array adından farklı bir
# başlık örneği dahil). generate_cmd_table'ın TAM TERSİ: ST metnini
# okuyup CmdStep listelerine çevirir — kullanıcı elle hiçbir şey
# yazmadan, projesinde zaten var olan tabloları düzenlemeye başlayabilsin.
_TOKEN_RE = _re.compile(
    r'TPL\.FC_(?P<call>First|Same|Next|Last)Step\(udiStepIndex,\s*diStep\);'
    r'|TPL\.FC_(?:First|Next)CmdTable\(iq_udiTableIndex:=\s*udiTableIndex\);'
    r"|(?P<arr>[A-Za-z_][A-Za-z0-9_]*)\[udiStepIndex\]\.(?P<field>sTitle|udiModuleName|diCMD|timTimeOut|xEndCMD)\s*:=\s*(?P<val>'[^']*'|[^;]+);"
    r"|astListofCMDTables\[udiTableIndex\]\.(?P<lfield>sTitle|diCMD)\s*:=\s*(?P<lval>'[^']*'|[^;]+);"
)


def _yorum_satirlarini_temizle(metin: str) -> str:
    # "(* ... *)" blok yorumları (gerçek referans dosyada devre dışı
    # bırakılmış eski adımlar tam olarak bu şekilde saklanıyor) önce
    # kaldırılıyor — aksi halde içindeki SEQ.FC_*Step çağrıları da parse
    # edilip tabloya hayalet adımlar olarak eklenir (birden fazla "first"
    # step'e, dolayısıyla generate_cmd_table'ın reddetmesine yol açar).
    metin = _re.sub(r"\(\*.*?\*\)", "", metin, flags=_re.S)
    # "//" yorumları SADECE satır başında değil, kodun SONUNDA da olabilir
    # (ör. "kod; //türkçe açıklama") — bunu satır-başı kontrolüyle yakalamak
    # yetmiyordu, açıklama kelimeleri infer_io_from_body'de sahte değişken
    # gibi görünüyordu (gerçek kullanıcı raporu). Satır içindeki ilk "//"'yi
    # kesiyoruz — ama '...' string sabiti içindeyse (ör. bir URL) saymıyoruz.
    satirlar = []
    for s in metin.split("\n"):
        icinde_mi = False
        kesim = len(s)
        i = 0
        while i < len(s) - 1:
            if s[i] == "'":
                icinde_mi = not icinde_mi
            elif not icinde_mi and s[i] == "/" and s[i + 1] == "/":
                kesim = i
                break
            i += 1
        satirlar.append(s[:kesim])
    return "\n".join(satirlar)


def _init_cmdtables_blogunu_parsele(blok: str) -> dict:
    sonuc: dict = {}
    mevcut_step: dict | None = None
    mevcut_array: str | None = None
    son_array: str | None = None

    def _adimi_kapat():
        nonlocal mevcut_step, mevcut_array
        if mevcut_step is not None and mevcut_array is not None:
            sonuc.setdefault(mevcut_array, {"title": None, "cmd_enum": None, "steps": []})
            sonuc[mevcut_array]["steps"].append(mevcut_step)
        mevcut_step, mevcut_array = None, None

    for m in _TOKEN_RE.finditer(blok):
        if m.group("call"):
            _adimi_kapat()
            mevcut_step = {"cagri_tipi": m.group("call").lower(), "title": "", "target_udi": "", "cmd": "", "timeout": "T#0MS"}
        elif m.group("arr"):
            if mevcut_step is None:
                continue  # beklenmeyen sıra — bu satırı atla, tool'u kırma
            arr, alan, deger = m.group("arr"), m.group("field"), m.group("val").strip()
            mevcut_array = son_array = arr
            if alan == "sTitle":
                mevcut_step["title"] = deger.strip("'")
            elif alan == "udiModuleName":
                mevcut_step["target_udi"] = deger
            elif alan == "diCMD":
                mevcut_step["cmd"] = deger
            elif alan == "timTimeOut":
                mevcut_step["timeout"] = deger
            # xEndCMD KASITLI olarak yok sayılıyor — cagri_tipi'den türetiliyor.
        elif m.group("lfield"):
            _adimi_kapat()
            if son_array is None:
                continue
            sonuc.setdefault(son_array, {"title": None, "cmd_enum": None, "steps": []})
            deger = m.group("lval").strip()
            if m.group("lfield") == "sTitle":
                sonuc[son_array]["title"] = deger.strip("'")
            else:
                sonuc[son_array]["cmd_enum"] = deger
    _adimi_kapat()
    return sonuc


def parse_init_cmdtables(xml_metni: str) -> list[dict]:
    """Proje export'unda (varsa) Init_CmdTables action'larını bulup geriye-
    parse eder. HER BLOK, onu saran <pou name="..."> ile birlikte ayrı bir
    girdi olarak döner: [{"pou": "ExampleModule", "tables": {...}}].

    KRİTİK: bir tam proje export'unda (LMC_PacDrive.xml gibi) hem ana
    makinenin (SR_MainMachine) hem HER modülün kendi Init_CmdTables'ı var —
    ve modülün kendi yerel "astPrepareTable" değişkeni ile ana makinenin
    kendi yerel "astPrepareTable" değişkeni AYNI İSMİ taşıyor ama TAMAMEN
    FARKLI tablolar. Önceki sürüm bunları array_name'e göre TEK bir sözlükte
    birleştiriyordu (sonuc.update(...)) — bu, ana makine ve modül içeriğini
    birbirine karıştıran bir hataydı (kullanıcı raporu). Bu yüzden artık HİÇ
    birleştirme yapılmıyor; hangi bloğun hangi kapsama ait olduğuna karar
    vermek çağıran tarafın (panel.js) sorumluluğu — POU adını modül adıyla
    eşleştirerek (bkz. panel.js pouEslesirMi)."""
    try:
        pou_pozisyonlari = [
            (m.start(), m.group(1)) for m in _re.finditer(r'<pou name="([^"]+)"', xml_metni)
        ]

        sonuc: list[dict] = []
        for m in _re.finditer(r'<action name="Init_CmdTables">.*?<xhtml[^>]*>(.*?)</xhtml>', xml_metni, _re.S):
            konum = m.start()
            pou_adi = None
            for poz, ad in pou_pozisyonlari:
                if poz < konum:
                    pou_adi = ad
                else:
                    break
            tablolar = _init_cmdtables_blogunu_parsele(_yorum_satirlarini_temizle(m.group(1)))
            if tablolar:
                sonuc.append({"pou": pou_adi, "tables": tablolar})
        return sonuc
    except Exception:
        return []


# ── Serbest ST mantığı (Logic_active vb.) — parse + render round-trip ──────
# CMD table'ların aksine burada sabit bir satır şablonu yok: kullanıcının
# elle yazdığı IF/ELSIF/ELSE dallanmaları, atamalar, fonksiyon çağrıları ve
# yorumlar var (bkz. Application.xml'deki ExampleModule.Logic_active
# örneği). Bu yüzden CMD table motorundan tamamen ayrı, genel amaçlı bir
# satır-tabanlı ayrıştırıcı: tam bir ST grameri DEĞİL, gerçek örnekte görülen
# alt kümeyi (tek satırlık IF/ELSIF/ELSE koşulları, ';' ile kapanan
# ifadeler/atamalar, '//' ve '(* *)' yorumları) destekler. Desteklemediği bir
# yapı görürse (kapanmamış IF, çok satıra bölünmüş koşul) sessizce yanlış
# sonuç üretmek yerine StLogicGecersiz fırlatır.
# Gerçek kullanıcı kodunda kapanış/etiket satırlarının SONUNDA da "//yorum"
# olabiliyor (ör. "999://ERR", "0://İnit") — bu yüzden aşağıdaki kapanış/
# etiket regex'lerinin HEPSİ isteğe bağlı bir satır-sonu yorumuna izin
# veriyor (?://.*)?$ ile; aksi halde satır sonu yorumu olan her CASE
# etiketi/END_* satırı eşleşmiyor, kapanmamış blok hatası veriyordu
# (gerçek kullanıcı raporu — ExampleModule.Logic_active).
_SATIR_SONU_YORUM = r'(?:\s*//.*)?$'
_IF_RE = _re.compile(r'^IF\s+(.+?)\s+THEN\s*$', _re.I)
_ELSIF_RE = _re.compile(r'^ELSIF\s+(.+?)\s+THEN\s*$', _re.I)
_ELSE_RE = _re.compile(r'^ELSE\s*' + _SATIR_SONU_YORUM, _re.I)
_ENDIF_RE = _re.compile(r'^END_IF\s*;?' + _SATIR_SONU_YORUM, _re.I)
_CASE_RE = _re.compile(r'^CASE\s+(.+?)\s+OF\s*$', _re.I)
_ENDCASE_RE = _re.compile(r'^END_CASE\s*;?' + _SATIR_SONU_YORUM, _re.I)
# CASE kolu etiketi: "1:", "1, 2:", "10..20:", "ET_State.Idle:" — kendi
# satırında yalnız durur (satır içi gövde desteklenmiyor, v1 sınırı).
# ':=' ile karışmasın diye ':' sonrasında '=' YASAK.
_CASE_LABEL_RE = _re.compile(r'^([A-Za-z0-9_.\s,\-]+):(?!=)\s*' + _SATIR_SONU_YORUM)
_FOR_RE = _re.compile(r'^FOR\s+(\w+)\s*:=\s*(.+?)\s+TO\s+(.+?)(?:\s+BY\s+(.+?))?\s+DO\s*$', _re.I)
_ENDFOR_RE = _re.compile(r'^END_FOR\s*;?' + _SATIR_SONU_YORUM, _re.I)
_WHILE_RE = _re.compile(r'^WHILE\s+(.+?)\s+DO\s*$', _re.I)
_ENDWHILE_RE = _re.compile(r'^END_WHILE\s*;?' + _SATIR_SONU_YORUM, _re.I)
_REPEAT_RE = _re.compile(r'^REPEAT\s*' + _SATIR_SONU_YORUM, _re.I)
_UNTIL_RE = _re.compile(r'^UNTIL\s+(.+?)\s*$', _re.I)
_ENDREPEAT_RE = _re.compile(r'^END_REPEAT\s*;?' + _SATIR_SONU_YORUM, _re.I)
# Koşul/başlık parantez içinde birden fazla satıra bölünmüş olabilir (ör.
# uzun bir OR/AND zinciri okunabilirlik için satır satır yazılmış). Bu
# durumda tek-satır regex'i doğrudan eşleşmez — _ON varyantları sadece
# satırın HANGİ yapıyla başladığını (IF/ELSIF/WHILE/CASE/FOR) tanımak için,
# çok satırlı birleştirmeyi tetiklemek amacıyla kullanılıyor.
_IF_ON = _re.compile(r'^IF\b', _re.I)
_ELSIF_ON = _re.compile(r'^ELSIF\b', _re.I)
_WHILE_ON = _re.compile(r'^WHILE\b', _re.I)
_CASE_ON = _re.compile(r'^CASE\b', _re.I)
_FOR_ON = _re.compile(r'^FOR\b', _re.I)


class StLogicGecersiz(ValueError):
    pass


def parse_st_logic(metin: str) -> list[dict]:
    satirlar = metin.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    n = len(satirlar)
    konum = [0]  # liste: iç içe closure'lardan mutasyona izin vermek için

    def _coklu_satir_birlestir(baslangic: int, terminal_kelime: str):
        """baslangic satırından başlayarak, parantezler dengeye gelene VE
        birleşik metin terminal_kelime (THEN/DO/OF) ile bitene kadar
        sonraki satırları tek boşlukla birleştirir. Bulamazsa None döner."""
        parcalar: list[str] = []
        idx = baslangic
        for _ in range(40):
            if idx >= n:
                return None
            parcalar.append(satirlar[idx].strip())
            idx += 1
            birlesik = " ".join(p for p in parcalar if p)
            denge = birlesik.count("(") - birlesik.count(")")
            if denge <= 0 and _re.search(r"\b" + terminal_kelime + r"\s*$", birlesik, _re.I):
                return birlesik, idx
        return None

    def _anahtar_esle(baslangic: int, tekli_regex, terminal_kelime: str, on_kelime_re):
        """baslangic satırını önce tek-satır regex'iyle dener; eşleşmezse
        VE satır on_kelime_re ile başlıyorsa (ör. 'IF'), çok satırlı
        birleştirmeyi dener. (match, sonraki_konum) ya da (None, baslangic)
        döner."""
        ilk = satirlar[baslangic].strip()
        m = tekli_regex.match(ilk)
        if m:
            return m, baslangic + 1
        if not on_kelime_re.match(ilk):
            return None, baslangic
        birlesim = _coklu_satir_birlestir(baslangic, terminal_kelime)
        if birlesim is None:
            return None, baslangic
        birlesik, yeni_konum = birlesim
        m2 = tekli_regex.match(birlesik)
        if not m2:
            return None, baslangic
        return m2, yeni_konum

    def blogu_parsele():
        dugumler: list[dict] = []
        bekleyen: list[str] = []

        def bekleyeni_bosalt():
            if bekleyen:
                birlesik = "\n".join(bekleyen).strip()
                if birlesik:
                    dugumler.append({"kind": "stmt", "text": birlesik})
                bekleyen.clear()

        while konum[0] < n:
            satir = satirlar[konum[0]]
            temiz = satir.strip()
            if temiz == "":
                konum[0] += 1
                continue
            if temiz.startswith("(*"):
                bekleyeni_bosalt()
                if temiz.endswith("*)") and len(temiz) >= 4:
                    dugumler.append({"kind": "comment", "block": True, "text": temiz[2:-2].strip()})
                    konum[0] += 1
                else:
                    parca = [temiz[2:]]
                    konum[0] += 1
                    kapandi = False
                    while konum[0] < n:
                        l2 = satirlar[konum[0]]
                        if "*)" in l2:
                            parca.append(l2[: l2.index("*)")])
                            konum[0] += 1
                            kapandi = True
                            break
                        parca.append(l2)
                        konum[0] += 1
                    if not kapandi:
                        raise StLogicGecersiz("Kapanmamış (* yorum bloğu.")
                    dugumler.append({"kind": "comment", "block": True, "text": "\n".join(parca).strip()})
                continue
            if temiz.startswith("//"):
                bekleyeni_bosalt()
                dugumler.append({"kind": "comment", "block": False, "text": temiz[2:].strip()})
                konum[0] += 1
                continue
            m, sonraki = _anahtar_esle(konum[0], _IF_RE, "THEN", _IF_ON)
            if m:
                bekleyeni_bosalt()
                konum[0] = sonraki
                dallar = [{"cond": m.group(1).strip(), "body": blogu_parsele()}]
                else_govde = None
                while konum[0] < n:
                    m2, sonraki2 = _anahtar_esle(konum[0], _ELSIF_RE, "THEN", _ELSIF_ON)
                    if m2:
                        konum[0] = sonraki2
                        dallar.append({"cond": m2.group(1).strip(), "body": blogu_parsele()})
                        continue
                    if _ELSE_RE.match(satirlar[konum[0]].strip()):
                        konum[0] += 1
                        else_govde = blogu_parsele()
                        continue
                    break
                if konum[0] >= n or not _ENDIF_RE.match(satirlar[konum[0]].strip()):
                    raise StLogicGecersiz("Kapanmamış IF bloğu (END_IF bulunamadı).")
                konum[0] += 1
                dugumler.append({"kind": "if", "branches": dallar, "elseBody": else_govde})
                continue
            mc, sonraki = _anahtar_esle(konum[0], _CASE_RE, "OF", _CASE_ON)
            if mc:
                bekleyeni_bosalt()
                ifade = mc.group(1).strip()
                konum[0] = sonraki
                kollar = []
                while konum[0] < n:
                    # "CASE ... OF" ile ilk etiket arasında (ya da kollar
                    # arasında) boş satır olabilir — gerçek kullanıcı
                    # dosyasında tam olarak bu vardı, atlamazsak etiket
                    # regex'i boş string'e hiç eşleşmeyip döngü SIFIR kolla
                    # kırılıyordu (yanlışlıkla "END_CASE bulunamadı" hatası).
                    if not satirlar[konum[0]].strip():
                        konum[0] += 1
                        continue
                    lm = _CASE_LABEL_RE.match(satirlar[konum[0]].strip())
                    if not lm:
                        break
                    konum[0] += 1
                    kollar.append({"labels": lm.group(1).strip(), "body": blogu_parsele()})
                else_govde = None
                if konum[0] < n and _ELSE_RE.match(satirlar[konum[0]].strip()):
                    konum[0] += 1
                    else_govde = blogu_parsele()
                if konum[0] >= n or not _ENDCASE_RE.match(satirlar[konum[0]].strip()):
                    raise StLogicGecersiz("Kapanmamış CASE bloğu (END_CASE bulunamadı).")
                konum[0] += 1
                if not kollar:
                    raise StLogicGecersiz("CASE bloğunun en az bir kolu (label) olmalı.")
                dugumler.append({"kind": "case", "expr": ifade, "arms": kollar, "elseBody": else_govde})
                continue
            mf, sonraki = _anahtar_esle(konum[0], _FOR_RE, "DO", _FOR_ON)
            if mf:
                bekleyeni_bosalt()
                konum[0] = sonraki
                govde = blogu_parsele()
                if konum[0] >= n or not _ENDFOR_RE.match(satirlar[konum[0]].strip()):
                    raise StLogicGecersiz("Kapanmamış FOR bloğu (END_FOR bulunamadı).")
                konum[0] += 1
                dugumler.append({
                    "kind": "for", "var": mf.group(1).strip(), "start": mf.group(2).strip(),
                    "end": mf.group(3).strip(), "step": (mf.group(4).strip() if mf.group(4) else None),
                    "body": govde,
                })
                continue
            mw, sonraki = _anahtar_esle(konum[0], _WHILE_RE, "DO", _WHILE_ON)
            if mw:
                bekleyeni_bosalt()
                konum[0] = sonraki
                govde = blogu_parsele()
                if konum[0] >= n or not _ENDWHILE_RE.match(satirlar[konum[0]].strip()):
                    raise StLogicGecersiz("Kapanmamış WHILE bloğu (END_WHILE bulunamadı).")
                konum[0] += 1
                dugumler.append({"kind": "while", "cond": mw.group(1).strip(), "body": govde})
                continue
            if _REPEAT_RE.match(temiz):
                bekleyeni_bosalt()
                konum[0] += 1
                govde = blogu_parsele()
                if konum[0] >= n:
                    raise StLogicGecersiz("Kapanmamış REPEAT bloğu (UNTIL bulunamadı).")
                mu = _UNTIL_RE.match(satirlar[konum[0]].strip())
                if not mu:
                    raise StLogicGecersiz("Kapanmamış REPEAT bloğu (UNTIL bulunamadı).")
                konum[0] += 1
                if konum[0] >= n or not _ENDREPEAT_RE.match(satirlar[konum[0]].strip()):
                    raise StLogicGecersiz("Kapanmamış REPEAT bloğu (END_REPEAT bulunamadı).")
                konum[0] += 1
                dugumler.append({"kind": "repeat", "cond": mu.group(1).strip(), "body": govde})
                continue
            if (_ELSIF_ON.match(temiz) or _ELSE_RE.match(temiz) or _ENDIF_RE.match(temiz)
                    or _ENDCASE_RE.match(temiz) or _CASE_LABEL_RE.match(temiz)
                    or _ENDFOR_RE.match(temiz) or _ENDWHILE_RE.match(temiz)
                    or _UNTIL_RE.match(temiz) or _ENDREPEAT_RE.match(temiz)):
                # bu satır, çağıran (üstteki) IF/CASE/FOR/WHILE/REPEAT'e ait
                # bir dal/kapanış — bu bloğu burada bitirip kontrolü çağırana
                # bırak.
                bekleyeni_bosalt()
                return dugumler
            bekleyen.append(satir)
            if ";" in temiz:
                bekleyeni_bosalt()
            konum[0] += 1
        bekleyeni_bosalt()
        return dugumler

    sonuc = blogu_parsele()
    if konum[0] < n:
        raise StLogicGecersiz(f"Beklenmeyen satır: {satirlar[konum[0]].strip()!r}")
    return sonuc


def render_st_logic(dugumler: list[dict], girinti: int = 0) -> str:
    pad = "\t" * girinti
    satirlar: list[str] = []
    for dugum in dugumler or []:
        tur = dugum.get("kind")
        if tur == "comment":
            metin = str(dugum.get("text", "")).strip()
            satirlar.append(f"{pad}(* {metin} *)" if dugum.get("block") else f"{pad}//{metin}")
        elif tur == "stmt":
            metin = str(dugum.get("text", "")).strip()
            if not metin:
                continue
            parcalar = metin.split("\n")
            satirlar.append(pad + parcalar[0])
            for ek in parcalar[1:]:
                satirlar.append(pad + ek.strip())
        elif tur == "if":
            dallar = dugum.get("branches") or []
            if not dallar:
                raise StLogicGecersiz("IF bloğunun en az bir dalı olmalı.")
            for i, dal in enumerate(dallar):
                kosul = str(dal.get("cond", "")).strip()
                if not kosul:
                    raise StLogicGecersiz("IF/ELSIF koşulu boş olamaz.")
                anahtar = "IF" if i == 0 else "ELSIF"
                satirlar.append(f"{pad}{anahtar} {kosul} THEN")
                alt = render_st_logic(dal.get("body") or [], girinti + 1)
                if alt:
                    satirlar.append(alt)
            else_govde = dugum.get("elseBody")
            if else_govde is not None:
                satirlar.append(f"{pad}ELSE")
                alt = render_st_logic(else_govde, girinti + 1)
                if alt:
                    satirlar.append(alt)
            satirlar.append(f"{pad}END_IF")
        elif tur == "case":
            ifade = str(dugum.get("expr", "")).strip()
            if not ifade:
                raise StLogicGecersiz("CASE ifadesi boş olamaz.")
            kollar = dugum.get("arms") or []
            if not kollar:
                raise StLogicGecersiz("CASE bloğunun en az bir kolu olmalı.")
            satirlar.append(f"{pad}CASE {ifade} OF")
            for kol in kollar:
                etiket = str(kol.get("labels", "")).strip()
                if not etiket:
                    raise StLogicGecersiz("CASE kolunun etiketi (label) boş olamaz.")
                satirlar.append(f"{pad}\t{etiket}:")
                alt = render_st_logic(kol.get("body") or [], girinti + 2)
                if alt:
                    satirlar.append(alt)
            else_govde = dugum.get("elseBody")
            if else_govde is not None:
                satirlar.append(f"{pad}\tELSE")
                alt = render_st_logic(else_govde, girinti + 2)
                if alt:
                    satirlar.append(alt)
            satirlar.append(f"{pad}END_CASE")
        elif tur == "for":
            degisken = str(dugum.get("var", "")).strip()
            baslangic = str(dugum.get("start", "")).strip()
            bitis = str(dugum.get("end", "")).strip()
            adim = dugum.get("step")
            if not degisken or not baslangic or not bitis:
                raise StLogicGecersiz("FOR döngüsünün değişken/başlangıç/bitiş alanları boş olamaz.")
            basSatir = f"{pad}FOR {degisken} := {baslangic} TO {bitis}"
            if adim and str(adim).strip():
                basSatir += f" BY {str(adim).strip()}"
            basSatir += " DO"
            satirlar.append(basSatir)
            alt = render_st_logic(dugum.get("body") or [], girinti + 1)
            if alt:
                satirlar.append(alt)
            satirlar.append(f"{pad}END_FOR")
        elif tur == "while":
            kosul = str(dugum.get("cond", "")).strip()
            if not kosul:
                raise StLogicGecersiz("WHILE koşulu boş olamaz.")
            satirlar.append(f"{pad}WHILE {kosul} DO")
            alt = render_st_logic(dugum.get("body") or [], girinti + 1)
            if alt:
                satirlar.append(alt)
            satirlar.append(f"{pad}END_WHILE")
        elif tur == "repeat":
            kosul = str(dugum.get("cond", "")).strip()
            if not kosul:
                raise StLogicGecersiz("REPEAT/UNTIL koşulu boş olamaz.")
            satirlar.append(f"{pad}REPEAT")
            alt = render_st_logic(dugum.get("body") or [], girinti + 1)
            if alt:
                satirlar.append(alt)
            satirlar.append(f"{pad}UNTIL {kosul}")
            satirlar.append(f"{pad}END_REPEAT")
        else:
            raise StLogicGecersiz(f"Bilinmeyen düğüm tipi: {tur!r}")
    return "\n".join(satirlar)


# ── ST İFADE ayrıştırıcısı — koşulları (IF/ELSIF/WHILE/UNTIL) Scratch tarzı
# iç içe DÜZENLENEBİLİR bloklara çevirmek için. IEC 61131-3'ün standart
# operatör önceliği (düşükten yükseğe): OR/XOR, AND, eşitlik (=/<>),
# karşılaştırma (</>/<=/>=), toplama (+/-), çarpma (*//,MOD), tekli (NOT/-).
# generate_cmd_table/render_st_logic'ten TAMAMEN BAĞIMSIZ — onlar hâlâ
# koşulu düz bir string olarak kullanıyor; bu modül sadece o string'i
# üretmenin/düzenlemenin alternatif bir yolu, üretilen ST çıktısını
# etkilemez.
_IFADE_TOKEN_RE = _re.compile(
    r"\s*(?:"
    r"(?P<TIME>T(?:IME)?#[0-9A-Za-z_]+)"
    r"|(?P<NUM>\d+(?:\.\d+)?)"
    r"|(?P<STR>'[^']*')"
    r"|(?P<ID>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<OP><>|<=|>=|[()\[\].,+\-*/<>=])"
    r")",
    _re.I,
)
_IFADE_ANAHTAR = {"AND", "OR", "XOR", "NOT", "MOD"}


class _StIfadeToken:
    __slots__ = ("tip", "deger")

    def __init__(self, tip: str, deger: str):
        self.tip = tip
        self.deger = deger


class StIfadeGecersiz(ValueError):
    pass


def _ifade_tokenlestir(metin: str) -> list[_StIfadeToken]:
    tokenler: list[_StIfadeToken] = []
    i, n = 0, len(metin)
    while i < n:
        if metin[i].isspace():
            i += 1
            continue
        m = _IFADE_TOKEN_RE.match(metin, i)
        if not m or m.end() == i:
            raise StIfadeGecersiz(f"Tanınmayan karakter: {metin[i:i+8]!r}")
        i = m.end()
        for grp in ("TIME", "NUM", "STR", "ID", "OP"):
            deger = m.group(grp)
            if deger is not None:
                if grp == "ID" and deger.upper() in _IFADE_ANAHTAR:
                    tokenler.append(_StIfadeToken(deger.upper(), deger))
                else:
                    tokenler.append(_StIfadeToken(grp, deger))
                break
    return tokenler


_IFADE_ONCELIK = {
    "OR": 1, "XOR": 1, "AND": 2, "=": 3, "<>": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4, "+": 5, "-": 5, "*": 6, "/": 6, "MOD": 6,
}


class _StIfadeParser:
    def __init__(self, tokenler: list[_StIfadeToken]):
        self.tokenler = tokenler
        self.i = 0

    def bak(self):
        return self.tokenler[self.i] if self.i < len(self.tokenler) else None

    def yut(self, tip: str | None = None) -> _StIfadeToken:
        t = self.bak()
        if t is None:
            raise StIfadeGecersiz(f"İfade eksik bitti (beklenen: {tip or 'token'}).")
        if tip and t.tip != tip:
            raise StIfadeGecersiz(f"Beklenmeyen token: {t.deger!r} (beklenen: {tip}).")
        self.i += 1
        return t

    def _ikili(self, alt_seviye, eslesenler):
        sol = alt_seviye()
        while self.bak() and (self.bak().deger in eslesenler or self.bak().tip in eslesenler):
            op_tok = self.yut()
            op = op_tok.tip if op_tok.tip in _IFADE_ANAHTAR else op_tok.deger
            sag = alt_seviye()
            sol = {"kind": "binop", "op": op, "left": sol, "right": sag}
        return sol

    def ifade(self):
        return self._ikili(self.and_ifade, {"OR", "XOR"})

    def and_ifade(self):
        return self._ikili(self.esitlik, {"AND"})

    def esitlik(self):
        return self._ikili(self.karsilastirma, {"=", "<>"})

    def karsilastirma(self):
        return self._ikili(self.toplama, {"<", ">", "<=", ">="})

    def toplama(self):
        return self._ikili(self.carpma, {"+", "-"})

    def carpma(self):
        return self._ikili(self.birli, {"*", "/", "MOD"})

    def birli(self):
        t = self.bak()
        if t and t.tip == "NOT":
            self.yut()
            return {"kind": "unop", "op": "NOT", "operand": self.birli()}
        if t and t.deger == "-":
            self.yut()
            return {"kind": "unop", "op": "-", "operand": self.birli()}
        return self.birincil()

    def birincil(self):
        t = self.bak()
        if t is None:
            raise StIfadeGecersiz("Beklenmedik ifade sonu.")
        if t.deger == "(":
            self.yut()
            dugum = self.ifade()
            self.yut()
            dugum = {"kind": "group", "inner": dugum}
        elif t.tip in ("NUM", "TIME", "STR"):
            self.yut()
            dugum = {"kind": "lit", "value": t.deger}
        elif t.tip == "ID":
            parcalar = [self.yut().deger]
            while self.bak() and self.bak().deger == ".":
                self.yut()
                parcalar.append(self.yut(tip="ID").deger)
            ad = ".".join(parcalar)
            if self.bak() and self.bak().deger == "(":
                self.yut()
                argumanlar = []
                if self.bak() and self.bak().deger != ")":
                    argumanlar.append(self.ifade())
                    while self.bak() and self.bak().deger == ",":
                        self.yut()
                        argumanlar.append(self.ifade())
                self.yut()
                dugum = {"kind": "call", "name": ad, "args": argumanlar}
            else:
                dugum = {"kind": "var", "name": ad}
        else:
            raise StIfadeGecersiz(f"Beklenmeyen token: {t.deger!r}.")
        while self.bak() and self.bak().deger == "[":
            self.yut()
            idx = self.ifade()
            self.yut()
            dugum = {"kind": "index", "base": dugum, "index": idx}
        return dugum


def parse_st_expression(ifade_metni: str) -> dict:
    """Bir ST BOOLEAN/aritmetik ifadesini (IF/ELSIF/WHILE koşulu gibi)
    operatör önceliğine uygun bir AST'ye çevirir — Scratch tarzı iç içe
    blok düzenleyicisi için. Sadece OKUMA amaçlı; asıl ST üretimini
    (render_st_logic) hiç etkilemez, o hâlâ düz string kullanıyor."""
    try:
        if not ifade_metni or not ifade_metni.strip():
            return {"basarili": False, "ast": None, "hata": "Boş ifade."}
        tokenler = _ifade_tokenlestir(ifade_metni)
        p = _StIfadeParser(tokenler)
        agac = p.ifade()
        if p.i != len(p.tokenler):
            raise StIfadeGecersiz(f"İfade tam ayrıştırılamadı, kalan: {p.bak().deger!r}")
        return {"basarili": True, "ast": agac, "hata": None}
    except StIfadeGecersiz as e:
        return {"basarili": False, "ast": None, "hata": str(e)}
    except Exception as e:
        return {"basarili": False, "ast": None, "hata": f"Beklenmeyen hata: {e}"}


def render_st_expression(ast: dict, dis_oncelik: int = 0) -> str:
    """parse_st_expression'ın tam tersi — AST'yi (JS blok düzenleyicisinde
    değiştirilmiş olabilir) tekrar geçerli bir ST ifadesine çevirir,
    gerekli yerlerde parantez ekler."""
    if not ast:
        raise StIfadeGecersiz("Boş düğüm.")
    kind = ast.get("kind")
    if kind == "lit":
        deger = str(ast.get("value", "")).strip()
        if not deger:
            raise StIfadeGecersiz("Sabit değer boş olamaz.")
        return deger
    if kind == "var":
        ad = str(ast.get("name", "")).strip()
        if not ad:
            raise StIfadeGecersiz("Değişken adı boş olamaz.")
        return ad
    if kind == "group":
        return f"({render_st_expression(ast['inner'])})"
    if kind == "index":
        return f"{render_st_expression(ast['base'])}[{render_st_expression(ast['index'])}]"
    if kind == "call":
        ad = str(ast.get("name", "")).strip()
        if not ad:
            raise StIfadeGecersiz("Çağrı adı boş olamaz.")
        args = ", ".join(render_st_expression(a) for a in ast.get("args", []))
        return f"{ad}({args})"
    if kind == "unop":
        op = ast.get("op")
        ic = render_st_expression(ast["operand"], 100)
        return f"NOT {ic}" if op == "NOT" else f"-{ic}"
    if kind == "binop":
        op = ast.get("op")
        if op not in _IFADE_ONCELIK:
            raise StIfadeGecersiz(f"Bilinmeyen operatör: {op!r}")
        kendi = _IFADE_ONCELIK[op]
        sol = render_st_expression(ast["left"], kendi)
        sag = render_st_expression(ast["right"], kendi + 1)
        metin = f"{sol} {op} {sag}"
        return f"({metin})" if kendi < dis_oncelik else metin
    raise StIfadeGecersiz(f"Bilinmeyen düğüm tipi: {kind!r}")


# web.py bu modüldeki fonksiyonlara bağımlı — import en sonda (circular import önlemi).
from .web import router  # noqa: E402
