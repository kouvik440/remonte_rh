import React from 'react';

export default function ResourceState({ data, label, children }) {
  if (data.loading) return <p className="leave-state" role="status">Chargement {label}…</p>;
  if (data.error) return <div className="message-box error" role="alert">{data.error} <button className="outline-button" type="button" onClick={data.reload}>Réessayer</button></div>;
  return data.report !== null ? children(data.report) : null;
}
