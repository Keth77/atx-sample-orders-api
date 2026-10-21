'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { handler, summarize } = require('../../src/stream_notify/index.js');

test('summarize reads the new image', () => {
  const record = {
    dynamodb: { NewImage: { orderId: { S: 'o-1' }, customerId: { S: 'c-1' }, items: { L: [{}, {}] } } },
  };
  assert.deepStrictEqual(summarize(record), { orderId: 'o-1', customerId: 'c-1', itemCount: 2 });
});

test('handler only processes INSERT events', async () => {
  const event = {
    Records: [
      { eventName: 'INSERT', dynamodb: { NewImage: { orderId: { S: 'o-1' } } } },
      { eventName: 'MODIFY', dynamodb: { NewImage: { orderId: { S: 'o-2' } } } },
    ],
  };
  assert.deepStrictEqual(await handler(event), { processed: 1 });
});
