import { describe, expect, it } from 'vitest';

import { parseSseChunk } from './chat';


describe('parseSseChunk', () => {
  it('parses a valid stream event', () => {
    const events = parseSseChunk(
      'event: message\ndata: {"type":"token","messageId":"m1","delta":"hello"}',
    );

    expect(events).toEqual([
      { type: 'token', messageId: 'm1', delta: 'hello' },
    ]);
  });

  it('ignores malformed or incomplete events', () => {
    expect(parseSseChunk('event: message')).toEqual([]);
    expect(parseSseChunk('data: not-json')).toEqual([]);
  });
});
