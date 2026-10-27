import React, { useRef, useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import PayrollDialog from './PayrollDialog.jsx';
import useTransferDocumentContext from '../hooks/useTransferDocumentContext.js';
import useTransferDocumentDownload from '../hooks/useTransferDocumentDownload.js';
import { money } from '../lib/payroll.js';
import { transfersPath } from '../lib/transfers.js';

const fields = [
  ['donneur_nom', 'Entreprise / titulaire du compte', 200], ['donneur_adresse', 'Adresse du donneur d’ordre', 500],
  ['donneur_telephone', 'Téléphone (facultatif)', 30, false], ['banque', 'Banque à débiter', 100],
  ['agence', 'Agence (facultative)', 100, false], ['compte_debit', 'RIB complet du compte à débiter (BF, 24 caractères)', 64],
  ['lieu', 'Lieu de signature', 100], ['signataire', 'Nom du signataire habilité', 150],
  ['fonction_signataire', 'Fonction du signataire (facultative)', 100, false], ['motif', 'Motif du virement', 250],
];

function blankForm(order) {
  const today = new Date();
  const date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  return { ...Object.fromEntries(fields.map(([key]) => [key, ''])), coordonnees_bancaires: '',
    date_execution: date, canal: 'BANQUE', motif: `Salaire du mois ${order.periode}` };
}

/** @param {{ order: Object, onClose: Function, onChanged: Function }} props */
export default function TransferDocumentDialog({ order, onClose, onChanged }) {
  const state = useTransferDocumentContext(order.id);
  const mutation = useApiMutation(onChanged);
  const file = useTransferDocumentDownload();
  const [form, setForm] = useState(() => blankForm(order));
  const [created, setCreated] = useState(false);
  const lock = useRef(false);
  const busy = mutation.saving || file.busy;
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    try {
      if (await mutation.submit(`${transfersPath}${order.id}/document/`, 'POST', { ...form, coordonnees_bancaires: Number(form.coordonnees_bancaires) })) {
        setCreated(true);
        await file.download(order);
      }
    } finally { lock.current = false; }
  };
  return <PayrollDialog title="Générer l’ordre de virement PDF" busy={busy} onClose={onClose}>
    {state.loading && <p role="status">Chargement de la paie et des comptes bénéficiaires…</p>}
    {state.error && <div className="message-box error" role="alert"><p>{state.error}</p><button type="button" className="outline-button" onClick={state.retry}>Réessayer</button></div>}
    {created ? <p role="status">Le document est généré et archivé. Imprimez-le pour signature et remise à la banque.</p>
      : state.context && <form onSubmit={submit}>
        <p>Bénéficiaire : {state.context.beneficiaire} · Net validé : {money(state.context.montant, 'XOF')}. Ce montant est repris de la paie.</p>
        <TransferDocumentFields form={form} change={change} context={state.context} mutation={mutation} busy={busy} />
        <p>Le document sera figé après génération. Pour modifier ensuite les instructions, annulez cet ordre et préparez un remplacement.</p>
        {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
        <div className="form-footer"><button type="submit" className="primary-button" disabled={busy || !state.context.comptes.some((account) => account.rib_valide)}>{busy ? 'Génération…' : 'Générer et télécharger le PDF'}</button></div>
      </form>}
    {file.error && <p className="message-box error" role="alert">{file.error}</p>}
    <div className="form-footer">
      {created && <button type="button" className="primary-button" disabled={busy} onClick={() => file.download(order)}>Télécharger l’ordre PDF</button>}
      <button type="button" className="outline-button" disabled={busy} onClick={onClose}>Fermer</button>
    </div>
  </PayrollDialog>;
}

export function TransferDocumentFields({ form, change, context, mutation, busy }) {
  return <fieldset className="leave-form-grid" disabled={busy}>
    <FormField label="Compte bancaire du bénéficiaire" error={mutation.errors.coordonnees_bancaires}>{(a11y) => <select {...a11y} value={form.coordonnees_bancaires} onChange={change('coordonnees_bancaires')} required>
      <option value="">Choisir un compte du salarié</option>{context.comptes.map((account) => <option key={account.id} value={account.id} disabled={!account.rib_valide}>{account.banque} · {account.compte_masque}{account.rib_valide ? '' : ' · RIB à compléter'}</option>)}
    </select>}</FormField>
    {!context.comptes.some((account) => account.rib_valide) && <p className="leave-wide message-box">Ajoutez un RIB UEMOA complet de 24 caractères dans les coordonnées bancaires du salarié avant de générer le document.</p>}
    {fields.map(([key, label, maxLength, required = true]) => <FormField key={key} label={label} error={mutation.errors[key]}>{(a11y) => <input {...a11y} value={form[key]} onChange={change(key)} maxLength={maxLength} required={required} autoComplete="off" spellCheck={key !== 'compte_debit'} />}</FormField>)}
    <FormField label="Date d’exécution demandée" error={mutation.errors.date_execution}>{(a11y) => <input {...a11y} type="date" value={form.date_execution} onChange={change('date_execution')} required />}</FormField>
    <FormField label="Mode de virement demandé" error={mutation.errors.canal}>{(a11y) => <select {...a11y} value={form.canal} onChange={change('canal')}>
      <option value="BANQUE">Selon les modalités de la banque</option><option value="INTERNE">Virement interne</option><option value="SICA">SICA</option><option value="RTGS">RTGS</option>
    </select>}</FormField>
  </fieldset>;
}
