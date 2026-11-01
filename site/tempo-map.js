/* Pure notated-position -> performed-quarter mapping. No DOM or edition data.
 * measures is document-order ids; measureQ holds first-pass starts; events are
 * time-ordered {qstamp, measure}. A repeat can re-enter anywhere in a section.
 */
export function mapTempoSections(rows, measures, events, measureQ) {
  const order = new Map(measures.map((id, i) => [id, i]));
  const seen = new Set();
  const points = [];
  let previous = null;
  function emit(q, index) {
    if (index < 0 || points.at(-1)?.index === index) return;
    points.push({ q, index });
  }
  for (const event of events) {
    const id = event.measure;
    if (!order.has(id) || id === previous) continue;
    previous = id;
    const start = seen.has(id) ? event.qstamp : measureQ.get(id) ?? event.qstamp;
    seen.add(id);
    const n = order.get(id);
    let active = -1;
    rows.forEach((row, i) => {
      const r = order.get(row.measure);
      if (r < n || (r === n && row.offset === 0)) active = i;
    });
    emit(start, active);
    rows.forEach((row, i) => {
      if (row.measure === id && row.offset > 0) emit(start + row.offset, i);
    });
  }
  return points;
}
