// A fake of the slice of the Things 3 scripting interface that things.js uses. For tests only.
// Models: lists, a Logbook, projects, areas, tags, property get (t.name()) and set (t.name = x), schedule, move.
// Does NOT model: headings, checklists, repeat rules. Whether Things clears the start date on move-to-Anytime is ASSUMED here.
function makeFake(seed, opts) {
  opts = opts || {};
  const items = (seed.items || []).map((x) => Object.assign({
    notes: '', tags: [], act: null, due: null, cre: new Date('2026-01-01T12:00:00'), comp: null,
    project: null, area: null, list: 'Anytime', status: 'open', heading: null,
  }, x));
  const projects = seed.projects || [];
  let seq = 0;
  const log = [];
  const pushes = [];   // every item pushed, with the list it was actually pushed into
  const byId = (id) => items.find((i) => i.id === id);
  const projName = (id) => { const p = projects.find((q) => q.id === id); return p ? p.name : null; };
  const throwIf = (col) => { if (opts.failColumn === col) throw new Error('column failed: ' + col); };
  const shortIf = (col, a) => (opts.shortColumn === col ? a.slice(1) : a);

  const collection = (rowsFn, listName) => {
    const col = (name, f) => () => { throwIf(name); return shortIf(name, rowsFn().map(f)); };
    return {
      id: col('id', (d) => d.id), name: col('name', (d) => d.name), notes: col('notes', (d) => d.notes),
      tagNames: col('tagNames', (d) => d.tags.join(', ')), activationDate: col('activationDate', (d) => d.act),
      dueDate: col('dueDate', (d) => d.due), creationDate: col('creationDate', (d) => d.cre),
      completionDate: col('completionDate', (d) => d.comp),
      project: { name: col('project.name', (d) => projName(d.project)), id: col('project.id', (d) => d.project) },
      area: { name: col('area.name', (d) => d.area) },
      push: (o) => { const p = o._props; items.push(Object.assign({ id: 'new-' + (++seq), notes: '', tags: [], act: null, due: null,
        cre: new Date(), comp: null, project: null, area: null, list: listName, status: 'open', heading: null },
        { name: p.name, notes: p.notes || '', tags: p.tagNames ? p.tagNames.split(', ') : [], due: p.dueDate || null })); log.push('push ' + p.name); pushes.push({ name: p.name, list: listName }); },
    };
  };
  const inList = (n) => items.filter((i) => i.status === 'open' && i.list === n);
  const logbook = () => items.filter((i) => i.status === 'completed').sort((a, b) => b.comp - a.comp);

  const wrap = (d) => new Proxy({}, {
    get(_, k) {
      if (k === '_d') return d;
      return () => {
        if (!d) throw new Error('not found');
        if (opts.beforeRead) opts.beforeRead(d, k);
        switch (k) {
          case 'name': return d.name;
          case 'notes': return d.notes;
          case 'tagNames': return d.tags.join(', ');
          case 'activationDate': return d.act;
          case 'dueDate': return d.due;
          case 'creationDate': return d.cre;
          case 'status': return d.status;
          case 'project': return d.project ? { name: () => projName(d.project), id: () => d.project } : null;
          case 'area': return d.area ? { name: () => d.area } : null;
          default: throw new Error('unmodelled property ' + String(k));
        }
      };
    },
    set(_, k, v) {
      if (!d) throw new Error('not found');
      log.push('set ' + k);
      switch (k) {
        case 'name': d.name = v; break;
        case 'notes': d.notes = opts.mangleNotes ? v.slice(1) : v; break;
        case 'tagNames': d.tags = v ? v.split(', ') : []; break;
        case 'dueDate': d.due = v; break;
        case 'project': d.project = v._id; break;
        case 'area': d.area = v._name; break;
        default: throw new Error('unmodelled setter ' + String(k));
      }
      return true;
    },
  });

  const T = {
    lists: { byName: (n) => ({ toDos: n === 'Logbook' ? collection(logbook, 'Logbook') : collection(() => inList(n), n) }) },
    toDos: { byId: (id) => wrap(byId(id)) },
    tags: { name: () => seed.tags || [] },
    areas: { name: () => seed.areas || [], byName: (n) => ({ _name: n }) },
    projects: {
      id: () => projects.map((p) => p.id), name: () => projects.map((p) => p.name), status: () => projects.map((p) => p.status || 'open'),
      area: { name: () => projects.map((p) => p.area || null) }, byId: (id) => ({ _id: id }),
    },
    ToDo: (props) => ({ _props: props }),
    schedule: (t, o) => { log.push('schedule'); if (opts.onSchedule) opts.onSchedule(t._d); t._d.act = o.for; },
    move: (t, o) => {
      log.push('move');
      const target = o.to;
      t._d.list = target.name;
      if (!opts.moveKeepsDate) t._d.act = null;
      if (opts.moveDropsProject) t._d.project = null;
    },
  };
  // list objects from byName need a name for T.move
  const origByName = T.lists.byName;
  T.lists.byName = (n) => Object.assign(origByName(n), { name: n });
  return { T, items, log, byId, pushes };
}
module.exports = { makeFake };
