import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const pageSource = readFileSync(new URL('./page.tsx', import.meta.url), 'utf8');
const apiSource = readFileSync(new URL('../../services/api.ts', import.meta.url), 'utf8');

test('analytics dashboard renders daily commercial activity from the API contract', () => {
  assert.match(apiSource, /actividad_diaria:\s*Array</);
  assert.match(pageSource, /Actividad comercial por día/);
  assert.match(pageSource, /report\.actividad_diaria\.map/);
});
