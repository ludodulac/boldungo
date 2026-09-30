import { getActiveProjectSnapshot, photoRecordToFile } from './project-photo-store.js';
// Hybrid Photos -> Survey PDF generator.
// Register before the historical v0.4 raster generator so this capture listener
// owns the download while the established prompt/audit modules remain intact.
const button = document.querySelector('#download-ai-package');
const status = document.querySelector('#ai-package-status');
const knownWidth = document.querySelector('#known-width');
const studs = document.querySelector('#studs');
const notes = document.querySelector('#notes');

const SLOT_ORDER = ['front', 'right', 'left', 'rear'];
const SLOT_LABELS = {
  front: 'Façade avant',
  right: 'Côté droit',
  left: 'Côté gauche',
  rear: 'Arrière',
};
const DETAIL_ORDER = ['detail_1', 'detail_2', 'detail_3', 'detail_4', 'detail_5', 'detail_6'];
const MAX_PHOTOS_PER_GROUP = 4;
const MAX_PHOTOS = 40;

const PDF_HANDOFF_VERSION = 'pdf-handoff-0.10-hybrid-text';
const PACKAGE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf';
const PAGE_W = 960;
const PAGE_H = 1358;
const MARGIN = 64;
const TEXT_SIZE = 19;
const TEXT_LINE_HEIGHT = 27;

function setReadyStatus() {
  if (status) {
    status.textContent = `Handoff ${PDF_HANDOFF_VERSION} prêt · ${PACKAGE_FILENAME} · consignes PDF en texte extractible · photos originales intégrées`;
  }
}
// Historical modules evaluate after this one and may set their own initial
// message. Refresh ours once the current module turn has completed.
setTimeout(setReadyStatus, 0);

function orientationConfirmed() {
  return Boolean(document.querySelector('#confirm-guided-orientations')?.checked);
}

