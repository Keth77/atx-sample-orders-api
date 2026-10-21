'use strict';

// Logs newly inserted orders from the DynamoDB stream.
// Uses CommonJS and callback-era patterns typical of Node.js 18 code.

function summarize(record) {
  const image = (record.dynamodb && record.dynamodb.NewImage) || {};
  const items = (image.items && image.items.L) || [];
  return {
    orderId: image.orderId ? image.orderId.S : undefined,
    customerId: image.customerId ? image.customerId.S : undefined,
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
