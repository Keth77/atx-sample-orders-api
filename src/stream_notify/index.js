'use strict';

// Logs newly inserted orders from the DynamoDB stream.
// Uses CommonJS, with modern optional chaining supported by Node.js 24.

function summarize(record) {
  const image = record.dynamodb?.NewImage ?? {};
  const items = image.items?.L ?? [];
  return {
    orderId: image.orderId?.S,
    customerId: image.customerId?.S,
    itemCount: items.length,
  };
}

exports.summarize = summarize;

exports.handler = async (event) => {
  const inserts = (event.Records || []).filter((r) => r.eventName === 'INSERT');
  const summaries = inserts.map(summarize);
  summaries.forEach((s) => console.log(JSON.stringify({ msg: 'order created', ...s })));
  return { processed: summaries.length };
};