function nativePhotoRecords() {
  const records = [];
  for (const slotName of SLOT_ORDER) {
    const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.guided-photo-input');
    const note = slot?.querySelector('.guided-photo-note')?.value.trim() || '';
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach((file, index) => records.push({
      file,
      slot: slotName,
      label: SLOT_LABELS[slotName] || slotName,
      note,
      slotViewIndex: index + 1,
      photoId: null,
      primaryFace: slotName.toUpperCase(),
      detailGroupId: null,
      captureRole: 'facade_view',
      orientationAuthority: orientationConfirmed() ? 'user_confirmed' : 'capture_hint',
    }));
  }
  for (const slotName of DETAIL_ORDER) {
    const slot = document.querySelector(`.detail-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.detail-photo-input');
    const note = slot?.querySelector('.detail-photo-note')?.value.trim() || '';
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach((file, index) => records.push({
      file,
      slot: slotName,
      label: slot?.dataset.label || slotName,
      note,
      slotViewIndex: index + 1,
      photoId: null,
      primaryFace: null,
      detailGroupId: slotName,
      captureRole: 'targeted_detail',
      orientationAuthority: 'none',
    }));
  }
  if (records.length > MAX_PHOTOS) throw new Error(`Maximum ${MAX_PHOTOS} photos pour ce handoff.`);
  return records;
}

async function photoRecords() {
  try {
    await window.boldungoProjectPhotoSavePromise;
  } catch {
    // The existing handoff remains available if local persistence failed.
  }

  try {
    const snapshot = await getActiveProjectSnapshot();
    if (snapshot.photos.length) {
      const records = snapshot.photos.map(photo => {
        const slot = photo.primary_face ? photo.primary_face.toLowerCase() : photo.detail_group_id;
        const detailNumber = photo.detail_group_id ? Number(String(photo.detail_group_id).split('_')[1]) : null;
        return {
          file: photoRecordToFile(photo),
          photoId: photo.photo_id,
          primaryFace: photo.primary_face,
          detailGroupId: photo.detail_group_id,
          slot,
          label: photo.primary_face ? (SLOT_LABELS[slot] || slot) : `Détail ${detailNumber || ''}`.trim(),
          note: photo.note || '',
          slotViewIndex: photo.capture_order,
          captureRole: photo.primary_face ? 'facade_view' : 'targeted_detail',
          orientationAuthority: photo.primary_face
            ? (snapshot.project.orientation_confirmed ? 'user_confirmed' : 'capture_hint')
            : 'none',
        };
      });
      if (records.length > MAX_PHOTOS) throw new Error(`Maximum ${MAX_PHOTOS} photos pour ce handoff.`);
      return { records, project: snapshot.project, source: 'indexeddb_project' };
    }
    return { records: nativePhotoRecords(), project: snapshot.project, source: 'native_inputs_fallback' };
  } catch {
    return { records: nativePhotoRecords(), project: null, source: 'native_inputs_fallback' };
  }
}

async function fetchText(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.text();
}

function commandText(records, project, topology, survey, outputContract) {
  const width = Number(knownWidth?.value);
  const targetStuds = Number(studs?.value) || 48;
  const confirmed = orientationConfirmed();
  const photoLines = records.map((record, index) =>
    `${index + 1}. ${record.file.name} — ${record.label}` +
    ` — photo_id=${record.photoId || 'UNPERSISTED'}` +
    ` — PRIMARY_FACE=${record.primaryFace || 'NONE'}` +
    `${record.detailGroupId ? ` — detail_group_id=${record.detailGroupId}` : ''}` +
    `${record.slotViewIndex > 1 ? ` (vue ${record.slotViewIndex})` : ''}` +
    `${record.note ? ` — note utilisateur: ${record.note}` : ''}` +
    ` — capture_role=${record.captureRole} — orientation_authority=${record.orientationAuthority}`
  ).join('\n');
  const orientationRule = confirmed
    ? 'Les orientations Avant / Droite / Gauche / Arrière ont été confirmées par l’utilisateur et sont des contraintes fortes. Les groupes targeted_detail n’ont aucune façade implicite.'
    : 'Les libellés des quatre cases de façade sont des indices de capture seulement. Vérifie-les par recoupement multi-vues. Les groupes targeted_detail n’ont aucune façade implicite.';

  return `BRICKHOUSE — HANDOFF PHOTOS -> SURVEY\nHANDOFF_VERSION=${PDF_HANDOFF_VERSION}\n\nOBJECTIF UNIQUE\nAnalyse les pages photo de CE PDF, exécute la topologie comme raisonnement intermédiaire, puis produis UNIQUEMENT un ArchitecturalSurvey v0.1 complet. NE CONSTRUIS PAS DE SCENE dans ce tour. La Scene sera reconstruite seulement après validation du Survey par Boldungo.\n\nINTERDIT\n- ne demande aucune confirmation ni information supplémentaire ;\n- ne produis ni Scene, ni BuildingModel, ni LEGO ;\n- ne réponds pas par une synthèse ;\n- ne complète jamais une zone cachée par plausibilité ;\n- ne transforme jamais un groupe targeted_detail en façade pour satisfaire un schéma ;\n- ne transforme jamais la maison benchmark en règle générale.\n\n${orientationRule}\n\nPHOTOS, DANS L’ORDRE DU PDF\n${photoLines}\n\nFAITS UTILISATEUR\n- project_id: ${project?.project_id || 'non_persisté'}\n- nom du projet: ${project?.project_name || 'Ma maison'}\n- ville (CITY = CONTEXTUAL_PRIOR, jamais preuve architecturale): ${project?.city || 'non renseignée'}\n- largeur réelle de façade avant: ${Number.isFinite(width) && width > 0 ? `${width} m` : 'inconnue'}\n- largeur cible future de maquette: ${targetStuds} tenons (information de contexte seulement, sans effet sur le Survey)\n- notes: ${project?.general_notes || notes?.value.trim() || 'aucune'}\n\nRÈGLE VILLE\nCITY != ARCHITECTURAL_EVIDENCE. La ville peut aider à poser de meilleures questions mais ne permet jamais de décréter un matériau, un toit ou une géométrie contrairement aux photos.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-survey-result.json. Le fichier doit contenir DIRECTEMENT l’objet ArchitecturalSurvey v0.1 à la racine. La première clé doit être schema_version. INTERDIT: {\"ArchitecturalSurvey\":{...}}, {\"survey\":{...}}, physical_objects, Scene ou autre wrapper.\n\nAUDIT DE CONTRAT OBLIGATOIRE AVANT SORTIE\n- schema_version vaut exactement \"0.1\" ;\n- id et name sont présents et non vides ;\n- canonical_frame est présent ;\n- photos est non vide ;\n- pour une photo capture_role=facade_view : facade vaut front|rear|left|right et image_left_maps_to_facade_offset vaut low|high ;\n- pour une photo capture_role=targeted_detail : facade=null et image_left_maps_to_facade_offset=null ; conserve user_note lorsqu’il est fourni ;\n- ne fabrique jamais une façade pour une vue de dessous, dessus, terrasse, toiture ou autre détail local ;\n- observations et relations sont des tableaux ;\n- toute observation opening représente un seul objet physique et possède attributes.physical_object_count=1 ;\n- attributes.semantic_type, s’il est présent, vaut uniquement window, door, door_or_glazed_door, glazed_door_or_large_glazed_opening ou garage_door ; sinon OMETS semantic_type ; n’écris jamais semantic_type:\"opening\" ;\n- chaque relation contient id, kind, subject_id, object_id, certainty, statement et evidence ;\n- chaque relation référence deux IDs d’observations existantes ;\n- known_measurements transporte la largeur utilisateur seulement au format du contrat ;\n- JSON valide, sans commentaire ni texte avant/après.\n\nIMPORTANT — FORME AVANT CONTENU\nLe squelette JSON canonique ci-dessous est l’autorité structurelle la plus directe. Copie sa FORME, jamais ses faits d’exemple. Il interdit explicitement le wrapper ArchitecturalSurvey, physical_objects et les anciennes formes de photos/mesures observées lors du premier essai réel en conversation neutre.\n\n================ SQUELETTE JSON CANONIQUE — COPIER LA FORME, PAS LES FAITS ================\n${outputContract}\n\n================ TOPOLOGIE — RAISONNEMENT INTERMÉDIAIRE ================\n${topology}\n\n================ ARCHITECTURAL SURVEY — CONTRAT AUTORITATIF ================\n${survey}\n\nAUDIT FINAL IMMÉDIAT AVANT FICHIER\n- la racine commence par schema_version et ne contient aucun wrapper ;\n- aucune clé physical_objects n’existe nulle part ;\n- canonical_frame.x_direction = \"front_view_left_to_right\" ;\n- photos[] possède description + source ;\n- known_measurements[] utilise kind/value/units/source ;\n- chaque objet physique est une observation ;\n- notes est string ou null ;\n- JSON valide, aucun texte avant/après.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-survey-result.json.`;
}

function ascii(text) {
  return String(text).normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—→]/g, '-')
    .replace(/[^\x09\x0A\x0D\x20-\x7E]/g, '?');
}

function wrapText(ctx, text, maxWidth) {
  const out = [];
  for (const rawLine of ascii(text).split(/\r?\n/)) {
    if (!rawLine) {
      out.push('');
      continue;
    }
    const words = rawLine.split(/\s+/);
    let line = '';
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      if (ctx.measureText(candidate).width <= maxWidth) {
        line = candidate;
      } else {
        if (line) out.push(line);
        line = word;
      }
    }
    out.push(line);
  }
  return out;
}

