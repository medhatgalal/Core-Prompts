import test from 'node:test';
import assert from 'node:assert/strict';
import { overlaps } from './sut.mjs';
test('ordinary overlap', () => assert.equal(overlaps([0, 3], [2, 4]), true));
