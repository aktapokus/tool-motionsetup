/**
 * tools/motionsetup/ui/panel.js
 * Motion Setup — CMD Table Builder — AGENTS.md Madde 4 + 4.1 sözleşmesi.
 *
 * Bu tool web_analyze/web_execute/web_rollback kullanmaz (istek/klasör
 * modeli buraya uymuyor) — kendi router'ı üzerinden (Madde 4.1) çalışır:
 * POST /api/tools/motionsetup/generate, POST /api/tools/motionsetup/import-topology.
 */

const STYLE_ID = 'motionsetup-panel-style';

const ICON_PLUS = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'><line x1='12' y1='5' x2='12' y2='19'/><line x1='5' y1='12' x2='19' y2='12'/></svg>";
const ICON_TRASH = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><polyline points='3 6 5 6 21 6'/><path d='M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6'/><path d='M10 11v6'/><path d='M14 11v6'/><path d='M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2'/></svg>";
const ICON_DRAG = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round'><line x1='8' y1='6' x2='8' y2='6.01'/><line x1='8' y1='12' x2='8' y2='12.01'/><line x1='8' y1='18' x2='8' y2='18.01'/><line x1='16' y1='6' x2='16' y2='6.01'/><line x1='16' y1='12' x2='16' y2='12.01'/><line x1='16' y1='18' x2='16' y2='18.01'/></svg>";
const ICON_CODE = "<svg viewBox='0 0 24 24' width='15' height='15' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><polyline points='16 18 22 12 16 6'/><polyline points='8 6 2 12 8 18'/></svg>";
const ICON_COPY = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><rect x='9' y='9' width='13' height='13' rx='2'/><path d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/></svg>";
const ICON_CHECK = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>";
const ICON_UPLOAD = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='17 8 12 3 7 8'/><line x1='12' y1='3' x2='12' y2='15'/></svg>";
const ICON_MODULE = "<svg viewBox='0 0 24 24' width='13' height='13' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'><rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/></svg>";
const ICON_LAYERS = "<svg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linejoin='round' stroke-linecap='round'><polygon points='12 2 2 7 12 12 22 7 12 2'/><polyline points='2 17 12 22 22 17'/><polyline points='2 12 12 17 22 12'/></svg>";

const ACCENT = '#7C3AED';
const ACCENT_DARK = '#6D28D9';
const ACCENT_LIGHT = '#EDE9FE';

// Gerçek projede (Vervo TPL) HER modülün Init_CmdTables'ında birebir aynı
// isimlerle tekrar eden 8 standart tablo — tahmin değil, referans XML'den
// doğrulandı (astPrepareTable/astAutoTable/.../astBrakeReleaseTable).
const STANDART_TABLOLAR = [
  { ad: 'Prepare', cmd_enum: 'ET_Cmd.Prepare', array_name: 'astPrepareTable' },
  { ad: 'Auto', cmd_enum: 'ET_Cmd.Auto', array_name: 'astAutoTable' },
  { ad: 'Manual', cmd_enum: 'ET_Cmd.Manual', array_name: 'astManualTable' },
  { ad: 'Stop', cmd_enum: 'ET_Cmd.Stop', array_name: 'astStopTable' },
  { ad: 'Start', cmd_enum: 'ET_Cmd.Start', array_name: 'astStartTable' },
  { ad: 'Abort', cmd_enum: 'ET_Cmd.Abort', array_name: 'astAbortTable' },
  { ad: 'Hold', cmd_enum: 'ET_Cmd.Hold', array_name: 'astHoldTable' },
  { ad: 'BrakeRelease', cmd_enum: 'ET_Cmd.BrakeRelease', array_name: 'astBrakeReleaseTable' },
];