function makeTextPages(text) {
  const probe = document.createElement('canvas').getContext('2d');
  if (!probe) throw new Error('Canvas de mesure indisponible.');
  probe.font = `${TEXT_SIZE}px sans-serif`;
  const lines = wrapText(probe, text, PAGE_W - MARGIN * 2);
  const perPage = Math.floor((PAGE_H - MARGIN * 2) / TEXT_LINE_HEIGHT);
  const pages = [];
  let pageNumber = 1;
  for (let offset = 0; offset < lines.length; offset += perPage) {
    pages.push({
      kind: 'text',
      lines: lines.slice(offset, offset + perPage),
      label: `page texte ${pageNumber}`,
    });
    pageNumber += 1;
  }
  return pages;
}

function newPageCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W;
  canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d', { alpha: false });
  if (!ctx) throw new Error('Canvas 2D indisponible sur cet appareil.');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);
  return { canvas, ctx };
}

function assertCanvasHealthy(canvas, label) {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error(`${label}: canvas inaccessible.`);
  const points = [[4, 4], [PAGE_W - 5, 4], [4, PAGE_H - 5], [PAGE_W - 5, PAGE_H - 5]];
  for (const [x, y] of points) {
    const pixel = ctx.getImageData(x, y, 1, 1).data;
    if (pixel[3] < 240 || pixel[0] < 220 || pixel[1] < 220 || pixel[2] < 220) {
      throw new Error(`${label}: page graphique invalide détectée avant export.`);
    }
  }
}

