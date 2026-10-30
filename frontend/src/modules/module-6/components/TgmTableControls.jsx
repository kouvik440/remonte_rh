import React from 'react';

export default function TgmTableControls({ query, setQuery, sort, setSort, options, page, setPage, count }) {
  const pages = Math.max(1, Math.ceil(count / 10));
  return <div className="form-grid tgm-filters" style={{ marginBottom: 16 }}>
    <label className="form-field">Rechercher<input type="search" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></label>
    <label className="form-field">Trier par<select value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}>
      {options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
    </select></label>
    <div aria-label="Pagination" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
      <button className="outline-button" type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>Précédent</button>
      <span role="status">{count} résultat(s) · {Math.min(page, pages)} / {pages}</span>
      <button className="outline-button" type="button" disabled={page >= pages} onClick={() => setPage(page + 1)}>Suivant</button>
    </div>
  </div>;
}
