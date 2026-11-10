import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateLegoDesignIntent, createLegoVisualBrief, reviewLegoVisualProposal } from '../frontend/lego-design-brief-v1.js';
const intent = JSON.parse(readFileSync(new URL('../frontend/data/boldungo-lego-design-intent-v1.json', import.meta.url), 'utf8'));
assert.equal(validateLegoDesignIntent(intent), true);
const brief = createLegoVisualBrief(intent);
assert.ok(brief.non_negotiable.length >= 6);
assert.ok(brief.distinguishing_details.some(f => f.id === 'zinc-seams' && f.inferred_not_observed));
assert.ok(brief.non_negotiable.some(f => f.id === 'rose-window-surrounds'));
assert.equal(brief.is_buildability_certified, false);
assert.equal(brief.required_contacts.length, 5);
const fullyCompliant = {
  rendered_feature_ids: intent.features.map(f => f.id),
  actual_contacts: intent.contacts.map(c => ({a:c.a,b:c.b,relation:c.relation})),
  present_visual_defects: [],
  claims_observed_feature_ids: []
};
assert.equal(reviewLegoVisualProposal(intent, fullyCompliant).visual_ready, true);
assert.equal(reviewLegoVisualProposal(intent, {...fullyCompliant, actual_contacts: []}).visual_ready, false);
assert.equal(reviewLegoVisualProposal(intent, {...fullyCompliant, present_visual_defects:['roof_as_visible_steps']}).visual_ready, false);
assert.equal(reviewLegoVisualProposal(intent, {...fullyCompliant, rendered_feature_ids: fullyCompliant.rendered_feature_ids.filter(id=>id!=='stair-l')}).visual_ready,false);
assert.equal(reviewLegoVisualProposal(intent, {...fullyCompliant, claims_observed_feature_ids:['zinc-seams']}).visual_ready,false);
assert.throws(() => validateLegoDesignIntent({...intent,features:[...intent.features,{...intent.features[0]}]}), /dupliqué/);
assert.throws(() => validateLegoDesignIntent({...intent,features:intent.features.map(f=>f.id==='zinc-seams'?{...f,inference_reason:''}:f)}), /justification/);
console.log('PASS: brief reconnaissable, contacts, zinc et détails inférés, blocage toiture en escalier');