function canvasJpegBytes(canvas, label, quality = 0.86) {
  assertCanvasHealthy(canvas, label);
  const dataUrl = canvas.toDataURL('image/jpeg', quality);
  if (!dataUrl.startsWith('data:image/jpeg;base64,') || dataUrl.length < 2000) {
    throw new Error(`${label}: encodage JPEG invalide.`);
  }
  const binary = atob(dataUrl.split(',')[1]);
  if (binary.length < 1000) throw new Error(`${label}: page JPEG anormalement vide.`);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function releaseCanvas(canvas) {
  canvas.width = 1;
  canvas.height = 1;
}

function encodeCanvasPage(canvas, label) {
  try {
    return { kind: 'image', bytes: canvasJpegBytes(canvas, label), width: PAGE_W, height: PAGE_H, label };
  } finally {
    releaseCanvas(canvas);
  }
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`Image illisible: ${file.name}`));
    };
    image.src = url;
  });
}

async function makePhotoPage(record, index) {
  const image = await loadImage(record.file);
  if (!image.naturalWidth || !image.naturalHeight) throw new Error(`Photo ${index + 1}: dimensions invalides.`);
  const { canvas, ctx } = newPageCanvas();
  try {
    ctx.fillStyle = '#111';
    ctx.font = 'bold 23px sans-serif';
    ctx.fillText(`PHOTO ${index + 1} — ${ascii(record.photoId || 'UNPERSISTED')} — ${ascii(record.label)}`, MARGIN, 42);
    ctx.font = '16px sans-serif';
    ctx.fillText(ascii(record.file.name), MARGIN, 76);
    ctx.fillText(`PRIMARY_FACE=${record.primaryFace || 'NONE'} · capture_role=${record.captureRole} · orientation_authority=${record.orientationAuthority}`, MARGIN, 102);
    if (record.note) ctx.fillText(`note: ${ascii(record.note).slice(0, 100)}`, MARGIN, 128);
    const top = 164;
    const maxW = PAGE_W - MARGIN * 2;
    const maxH = PAGE_H - top - MARGIN;
    const scale = Math.min(maxW / image.naturalWidth, maxH / image.naturalHeight);
    const w = Math.max(1, image.naturalWidth * scale);
    const h = Math.max(1, image.naturalHeight * scale);
    ctx.drawImage(image, (PAGE_W - w) / 2, top + (maxH - h) / 2, w, h);
    return encodeCanvasPage(canvas, `photo ${index + 1}`);
  } finally {
    image.src = '';
    if (canvas.width !== 1 || canvas.height !== 1) releaseCanvas(canvas);
  }
}

