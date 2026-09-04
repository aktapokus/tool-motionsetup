"""
tools/motionsetup/web.py
Motion Setup — CMD Table Builder router.

Bu tool web_analyze/web_execute/web_rollback (AGENTS.md Madde 3)
SÖZLEŞMESİNE KATILMIYOR — "istek + klasör" modeli bu araca uymuyor
(codegen girdisi bir step listesi, bir klasör/serbest metin değil).
Bunun yerine kendi router'ını expose ediyor (Madde 4.1, Gmail'in OAuth
route'larıyla aynı desen) — core bunu otomatik mount eder, hiçbir satır
core/api.py'ye eklenmez.
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter()


@router.post("/import-topology")
async def import_topology(file: UploadFile = File(...)):
    from . import extract_topology, parse_init_cmdtables

    ham = await file.read()
    try:
        metin = ham.decode("utf-8-sig")
    except UnicodeDecodeError:
        metin = ham.decode("utf-8", errors="replace")
    sonuc = extract_topology(metin)
    sonuc["mevcut_tablolar_liste"] = parse_init_cmdtables(metin)
    return sonuc


class CmdStepIstek(BaseModel):
    title: str
    target_udi: str
    cmd: str
    timeout: str = "T#0MS"
    cagri_tipi: str = "next"


class CmdTableIstek(BaseModel):
    title: str
    cmd_enum: str
    array_name: str
    steps: list[CmdStepIstek]
    ilk_tablo: bool = True


@router.post("/generate")
def generate(istek: CmdTableIstek):
    from . import CmdTable, generate_cmd_table, CmdTableGecersiz

    table = CmdTable.from_dict(istek.model_dump())
    try:
        kod = generate_cmd_table(table, ilk_tablo=istek.ilk_tablo)
    except CmdTableGecersiz as e:
        return {"basarili": False, "hata": str(e), "kod": None}
    return {"basarili": True, "hata": None, "kod": kod}


class StLogicParseIstek(BaseModel):
    text: str


class StLogicRenderIstek(BaseModel):
    nodes: list[dict]


@router.post("/logic/parse")
def logic_parse(istek: StLogicParseIstek):
    from . import parse_st_logic, StLogicGecersiz

    try:
        tree = parse_st_logic(istek.text)
    except StLogicGecersiz as e:
        return {"basarili": False, "hata": str(e), "tree": None}
    except Exception as e:
        return {"basarili": False, "hata": f"Beklenmeyen hata: {e}", "tree": None}
    return {"basarili": True, "hata": None, "tree": tree}


@router.post("/logic/render")
def logic_render(istek: StLogicRenderIstek):
    from . import render_st_logic, StLogicGecersiz

    try:
        kod = render_st_logic(istek.nodes)
    except StLogicGecersiz as e:
        return {"basarili": False, "hata": str(e), "kod": None}
    except Exception as e:
        return {"basarili": False, "hata": f"Beklenmeyen hata: {e}", "kod": None}
    return {"basarili": True, "hata": None, "kod": kod}


class PouArayuzIstek(BaseModel):
    xml: str
    pou_adi: str | None = None


@router.post("/interface/extract")
def interface_extract(istek: PouArayuzIstek):
    from . import extract_pou_interface

    return extract_pou_interface(istek.xml, istek.pou_adi)


class GovdeIstek(BaseModel):
    text: str


@router.post("/interface/infer")
def interface_infer(istek: GovdeIstek):
    from . import infer_io_from_body

    return infer_io_from_body(istek.text)


class IfadeAyristirIstek(BaseModel):
    text: str


@router.post("/expr/parse")
def expr_parse(istek: IfadeAyristirIstek):
    from . import parse_st_expression

    return parse_st_expression(istek.text)


class IfadeUretIstek(BaseModel):
    ast: dict


@router.post("/expr/render")
def expr_render(istek: IfadeUretIstek):
    from . import render_st_expression, StIfadeGecersiz

    try:
        return {"basarili": True, "text": render_st_expression(istek.ast), "hata": None}
    except StIfadeGecersiz as e:
        return {"basarili": False, "text": None, "hata": str(e)}
    except Exception as e:
        return {"basarili": False, "text": None, "hata": f"Beklenmeyen hata: {e}"}


@router.get("/custom-blocks")
def custom_blocks_list():
    from . import ozel_bloklari_oku

    return {"bloklar": ozel_bloklari_oku()}


class OzelBlokIstek(BaseModel):
    bloklar: list[dict]


@router.post("/custom-blocks")
def custom_blocks_save(istek: OzelBlokIstek):
    from . import ozel_bloklari_yaz

    try:
        ozel_bloklari_yaz(istek.bloklar)
    except Exception as e:
        return {"basarili": False, "hata": str(e)}
    return {"basarili": True, "hata": None}
