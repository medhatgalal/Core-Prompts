// PUBLIC AUTHOR ANSWER; no model was asked to generate these tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import { overlaps } from './sut.mjs';
test('touching endpoints are disjoint', () => assert.equal(overlaps([0, 2], [2, 4]), false));
test('empty interval inside another is disjoint', () => assert.equal(overlaps([2, 2], [0, 4]), false));
test('reversed bounds are rejected', () => assert.throws(() => overlaps([2, 1], [0, 4]), RangeError));
test('ordinary overlap is symmetric', () => assert.equal(overlaps([2, 4], [0, 3]), true));
