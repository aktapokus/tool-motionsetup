"""
CMD Table codegen prototype — Aktapokus Motion Setup Tool.

STATE_NODE primitifinin CMD_TABLE bağlamındaki uygulaması: bir CMD table
sıralı bir "step" listesidir, her step {title, target_udi, cmd, timeout,
is_end} taşır. Bu modül bir step listesini, referans Init_CmdTables
POU'suyla (ExampleModule) birebir yapısal olarak eşleşen ST
kodu haline getirir.

Referans desen (kullanıcının paylaştığı gerçek proje kodundan):
  - İlk step  -> SEQ.FC_FirstStep(udiStepIndex, diStep);
  - Ara step'ler -> SEQ.FC_NextStep(udiStepIndex, diStep);
  - Son step  -> SEQ.FC_LastStep(udiStepIndex, diStep);
  - Her step için 6 alan ata: sTitle, udiModuleName, diStep, diCMD,
    timTimeOut, xEndCMD (bu sırayla, hizalı := ile)
  - Tablo bitince: SEQ.FC_FirstCmdTable + astListofCMDTables[...] 3 satır
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CmdStep:
    title: str
    target_udi: str        # ör. "c_udiGroupTransferZ" ya da "SEQ.Gc_udiAllSubModules"
    cmd: str                # ör. "MC.ET_Cmd.Start" — "diCMD" alanına aynen yazılır
    timeout: str = "T#0MS"
    is_end: bool = False


@dataclass
class CmdTable:
    title: str              # ör. "Prepare" / "Auto"
    cmd_enum: str            # astListofCMDTables[...].diCMD değeri, ör. "ET_Cmd.Prepare"
    array_name: str           # "astPrepareTable" / "astAutoTable"
    steps: list[CmdStep] = field(default_factory=list)


# Referans dosyada alanlar "astPrepareTable[udiStepIndex]." + alan adı + boşluk + ":="
# şeklinde hizalanıyor. En uzun alan adı "udiModuleName" (13 karakter) — hizalama
# ona göre hesaplanıyor, dizi adı ne olursa olsun sabit alan genişliği korunuyor.
_FIELDS = ["sTitle", "udiModuleName", "diStep", "diCMD", "timTimeOut", "xEndCMD"]
_FIELD_WIDTH = max(len(f) for f in _FIELDS)


def _assign_line(array_name: str, field_name: str, value: str) -> str:
    prefix = f"{array_name}[udiStepIndex].{field_name}"
    return f"{prefix.ljust(len(array_name) + 2 + len('udiStepIndex') + 2 + _FIELD_WIDTH)}:= {value};"


def _step_field_values(step: CmdStep) -> dict[str, str]:
    return {
        "sTitle": f"'{step.title}'",
        "udiModuleName": step.target_udi,
        "diStep": "diStep",
        "diCMD": step.cmd,
        "timTimeOut": step.timeout,
        "xEndCMD": "TRUE" if step.is_end else "FALSE",
    }


def generate_cmd_table(table: CmdTable) -> str:
    if not table.steps:
        raise ValueError("CmdTable en az bir step içermeli.")

    lines: list[str] = []
    n = len(table.steps)

    for i, step in enumerate(table.steps):
        if i == 0:
            call = "SEQ.FC_FirstStep(udiStepIndex, diStep);"
        elif i == n - 1:
            call = "SEQ.FC_LastStep(udiStepIndex, diStep);"
        else:
            call = "SEQ.FC_NextStep(udiStepIndex, diStep);"
        lines.append(call)

        values = _step_field_values(step)
        for f in _FIELDS:
            lines.append(_assign_line(table.array_name, f, values[f]))
        lines.append("")  # step'ler arası boş satır (referansla aynı)

    lines.append("SEQ.FC_FirstCmdTable(iq_udiTableIndex:= udiTableIndex);")
    lines.append(f"astListofCMDTables[udiTableIndex].sTitle              := '{table.title}';")
    lines.append(f"astListofCMDTables[udiTableIndex].diCMD               := {table.cmd_enum};")
    lines.append(f"astListofCMDTables[udiTableIndex].udiNumberOfCmdSteps := udiStepIndex;")

    return "\n".join(lines)


# ── Referans "Prepare" tablosunu (Image 1'den transkribe edilen gerçek kod)
# aynı step listesiyle yeniden üretip yapısal olarak doğruluyoruz. ──
if __name__ == "__main__":
    prepare_table = CmdTable(
        title="Prepare",
        cmd_enum="ET_Cmd.Prepare",
        array_name="astPrepareTable",
        steps=[
            CmdStep("DriveEnable On AllSubModules", "SEQ.Gc_udiAllSubModules", "MC.ET_Cmd.DriveEnableOn"),
            CmdStep("Homing Mode AllSubModules", "SEQ.Gc_udiAllSubModules", "MC.ET_Cmd.Homing"),
            CmdStep("Homing Start GroupTransferZ", "c_udiGroupTransferZ", "MC.ET_Cmd.Start"),
            CmdStep("Homing Start GroupTransferX", "c_udiGroupTransferX", "MC.ET_Cmd.Start"),
            CmdStep("End", "0", "0", is_end=True),
        ],
    )
    print(generate_cmd_table(prepare_table))