const T_FALLBACK = {
  tablo_baslik_etiket: '// Tablo', tablo_title_placeholder: 'Tablo başlığı (ör. Prepare)',
  tablo_cmdenum_placeholder: 'cmd_enum (ör. ET_Cmd.Prepare)', tablo_arrayname_placeholder: 'array_name (ör. astPrepareTable)',
  steps_etiket: '// Adımlar', surukle_ipucu: 'Soldaki bir Hedef bloğuna, sonra bir Komut bloğuna tıklayarak yeni adım oluşturun (sürüklemeye gerek yok) — ya da kutulara elle yazın.',
  blok_tikla_ipucu: 'Tıklayarak son adıma ekle',
  step_title_placeholder: 'Başlık', step_udi_placeholder: 'Hedef modül (udi)',
  step_cmd_placeholder: 'Komut (diCMD)', step_timeout_placeholder: 'Timeout',
  step_end_label: 'Son adım', step_ayni_adim_label: 'Öncekiyle paralel (aynı adım)',
  adim_ekle_btn: 'Adım Ekle', adim_sil: 'Sil',
  bos_adim_placeholder: '// Henüz adım eklenmedi — "Adım Ekle" ile başlayın',
  kod_uret_btn: 'ST Kodu Üret', kod_kopyala_btn: 'Kopyala', kod_kopyalandi: 'Kopyalandı',
  kod_bos_placeholder: '// Üretilen kod burada görünecek', hata_etiket: 'Hata',
  bilesenler_etiket: '// Bileşenler', xml_ice_aktar_btn: 'Proje XML İçe Aktar',
  ice_aktariliyor: 'İçe aktarılıyor…', ice_aktarma_hatasi: 'İçe aktarma başarısız',
  kapsam_etiket: 'Kapsam', kapsam_ana_makine: 'Ana Makine (modülleri çağırır)',
  hedefler_etiket: 'Hedefler', komutlar_etiket_proje: 'Komutlar (modül — ET_Cmd)',
  komutlar_etiket_axm: 'Komutlar (eksen — AXM.ET_Cmd)', yayin_blok_etiket: 'Tümü (yayın)',
  adreslenemeyen_not: 'Bu modülün eksenleri ayrı hedeflenemiyor — sadece modül seviyesinde',
  ice_aktarilmadi_placeholder: 'Bloklar için önce bir proje XML\'i içe aktarın',
  standart_tablolar_btn: 'Standart Tabloları Oluştur',
  standart_tablolar_ipucu: '8 standart tablo (Prepare/Auto/Manual/Stop/Start/Abort/Hold/BrakeRelease) otomatik oluşturulur — sadece adımları doldurman yeterli.',
};

