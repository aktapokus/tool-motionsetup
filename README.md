# Motion Setup — CMD Table Builder

> ⚠️ **Draft / geliştirme aşamasında.** Bu repo aktif olarak
> değişiyor — henüz kararlı bir sürüm değil, API'ler ve dosya yapısı
> önceden haber verilmeden değişebilir. Gerçek üretim koduyla
> test ediliyor ama henüz "bitti" sayılmıyor.

Schneider Machine Expert / Vervo TPL framework pattern'ini (Equipment
Module, CMD Table, numbered-state sequencer) hedefleyen bir IR → ST
codegen aracı. Bu ilk sürüm sadece **CMD Table builder**'ı kapsıyor
(`Init_CmdTables` POU'sundaki `astPrepareTable`/`astAutoTable` üretimi).

## Logic Editor (Blockly tabanlı ST ↔ blok editörü)

`ui/logic_editor.html` — ayrı bir sekmede açılan, Blockly üzerine kurulu
bir IEC 61131-3 Structured Text editörü. Gerçek ST kodunu (deklarasyon
ya da gövde) yapıştırıp bloklara çevirebiliyor, blokları düzenleyip
tekrar ST koduna dönüştürebiliyorsun. Desteklenenler: IF/ELSIF/ELSE,
CASE, FOR/CONTINUE, fonksiyon/FB çağrıları (IN/OUT parametre ayrımıyla),
aritmetik (+/-/*//÷/MOD, öncelik sırasına duyarlı), karşılaştırma/mantık
operatörleri, satır-içi ve blok yorumları, STRUCT tip tanımları,
bilinen değişkenler için otomatik tamamlama. Kendi el yazması
recursive-descent parser'ı var (`parseStToBlockXml`), üçüncü parti bir
ST parser'ına bağımlı değil.

## Kapsam (v0.1.0)

- Bir CMD table (Prepare/Auto/özel) için sıralı adım listesi oluşturma
  (sürükle-bırak ile yeniden sıralanabilir).
- Her adım: başlık, hedef modül (`udi`), komut (`diCMD`), timeout,
  son-adım işareti.
- `TPL.FC_FirstStep/NextStep/LastStep` + `astListofCMDTables[...]`
  özet bloğunu, gerçek Vervo proje kodundaki referans yapıyla birebir
  eşleşen ST kodu olarak üretir.

## Kapsam dışı (sıradaki fazlar)

- `Logic_active` state machine builder (aynı `STATE_NODE` primitifinin
  genellemesi).
- Cam profile / virtual master senkronizasyonu.
- Ürün ağacı editörü (şu an sadece backend şeması var, `product-tree.
  schema.json`/`module-scaffold.schema.json`).
- Rockwell Studio 5000 backend'i.

## Kurulum

`setup.bat`'ı çalıştırın — `aktapokus-core`'un yolunu soracak, dosyaları
`tools/motionsetup/` altına kopyalayıp container'ı yeniden başlatacak.

## Mimari not

Bu tool `web_analyze`/`web_execute`/`web_rollback` sözleşmesine
(AGENTS.md Madde 3) katılmıyor — "istek + klasör" modeli codegen
girdisiyle uyuşmuyor. Bunun yerine kendi router'ını (Madde 4.1)
expose ediyor: `POST /api/tools/motionsetup/generate`.
