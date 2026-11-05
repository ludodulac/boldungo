// Petit prototype autonome : le contrôle de l'identité visuelle précède la construction LEGO.
// Aucune image n'est analysée ici ; ce module exploite uniquement un brief préalablement établi.
const IMPORTANCE = new Set(['signature', 'character', 'optional']);
const STATUS = new Set(['owner_confirmed', 'photo_observed', 'material_inferred']);
const CONTACT = new Set(['touch_no_gap', 'touch_with_height_step']);
const ensure = (check, message) => { if (!check) throw new Error(message); };
const sortedPair = (a,b) => [a,b].sort().join(' :: ');

export function validateLegoDesignIntent(intent) {
  ensure(intent && intent.schema_version === 'boldungo.lego-design-intent.v1', 'schema_version incorrecte');
  ensure(Array.isArray(intent.features) && intent.features.length > 0, 'features requises');
  ensure(Array.isArray(intent.contacts), 'contacts requis');
  const knownIds = new Set();
  for (const feature of intent.features) {
    ensure(feature && typeof feature.id === 'string' && feature.id, 'feature id requis');
    ensure(!knownIds.has(feature.id), 'feature id dupliqué : ' + feature.id);
    knownIds.add(feature.id);
    ensure(IMPORTANCE.has(feature.importance), 'importance invalide : ' + feature.id);
    ensure(STATUS.has(feature.status), 'preuve invalide : ' + feature.id);
    ensure(typeof feature.treatment === 'string' && feature.treatment.trim(), 'traitement manquant : ' + feature.id);
    if (feature.status === 'material_inferred') {
      ensure(typeof feature.inference_reason === 'string' && feature.inference_reason.trim(), 'justification de détail inféré manquante : ' + feature.id);
    } else {
      ensure(Array.isArray(feature.photo_examples) || feature.status === 'owner_confirmed', 'photo de référence manquante : ' + feature.id);
    }
  }
  const pairs = new Set();
  for (const c of intent.contacts) {
    ensure(typeof c.a === 'string' && typeof c.b === 'string' && c.a !== c.b, 'contact invalide');
    ensure(CONTACT.has(c.relation), 'type de contact invalide');
    ensure(c.status === 'owner_confirmed' || c.status === 'photo_observed', 'source de contact invalide');
    const pair = sortedPair(c.a,c.b);
    ensure(!pairs.has(pair), 'contact dupliqué ' + pair);
    pairs.add(pair);
  }
  ensure(Array.isArray(intent.visual_prohibitions), 'interdits visuels requis');
  return true;
}

export function createLegoVisualBrief(intent) {
  validateLegoDesignIntent(intent);
  const features = intent.features.map(f => ({
    id: f.id,
    label: f.label,
    importance: f.importance,
    source: f.status,
    lego_intent: f.treatment,
    inferred_not_observed: f.status === 'material_inferred'
  }));
  return {
    goal: intent.goal,
    priorities: [...intent.general_rules.priority_order],
    non_negotiable: features.filter(f => f.importance === 'signature'),
    distinguishing_details: features.filter(f => f.importance === 'character'),
    optional: features.filter(f => f.importance === 'optional'),
    inferred_details: features.filter(f => f.inferred_not_observed),
    required_contacts: intent.contacts.map(c => ({...c})),
    forbidden_looks: [...intent.visual_prohibitions],
    metric_anchors: {...intent.metric_anchors},
    is_buildability_certified: false
  };
}

// Passage obligatoire de validation du résultat d'un designer IA ou humain.
// proposal = { rendered_feature_ids: [...], actual_contacts: [{a,b,relation}],
//              present_visual_defects: [...], claims_observed_feature_ids: [...] }
// Si une vérification n'a pas été effectuée, elle n'est pas silencieusement déclarée réussie.
export function reviewLegoVisualProposal(intent, proposal) {
  validateLegoDesignIntent(intent);
  ensure(proposal && Array.isArray(proposal.rendered_feature_ids), 'proposition : rendered_feature_ids manquant');
  ensure(Array.isArray(proposal.actual_contacts), 'proposition : actual_contacts manquant');
  ensure(Array.isArray(proposal.present_visual_defects), 'proposition : present_visual_defects manquant');
  const present = new Set(proposal.rendered_feature_ids);
  const blocking = [];
  const warnings = [];
  for (const feature of intent.features) {
    if (!present.has(feature.id)) {
      (feature.importance === 'signature' ? blocking : warnings).push('Détail absent : ' + feature.id);
    }
  }
  const actual = new Map(proposal.actual_contacts.map(c => [sortedPair(c.a,c.b),c.relation]));
  for (const required of intent.contacts) {
    const found = actual.get(sortedPair(required.a,required.b));
    if (!found || found !== required.relation) blocking.push('Contact non vérifié/conforme : ' + required.a + ' ↔ ' + required.b + ' (' + required.relation + ')');
  }
  for (const defect of proposal.present_visual_defects) {
    if (intent.visual_prohibitions.includes(defect)) blocking.push('Aspect interdit : ' + defect);
  }
  const inferred = new Set(intent.features.filter(f => f.status === 'material_inferred').map(f => f.id));
  for (const id of proposal.claims_observed_feature_ids || []) {
    if (inferred.has(id)) blocking.push('Détail seulement inféré présenté comme observé : ' + id);
  }
  return {visual_ready: blocking.length === 0, blocking, warnings, structural_buildability_tested: false};
}
