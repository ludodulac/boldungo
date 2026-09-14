import assert from 'node:assert/strict';
import { composedOpeningVisualPlan } from '../../frontend/scene-opening-visual.js';

const acquired = {
  surround_color: 'beige',
  surround_relief: 'projecting',
  glazing_plane: 'recessed',
  leaf_count: 2,
  mullion_count: 1,
  glazing: 'dark_reflective',
  frame_color: 'dark_gray_brown',
  frame_material: 'painted_or_dark_joinery',
  pane_count: null,
  pane_layout: null,
};

const plan = composedOpeningVisualPlan(acquired);
assert.ok(plan, 'the acquired composition must be renderable');
assert.equal(plan.mullionCount, 1, 'exactly the acquired central division is rendered');
assert.equal(plan.surroundRelief, 'projecting');
assert.equal(plan.glazingPlane, 'recessed');

assert.equal(composedOpeningVisualPlan(null), null, 'no opening_visual keeps legacy generic rendering');
assert.equal(composedOpeningVisualPlan({ pane_count: 2 }), null, 'pane_count alone must not invent this composition');
assert.equal(composedOpeningVisualPlan({ ...acquired, mullion_count: null }), null, 'missing mullion truth must not invent a divider');
assert.equal(composedOpeningVisualPlan({ ...acquired, leaf_count: null }), null, 'missing leaf truth must not infer the proven two-leaf composition');
assert.equal(composedOpeningVisualPlan({ ...acquired, mullion_count: 2 }), null, 'unsupported mullion layouts are not guessed');
assert.equal(composedOpeningVisualPlan({ ...acquired, surround_relief: null }), null, 'missing relief truth must not invent projection');
assert.equal(composedOpeningVisualPlan({ ...acquired, glazing_plane: null }), null, 'missing glazing-plane truth must not invent recession');
assert.equal(composedOpeningVisualPlan({ ...acquired, frame_material: null }), null, 'missing joinery material truth must not invent frame treatment');
assert.equal(composedOpeningVisualPlan({ ...acquired, surround_color: 'unknown-color' }), null, 'unsupported visual vocabulary falls back instead of inventing a color');

console.log('scene opening visual plan: ok');
