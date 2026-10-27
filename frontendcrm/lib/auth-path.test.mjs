import test from 'node:test';
import assert from 'node:assert/strict';

import { isAuthPath } from './auth-path.mjs';

test('recognizes exported authentication routes with trailing slashes', () => {
  assert.equal(isAuthPath('/login/'), true);
  assert.equal(isAuthPath('/register/'), true);
});

test('does not treat protected routes as authentication routes', () => {
  assert.equal(isAuthPath('/'), false);
  assert.equal(isAuthPath('/dashboard/'), false);
});