function concat(parts) {
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function latinBytes(value) {
  const bytes = new Uint8Array(value.length);
  for (let i = 0; i < value.length; i += 1) bytes[i] = value.charCodeAt(i) & 0xff;
  return bytes;
}

function pdfString(value) {
  return ascii(value).replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

function textContent(lines) {
  const startY = PAGE_H - MARGIN - TEXT_SIZE;
  const body = lines.map((line, index) => {
    const move = index === 0 ? '' : `0 -${TEXT_LINE_HEIGHT} Td\n`;
    return `${move}(${pdfString(line)}) Tj\n`;
  }).join('');
  return `BT\n/F1 ${TEXT_SIZE} Tf\n${MARGIN} ${startY} Td\n${body}ET\n`;
}

function pdfFromPages(pages) {
  if (!pages.length) throw new Error('Aucune page à exporter.');
  const objects = [];
  const addObject = parts => {
    objects.push(parts);
    return objects.length;
  };
  const catalogId = addObject([]);
  const pagesId = addObject([]);
  const fontId = addObject([latinBytes('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')]);
  const pageIds = [];

  for (const page of pages) {
    if (page.kind === 'text') {
      const content = textContent(page.lines || []);
      const contentId = addObject([latinBytes(`<< /Length ${content.length} >>\nstream\n${content}endstream`)]);
      pageIds.push(addObject([latinBytes(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`)]));
      continue;
    }

    if (!(page.bytes instanceof Uint8Array) || page.bytes.length < 1000) {
      throw new Error(`${page.label || 'page'}: données JPEG absentes.`);
    }
    const imageId = addObject([
      latinBytes(`<< /Type /XObject /Subtype /Image /Width ${page.width} /Height ${page.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${page.bytes.length} >>\nstream\n`),
      page.bytes,
      latinBytes('\nendstream'),
    ]);
    const content = `q\n${PAGE_W} 0 0 ${PAGE_H} 0 0 cm\n/Im0 Do\nQ\n`;
    const contentId = addObject([latinBytes(`<< /Length ${content.length} >>\nstream\n${content}endstream`)]);
    pageIds.push(addObject([latinBytes(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /XObject << /Im0 ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`)]));
  }

  objects[catalogId - 1] = [latinBytes(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`)];
  objects[pagesId - 1] = [latinBytes(`<< /Type /Pages /Count ${pageIds.length} /Kids [${pageIds.map(id => `${id} 0 R`).join(' ')}] >>`)];

  const chunks = [latinBytes('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n')];
  const offsets = [0];
  let length = chunks[0].length;
  objects.forEach((parts, index) => {
    offsets.push(length);
    const head = latinBytes(`${index + 1} 0 obj\n`);
    const tail = latinBytes('\nendobj\n');
    chunks.push(head, ...parts, tail);
    length += head.length + parts.reduce((sum, part) => sum + part.length, 0) + tail.length;
  });
  const xrefOffset = length;
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i <= objects.length; i += 1) xref += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  xref += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  chunks.push(latinBytes(xref));
  return new Blob([concat(chunks)], { type: 'application/pdf' });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

button?.addEventListener('click', async event => {
  event.preventDefault();
  event.stopImmediatePropagation();
  const { records, project } = await photoRecords();
  if (!records.length) {
    if (status) status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · Ajoutez au moins une photo.`;
    return;
  }

  button.disabled = true;
  if (status) status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · Préparation du PDF hybride avec ${records.length} photo(s)…`;
  try {
    // fetch() here sees every already-installed v0.5-v0.9 prompt wrapper, so the
    // effective Survey prompt remains exactly the current audited prompt.
    const [topology, survey, outputContract] = await Promise.all([
      fetchText('./brickhouse-topology-prompt.txt'),
      fetchText('./brickhouse-survey-prompt.txt'),
      fetchText('./brickhouse-survey-output-contract.txt'),
    ]);
    const pages = makeTextPages(commandText(records, project, topology, survey, outputContract));
    const textPageCount = pages.length;
    for (let index = 0; index < records.length; index += 1) {
      if (status) status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · Encodage photo ${index + 1}/${records.length}…`;
      pages.push(await makePhotoPage(records[index], index));
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    const pdf = pdfFromPages(pages);
    if (pdf.size < 5000) throw new Error('PDF final anormalement petit.');
    downloadBlob(pdf, PACKAGE_FILENAME);
    if (status) status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · ${PACKAGE_FILENAME} prêt · ${textPageCount} page(s) de texte extractible + ${records.length} photo(s) · l’IA doit rendre brickhouse-survey-result.json.`;
  } catch (error) {
    if (status) status.textContent = `PDF NON téléchargé : ${error.message}`;
  } finally {
    button.disabled = false;
  }
}, { capture: true });
