import React from 'react';

/** @param {{ record: Object }} props */
export default function RecordSummary({ record }) {
  return <>
    <h3>{record.banque}</h3>
    <p>{record.employe_prenom} {record.employe_nom}</p>
    <p>RIB : •••• {record.iban.slice(-4)}</p>
    <p>Dernière modification : {new Date(record.date_modification).toLocaleDateString('fr-FR')}</p>
  </>;
}