function ensureStyles() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .ms-theme { --ms-accent: ${ACCENT}; --ms-accent-dark: ${ACCENT_DARK}; --ms-accent-light: ${ACCENT_LIGHT}; }
    .ms-theme .btn-primary { background: var(--ms-accent) !important; border-color: var(--ms-accent) !important; }
    .ms-theme .btn-primary:hover { background: var(--ms-accent-dark) !important; }
    .ms-page { display: flex; flex-direction: column; flex: 1; min-height: 0; }
    .ms-split { display: flex; flex: 1; min-height: 0; overflow: hidden; }
    .ms-palette-col { width: 220px; flex-shrink: 0; border-right: 1px solid var(--border); overflow-y: auto; padding: 16px; }
    .ms-split-left { flex: 1.6 1 0; min-width: 460px; border-right: 1px solid var(--border); overflow-y: auto; padding: 16px; }
    .ms-split-right { flex: 1; min-width: 0; overflow-y: auto; display: flex; flex-direction: column; padding: 16px; }
    .ms-table-meta { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
    .ms-table-meta input { font-family: var(--mono); font-size: 12px; }
    .ms-hint { font-size: 11px; color: var(--text-xs); margin-bottom: 10px; }
    .ms-standart-btn { width: 100%; justify-content: center; margin-bottom: 8px; }
    .ms-tablo-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
    .ms-tablo-tab {
      font-family: var(--mono); font-size: 10px; padding: 5px 9px; border: 1px solid var(--border);
      border-radius: 999px; background: var(--surface-2); color: var(--text-dim); cursor: pointer;
    }
    .ms-tablo-tab.active { background: var(--ms-accent); border-color: var(--ms-accent); color: #fff; }
    .ms-tablo-tab .ms-tab-count { opacity: 0.7; margin-left: 3px; }
    .ms-steps { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
    .ms-step-row {
      display: flex; align-items: center; gap: 6px; padding: 8px; border: 1px solid var(--border);
      border-radius: var(--radius-sm); background: var(--surface-2); cursor: grab;
    }
    .ms-step-row.dragging { opacity: 0.4; }
    .ms-step-drag { color: var(--text-xs); flex-shrink: 0; }
    .ms-step-idx {
      font-family: var(--mono); font-size: 10px; color: var(--ms-accent-dark); background: var(--ms-accent-light);
      border-radius: 3px; padding: 1px 5px; flex-shrink: 0; min-width: 18px; text-align: center;
    }
    .ms-step-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
    .ms-step-fields { display: grid; grid-template-columns: 1.5fr 1.6fr 1.3fr 0.7fr; gap: 6px; min-width: 0; }
    .ms-step-fields input { font-family: var(--mono); font-size: 12px; padding: 6px 8px; min-width: 0; }
    .ms-step-fields input.ms-dropok { border-style: dashed; }
    .ms-step-fields input.ms-dragover { border-color: var(--ms-accent); background: var(--ms-accent-light); }
    .ms-step-flags { display: flex; align-items: center; gap: 10px; }
    .ms-step-flags select { font-family: var(--mono); font-size: 11px; padding: 4px 8px; width: auto; flex-shrink: 0; }
    .ms-step-del { background: none; border: none; color: var(--text-xs); cursor: pointer; padding: 4px; flex-shrink: 0; }
    .ms-step-del:hover { color: var(--red); }
    .ms-empty { padding: 20px; text-align: center; color: var(--text-xs); font-size: 12px; border: 1px dashed var(--border); border-radius: var(--radius-sm); }
    .ms-code-area { flex: 1; min-height: 0; display: flex; flex-direction: column; }
    .ms-code-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .ms-code-title { font-size: 11px; font-weight: 500; color: var(--text-dim); }
    .ms-code-pre {
      flex: 1; min-height: 0; overflow: auto; background: var(--surface-2); border: 1px solid var(--border);
      border-radius: var(--radius-sm); padding: 14px; font-family: var(--mono); font-size: 12px; line-height: 1.6;
      color: var(--text); white-space: pre;
    }
    .ms-code-placeholder { color: var(--text-xs); }
    .ms-import-btn { width: 100%; justify-content: center; margin-bottom: 12px; }
    .ms-kapsam-select { width: 100%; margin-bottom: 12px; }
    .ms-blok-grup-baslik { font-size: 10px; font-weight: 500; color: var(--text-xs); text-transform: uppercase; letter-spacing: 0.06em; margin: 12px 0 6px; }
    .ms-blok-grup-baslik:first-child { margin-top: 0; }
    .ms-blok { display: flex; align-items: center; gap: 5px; padding: 6px 8px; margin-bottom: 4px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface-2); font-size: 11px; font-family: var(--mono); cursor: pointer; }
    .ms-blok:hover { border-color: var(--ms-accent); }
    .ms-blok-eksen { margin-left: 14px; background: var(--bg); }
    .ms-blok-udi { margin-left: auto; color: var(--text-xs); font-size: 9px; }
    .ms-cmd-bloklar { display: flex; flex-wrap: wrap; gap: 4px; }
    .ms-cmd-blok { padding: 4px 8px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface-2); font-size: 10px; font-family: var(--mono); cursor: pointer; }
    .ms-cmd-blok:hover { border-color: var(--ms-accent); }
  `;
  document.head.appendChild(style);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
}

let _msIdSeq = 0;
function yeniStepId() { return `s${++_msIdSeq}`; }

export function mount(container, api, toolId) {
  ensureStyles();
  container.classList.add('ms-theme');

  function t(key, vars) {
    let s = (typeof api.t === 'function') ? api.t(key) : undefined;
    if (s === undefined || s === null || s === key) s = T_FALLBACK[key] ?? key;
    if (vars) for (const k in vars) s = s.split(`{${k}}`).join(vars[k]);
    return s;
  }

  // ── Çoklu tablo state'i — HER KAPSAM (Ana Makine / her modül) kendi 8
  // tablosunu ayrı tutar (tablolarByKapsam[kapsam]). "tablolar" her zaman
  // O ANKİ aktif kapsamın setine işaret eder — Scope değiştiğinde
  // kapsamTablolariniHazirla() bunu günceller. Bu, farklı kapsamların
  // içeriğinin birbirine karışmasını (bkz. geçmişteki bug: ana makine ve
  // modül-içi tabloların aynı array_name'i paylaştığı için yanlışlıkla
  // birleşmesi) ve kapsam değiştirince önceki düzenlemelerin kaybolmasını
  // önler — her kapsamın kendi seti ayrı hafızada kalır. ──
  let tablolarByKapsam = {};
  let tablolar = { Prepare: { title: 'Prepare', cmd_enum: 'ET_Cmd.Prepare', array_name: 'astPrepareTable', steps: [] } };
  let aktifTabloAdi = 'Prepare';
  let dragIdx = null;
  let topology = null;   // { modules, project_et_cmd, axm_et_cmd_used }
  let parseListesi = []; // [{pou, tables}] — import-topology'nin mevcut_tablolar_liste'si
  let kapsam = 'main';   // 'main' | modül adı

  function aktifTablo() { return tablolar[aktifTabloAdi]; }

  // "GroupTransfer" gibi bir kapsam adının, "SR02_GroupTransferModule" gibi
  // bir POU adı içinde SIRAYLA (aralarına başka karakter girebilir, ör.
  // "Robot"+"Module_"+"Gripper" -> "RobotGripper") geçip geçmediğini
  // kontrol eder. Ana makine için POU adında "mainmachine" aranır.
  function pouEslesirMi(pouAdi, kapsamAdi) {
    if (!pouAdi) return false;
    const p = pouAdi.toLowerCase();
    if (kapsamAdi === 'main') return p.replace(/_/g, '').includes('mainmachine');
    const parcalar = kapsamAdi.match(/[A-Z][a-z0-9]*/g) || [kapsamAdi];
    let pos = 0;
    for (const parca of parcalar) {
      const idx = p.indexOf(parca.toLowerCase(), pos);
      if (idx === -1) return false;
      pos = idx + parca.length;
    }
    return true;
  }
  function enIyiEslesenBlokBul(kapsamAdi) {
    return parseListesi.find(blok => pouEslesirMi(blok.pou, kapsamAdi));
  }

  // Belirtilen kapsamın 8 tablosunu hazırlar. zorla=false ve bu kapsam
  // için zaten bir set varsa (kullanıcı düzenlemiş olabilir) DOKUNMAZ —
  // sadece "tablolar" değişkenini o sete işaret ettirir.
  function kapsamTablolariniHazirla(kapsamAdi, zorla) {
    if (!zorla && tablolarByKapsam[kapsamAdi]) {
      tablolar = tablolarByKapsam[kapsamAdi];
      return;
    }
    const eslesenBlok = enIyiEslesenBlokBul(kapsamAdi);
    const yeni = {};
    STANDART_TABLOLAR.forEach(std => {
      const hazir = eslesenBlok && eslesenBlok.tables[std.array_name];
      if (hazir && hazir.steps && hazir.steps.length) {
        yeni[std.ad] = {
          title: hazir.title || std.ad,
          cmd_enum: hazir.cmd_enum || std.cmd_enum,
          array_name: std.array_name,
          steps: hazir.steps.map(s => Object.assign({
            id: yeniStepId(), title: '', target_udi: '', cmd: '', timeout: 'T#0MS', cagri_tipi: 'next',
          }, s)),
        };
      } else {
        yeni[std.ad] = { title: std.ad, cmd_enum: std.cmd_enum, array_name: std.array_name, steps: [] };
      }
    });
    tablolarByKapsam[kapsamAdi] = yeni;
    tablolar = yeni;
    aktifTabloAdi = 'Prepare';
  }

  container.innerHTML = `
    <div class="ms-page">
      <div class="ms-split">
        <div class="ms-palette-col">
          <div class="field-block">
            <label class="field-label">${esc(t('bilesenler_etiket'))}</label>
            <input type="file" id="msXmlDosya" accept=".xml" style="display:none">
            <button class="btn-secondary ms-import-btn" id="msIceAktarBtn">${ICON_UPLOAD} ${esc(t('xml_ice_aktar_btn'))}</button>
            <button class="btn-secondary ms-import-btn" id="msLogicEditorBtn">${ICON_CODE} ${esc(t('logic_editor_btn'))}</button>
          </div>
          <div id="msPaletteBody"><div class="ms-hint">${esc(t('ice_aktarilmadi_placeholder'))}</div></div>
        </div>
        <div class="ms-split-left">
          <div class="field-block">
            <button class="btn-secondary ms-standart-btn" id="msStandartBtn">${ICON_LAYERS} ${esc(t('standart_tablolar_btn'))}</button>
            <div class="ms-hint">${esc(t('standart_tablolar_ipucu'))}</div>
            <div class="ms-tablo-tabs" id="msTabloTabs"></div>
          </div>
          <div class="field-block">
            <label class="field-label">${esc(t('tablo_baslik_etiket'))}</label>
            <div class="ms-table-meta">
              <input type="text" id="msTabloTitle" placeholder="${esc(t('tablo_title_placeholder'))}">
              <input type="text" id="msTabloCmdEnum" placeholder="${esc(t('tablo_cmdenum_placeholder'))}">
              <input type="text" id="msTabloArrayName" placeholder="${esc(t('tablo_arrayname_placeholder'))}">
            </div>
          </div>
          <div class="field-block">
            <label class="field-label">${esc(t('steps_etiket'))}</label>
            <div class="ms-hint">${esc(t('surukle_ipucu'))}</div>
            <div class="ms-steps" id="msSteps"></div>
            <button class="btn-secondary" id="msAdimEkleBtn">${ICON_PLUS} ${esc(t('adim_ekle_btn'))}</button>
          </div>
        </div>
        <div class="ms-split-right">
          <div class="ms-code-area">
            <div class="ms-code-header">
              <span class="ms-code-title">// ST</span>
              <div style="display:flex;gap:8px">
                <button class="btn-secondary" id="msIndirBtn" style="display:none">${ICON_UPLOAD} ${esc(t('kod_indir_btn'))}</button>
                <button class="btn-secondary" id="msKopyalaBtn" style="display:none">${ICON_COPY} ${esc(t('kod_kopyala_btn'))}</button>
                <button class="btn-primary" id="msUretBtn">${ICON_CODE} ${esc(t('kod_uret_btn'))}</button>
              </div>
            </div>
            <pre class="ms-code-pre" id="msKodPre"><span class="ms-code-placeholder">${esc(t('kod_bos_placeholder'))}</span></pre>
          </div>
        </div>
      </div>
    </div>
  `;

  const tabsEl = container.querySelector('#msTabloTabs');
  const titleEl = container.querySelector('#msTabloTitle');
  const cmdEnumEl = container.querySelector('#msTabloCmdEnum');
  const arrayNameEl = container.querySelector('#msTabloArrayName');
  const stepsEl = container.querySelector('#msSteps');
  const kodPre = container.querySelector('#msKodPre');
  const kopyalaBtn = container.querySelector('#msKopyalaBtn');
  const indirBtn = container.querySelector('#msIndirBtn');
  const paletteBody = container.querySelector('#msPaletteBody');
  const xmlDosyaInput = container.querySelector('#msXmlDosya');

  function renderTabs() {
    const adlar = Object.keys(tablolar);
    tabsEl.innerHTML = adlar.map(ad => `
      <button class="ms-tablo-tab ${ad === aktifTabloAdi ? 'active' : ''}" data-tab="${esc(ad)}">
        ${esc(ad)}<span class="ms-tab-count">${tablolar[ad].steps.length}</span>
      </button>
    `).join('');
    tabsEl.querySelectorAll('[data-tab]').forEach(btn => {
      btn.onclick = () => {
        aktifTabloAdi = btn.dataset.tab;
        renderTableMeta();
        renderSteps();
        renderTabs();
      };
    });
  }

  function renderTableMeta() {
    const tbl = aktifTablo();
    titleEl.value = tbl.title;
    cmdEnumEl.value = tbl.cmd_enum;
    arrayNameEl.value = tbl.array_name;
  }

  titleEl.oninput = () => { aktifTablo().title = titleEl.value; renderTabs(); };
  cmdEnumEl.oninput = () => aktifTablo().cmd_enum = cmdEnumEl.value;
  arrayNameEl.oninput = () => aktifTablo().array_name = arrayNameEl.value;

  container.querySelector('#msStandartBtn').onclick = () => {
    kapsamTablolariniHazirla(kapsam, true); // zorla=true: bu kapsamı sıfırdan yeniden kur
    renderTableMeta();
    renderSteps();
    renderTabs();
  };

  // ── XML içe aktarma ──
  container.querySelector('#msIceAktarBtn').onclick = () => xmlDosyaInput.click();
  container.querySelector('#msLogicEditorBtn').onclick = () => {
    const tok = window.__AKTAPOKUS_TOKEN__ || '';
    window.open(`/tool-ui/${toolId}/logic_editor.html?token=${encodeURIComponent(tok)}`, '_blank');
  };
  xmlDosyaInput.onchange = async () => {
    const dosya = xmlDosyaInput.files[0];
    if (!dosya) return;
    paletteBody.innerHTML = `<div class="ms-hint">${esc(t('ice_aktariliyor'))}</div>`;
    try {
      const fd = new FormData();
      fd.append('file', dosya);
      const r = await api.apiFetch(`/api/tools/${toolId}/import-topology`, { method: 'POST', body: fd });
      const d = await r.json();
      if (!r.ok || d.hata) {
        paletteBody.innerHTML = `<div class="ms-hint" style="color:var(--red)">${esc(t('ice_aktarma_hatasi'))}: ${esc(d.hata || '')}</div>`;
        return;
      }
      topology = d;
      parseListesi = d.mevcut_tablolar_liste || [];
      kapsam = 'main';
      tablolarByKapsam = {}; // yeni dosya — önceki kapsam düzenlemeleri geçersiz
      renderPalette();
      // Proje XML'inde zaten yazılı olan tabloları otomatik doldur —
      // kullanıcı "Standart Tabloları Oluştur"a basmadan hazır gelsin.
      kapsamTablolariniHazirla('main', true);
      renderTableMeta();
      renderSteps();
      renderTabs();
    } catch (e) {
      paletteBody.innerHTML = `<div class="ms-hint" style="color:var(--red)">${esc(t('ice_aktarma_hatasi'))}: ${esc(e.message)}</div>`;
    }
  };

  function blokHtml(deger, etiket, udiGoster, ekSinif) {
    return `
      <div class="ms-blok ${ekSinif || ''}" draggable="true" data-drag-value="${esc(deger)}" data-blok-alan="target_udi" data-blok-etiket="${esc(etiket)}" title="${esc(t('blok_tikla_ipucu'))}">
        ${ICON_MODULE} <span>${esc(etiket)}</span>
        ${udiGoster !== undefined ? `<span class="ms-blok-udi">udi=${esc(udiGoster)}</span>` : ''}
      </div>`;
  }

  // Blok tıklama: hedef ("target_udi") bloğu her zaman YENİ bir adım açar
  // (önceki adım tamamsa) ya da son adımın hedefini doldurur — VE aynı
  // anda başlığı ("{Tablo} {Hedef}", ör. "Prepare BoxTransfer") ve komutu
  // (aktif tablonun kendi cmd_enum'u, ör. ET_Cmd.Prepare) da otomatik
  // doldurur — gerçek projede standart tablolardaki HER adımın komutu zaten
  // tablonun kendi komutuyla aynı, kullanıcının bunu tekrar tekrar
  // seçmesine gerek yok. Özel bir durum (ör. eksen homing'i farklı bir
  // AXM.ET_Cmd.* istiyorsa) bir komut bloğuna tıklayarak override edilebilir.
  // Sürükle-bırak alternatif olarak kalıyor ama artık tek yol değil.
  function blokUygula(alan, deger, etiket) {
    const tbl = aktifTablo();
    const steps = tbl.steps;
    let sonAdim = steps[steps.length - 1];
    if (alan === 'target_udi') {
      const otomatikBaslik = etiket ? `${tbl.title} ${etiket}`.trim() : '';
      if (!sonAdim || (sonAdim.target_udi && sonAdim.cmd)) {
        stepEkle({ target_udi: deger, title: otomatikBaslik, cmd: tbl.cmd_enum });
        return;
      }
      sonAdim.target_udi = deger;
      if (!sonAdim.title) sonAdim.title = otomatikBaslik;
      if (!sonAdim.cmd) sonAdim.cmd = tbl.cmd_enum;
    } else {
      if (!sonAdim) { stepEkle({ cmd: deger }); return; }
      sonAdim.cmd = deger;
    }
    renderSteps();
    renderTabs();
  }

  function renderPalette() {
    if (!topology) {
      paletteBody.innerHTML = `<div class="ms-hint">${esc(t('ice_aktarilmadi_placeholder'))}</div>`;
      return;
    }
    const modules = topology.modules || [];

    const kapsamOptions = [
      `<option value="main">${esc(t('kapsam_ana_makine'))}</option>`,
      ...modules.map(m => `<option value="${esc(m.name)}" ${kapsam === m.name ? 'selected' : ''}>${esc(m.name)}</option>`),
    ].join('');

    let hedefBlokHtml;
    if (kapsam === 'main') {
      hedefBlokHtml = blokHtml('TPL.Gc_udiAllSubModules', t('yayin_blok_etiket'))
        + modules.map(m => blokHtml(m.udi_const, m.name, m.udi_value)).join('');
    } else {
      const mod = modules.find(m => m.name === kapsam);
      const eksenler = mod ? mod.axes || [] : [];
      const adreslenebilir = eksenler.filter(a => a.addressable);
      const adreslenemeyen = eksenler.filter(a => !a.addressable);
      hedefBlokHtml = blokHtml('TPL.Gc_udiAllSubModules', t('yayin_blok_etiket'))
        + adreslenebilir.map(a => blokHtml(a.udi_const, a.name, undefined, 'ms-blok-eksen')).join('')
        + (adreslenemeyen.length
            ? `<div class="ms-hint">${esc(t('adreslenemeyen_not'))}: ${adreslenemeyen.map(a => esc(a.name)).join(', ')}</div>`
            : '');
    }

    const projeKomutlar = (topology.project_et_cmd || [])
      .map(c => `<div class="ms-cmd-blok" draggable="true" data-drag-value="ET_Cmd.${esc(c.name)}" data-blok-alan="cmd" title="${esc(t('blok_tikla_ipucu'))}">${esc(c.name)}</div>`).join('');
    const axmKomutlar = (topology.axm_et_cmd_used || [])
      .map(name => `<div class="ms-cmd-blok" draggable="true" data-drag-value="AXM.ET_Cmd.${esc(name)}" data-blok-alan="cmd" title="${esc(t('blok_tikla_ipucu'))}">${esc(name)}</div>`).join('');

    paletteBody.innerHTML = `
      <label class="field-label">${esc(t('kapsam_etiket'))}</label>
      <select class="tool-select ms-kapsam-select" id="msKapsamSelect">${kapsamOptions}</select>
      <div class="ms-blok-grup-baslik">${esc(t('hedefler_etiket'))}</div>
      ${hedefBlokHtml}
      <div class="ms-blok-grup-baslik">${esc(t('komutlar_etiket_proje'))}</div>
      <div class="ms-cmd-bloklar">${projeKomutlar}</div>
      <div class="ms-blok-grup-baslik">${esc(t('komutlar_etiket_axm'))}</div>
      <div class="ms-cmd-bloklar">${axmKomutlar}</div>
    `;

    paletteBody.querySelector('#msKapsamSelect').onchange = (e) => {
      kapsam = e.target.value;
      // Bu kapsam ilk kez ziyaret ediliyorsa (zorla=false) eşleşen XML
      // verisinden otomatik doldurulur; daha önce ziyaret edildiyse
      // kullanıcının düzenlemeleri korunur, üzerine yazılmaz.
      kapsamTablolariniHazirla(kapsam, false);
      renderTableMeta();
      renderSteps();
      renderTabs();
      renderPalette();
    };
    paletteBody.querySelectorAll('[data-drag-value]').forEach(el => {
      el.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', el.dataset.dragValue);
        e.dataTransfer.effectAllowed = 'copy';
      });
      el.onclick = () => blokUygula(el.dataset.blokAlan, el.dataset.dragValue, el.dataset.blokEtiket);
    });
  }

  // "first" HER ZAMAN listenin ilk elemanı olmak zorunda (framework kuralı,
  // AGENTS.md'de değil ama gerçek TPL kodunda doğrulandı) — bu yüzden yeni
  // bir step eklerken: ilk step ise 'first', değilse 'next' varsayılan.
  // Önceki "son" step artık son olmayacağı için otomatik 'next'e demote
  // edilir — kullanıcı "Last"ı unutup yeni adım eklediğinde sessizce
  // geçersiz bir tablo oluşmasın diye.
  function stepEkle(baslangic) {
    const steps = aktifTablo().steps;
    if (steps.length && steps[steps.length - 1].cagri_tipi === 'last') {
      steps[steps.length - 1].cagri_tipi = 'next';
    }
    steps.push(Object.assign({
      id: yeniStepId(), title: '', target_udi: '', cmd: '', timeout: 'T#0MS',
      cagri_tipi: steps.length === 0 ? 'first' : 'next',
    }, baslangic || {}));
    renderSteps();
    renderTabs();
  }

  const CAGRI_TIPI_ETIKET = {
    first: 'First (İlk Adım)', same: 'Same (Aynı Adım — paralel)',
    next: 'Next (Sıradaki Adım)', last: 'Last (Son Adım — tabloyu kapatır)',
  };

  function renderSteps() {
    const steps = aktifTablo().steps;
    if (!steps.length) {
      stepsEl.innerHTML = `<div class="ms-empty">${esc(t('bos_adim_placeholder'))}</div>`;
      return;
    }
    stepsEl.innerHTML = steps.map((s, i) => {
      const ilkSatir = i === 0;
      const secenekler = ilkSatir ? ['first'] : ['same', 'next', 'last'];
      return `
      <div class="ms-step-row" draggable="true" data-idx="${i}">
        <span class="ms-step-drag">${ICON_DRAG}</span>
        <span class="ms-step-idx">${i + 1}</span>
        <div class="ms-step-body">
          <div class="ms-step-fields">
            <input type="text" data-field="title" data-idx="${i}" placeholder="${esc(t('step_title_placeholder'))}" value="${esc(s.title)}">
            <input type="text" data-field="target_udi" data-idx="${i}" class="ms-dropok" placeholder="${esc(t('step_udi_placeholder'))}" value="${esc(s.target_udi)}">
            <input type="text" data-field="cmd" data-idx="${i}" class="ms-dropok" placeholder="${esc(t('step_cmd_placeholder'))}" value="${esc(s.cmd)}">
            <input type="text" data-field="timeout" data-idx="${i}" placeholder="${esc(t('step_timeout_placeholder'))}" value="${esc(s.timeout)}">
          </div>
          <div class="ms-step-flags">
            <select class="tool-select" data-field="cagri_tipi" data-idx="${i}" ${ilkSatir ? 'disabled' : ''}>
              ${secenekler.map(v => `<option value="${v}" ${s.cagri_tipi === v ? 'selected' : ''}>${esc(CAGRI_TIPI_ETIKET[v])}</option>`).join('')}
            </select>
          </div>
        </div>
        <button class="ms-step-del" data-del="${i}" title="${esc(t('adim_sil'))}">${ICON_TRASH}</button>
      </div>
    `;
    }).join('');

    stepsEl.querySelectorAll('input[data-field], select[data-field]').forEach(inp => {
      const idx = Number(inp.dataset.idx);
      const field = inp.dataset.field;
      const handler = () => {
        aktifTablo().steps[idx][field] = inp.type === 'checkbox' ? inp.checked : inp.value;
      };
      inp.addEventListener(inp.type === 'checkbox' ? 'change' : (inp.tagName === 'SELECT' ? 'change' : 'input'), handler);
    });
    stepsEl.querySelectorAll('[data-del]').forEach(btn => {
      btn.onclick = () => { aktifTablo().steps.splice(Number(btn.dataset.del), 1); renderSteps(); renderTabs(); };
    });

    // Palet bloklarının bırakılabileceği alanlar (hedef modül / komut).
    stepsEl.querySelectorAll('input.ms-dropok').forEach(inp => {
      inp.addEventListener('dragover', (e) => { e.preventDefault(); inp.classList.add('ms-dragover'); });
      inp.addEventListener('dragleave', () => inp.classList.remove('ms-dragover'));
      inp.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        inp.classList.remove('ms-dragover');
        const deger = e.dataTransfer.getData('text/plain');
        if (!deger) return;
        inp.value = deger;
        aktifTablo().steps[Number(inp.dataset.idx)][inp.dataset.field] = deger;
      });
    });

    stepsEl.querySelectorAll('.ms-step-row').forEach(row => {
      row.addEventListener('dragstart', (e) => {
        dragIdx = Number(row.dataset.idx);
        row.classList.add('dragging');
      });
      row.addEventListener('dragend', () => row.classList.remove('dragging'));
      row.addEventListener('dragover', (e) => e.preventDefault());
      row.addEventListener('drop', (e) => {
        if (dragIdx === null) return; // palet blogu buraya kadar bubble ettiyse (input kendi drop'unu zaten islemisti) yoksay
        e.preventDefault();
        const targetIdx = Number(row.dataset.idx);
        if (dragIdx === targetIdx) return;
        const steps = aktifTablo().steps;
        const [moved] = steps.splice(dragIdx, 1);
        steps.splice(targetIdx, 0, moved);
        dragIdx = null;
        renderSteps();
      });
    });
  }

  container.querySelector('#msAdimEkleBtn').onclick = () => stepEkle();
  renderTableMeta();
  renderSteps();
  renderTabs();
  renderPalette();

  container.querySelector('#msUretBtn').onclick = async () => {
    kopyalaBtn.style.display = 'none';
    indirBtn.style.display = 'none';
    kodPre.textContent = '';
    // Tek tıkla, aktif kapsamdaki 8 standart tablonun TAMAMI tek sayfada
    // üretilir (kullanıcı isteği: ayrı ayrı değil, hepsi bir arada) — boş
    // (adımsız) tablolar atlanır. Kapsam içinde SADECE ilk dolu tablo
    // FC_FirstCmdTable kullanır, ondan sonraki her tablo aynı
    // astListofCMDTables[]'e FC_NextCmdTable ile eklenir (referans dosyada
    // doğrulandı: Prepare=First, geri kalan 7 tablo=Next).
    const doluTablolar = Object.keys(tablolar).filter(ad => tablolar[ad].steps.length > 0);
    if (doluTablolar.length === 0) {
      kodPre.innerHTML = `<span style="color:var(--red)">${esc(t('hata_etiket'))}: ${esc(t('bos_adim_placeholder'))}</span>`;
      return;
    }
    const parcalar = [];
    let hataVarMi = false;
    for (let i = 0; i < doluTablolar.length; i++) {
      const ad = doluTablolar[i];
      const tbl = tablolar[ad];
      try {
        const r = await api.apiFetch(`/api/tools/${toolId}/generate`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: tbl.title, cmd_enum: tbl.cmd_enum, array_name: tbl.array_name,
            steps: tbl.steps.map(s => ({
              title: s.title, target_udi: s.target_udi, cmd: s.cmd, timeout: s.timeout,
              cagri_tipi: s.cagri_tipi,
            })),
            ilk_tablo: i === 0,
          }),
        });
        const d = await r.json();
        if (!r.ok || !d.basarili) {
          hataVarMi = true;
          parcalar.push(`(* ${ad} — ${t('hata_etiket')}: ${d.hata || d.detail || 'bilinmeyen hata'} *)`);
        } else {
          parcalar.push(d.kod);
        }
      } catch (e) {
        hataVarMi = true;
        parcalar.push(`(* ${ad} — ${t('hata_etiket')}: ${e.message} *)`);
      }
    }
    kodPre.textContent = parcalar.join('\n\n');
    if (!hataVarMi) {
      kopyalaBtn.style.display = '';
      indirBtn.style.display = '';
    }
  };

  indirBtn.onclick = () => {
    const dosyaAdi = `${(kapsam === 'main' ? 'MainMachine' : kapsam)}_Init_CmdTables.st`;
    const blob = new Blob([kodPre.textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = dosyaAdi;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  kopyalaBtn.onclick = async () => {
    try {
      await navigator.clipboard.writeText(kodPre.textContent);
      const orijinal = kopyalaBtn.innerHTML;
      kopyalaBtn.innerHTML = `${ICON_CHECK} ${esc(t('kod_kopyalandi'))}`;
      setTimeout(() => kopyalaBtn.innerHTML = orijinal, 1500);
    } catch (e) {
      api.gosterfeedback && api.gosterfeedback(e.message, 'err');
    }
  };
}

export function unmount(container) {
  container.classList.remove('ms-theme');
  container.innerHTML = '';
}
