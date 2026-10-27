import React, { useState } from 'react';
import FormField from '../../../shared/components/FormField.jsx';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import TransferEditor from './TransferEditor.jsx';
import TransferDecision from './TransferDecision.jsx';
import TransferDetail from './TransferDetail.jsx';
import TransferDocumentDialog from './TransferDocumentDialog.jsx';
import useTransferDocumentDownload from '../hooks/useTransferDocumentDownload.js';
import { dateTime, employeeName, money } from '../lib/payroll.js';
import { matchesPayroll, transferActions, transferLabels, transferStatuses } from '../lib/transfers.js';

/** @param {{ orders: Array, payrolls: Array, loading: boolean, error: string, payrollError: string, permissions: Object, onChanged: Function }} props */
export default function TransferOrders({ orders, payrolls, loading, error, payrollError, permissions, onChanged }) {
  const mutation = useApiMutation(onChanged);
  const [editor, setEditor] = useState(null);
  const [decision, setDecision] = useState(null);
  const [detailId, setDetailId] = useState(null);
  const [documentOrder, setDocumentOrder] = useState(null);
  const file = useTransferDocumentDownload();
  const [notice, setNotice] = useState('');
  const [filters, setFilters] = useState({ period: '', status: '' });
  const usablePermissions = { ...permissions, payrollRead: permissions.payrollRead && !payrollError };
  const open = (action, order = null) => {
    mutation.reset(); setNotice('');
    if (action === 'document') { setDocumentOrder(order); return; }
    if (action === 'download_document') { file.download(order); return; }
    if (action === 'create' || action === 'edit') setEditor({ order });
    else setDecision({ action, order });
  };
  const saved = () => { setEditor(null); setDecision(null); setNotice('Ordre de virement mis à jour.'); };
  const filtered = orders.filter((order) => (!filters.period || order.periode === filters.period) && (!filters.status || order.statut === filters.status));
  return <section className="content-card">
    <div className="card-heading"><h2>Ordres de virement</h2><div className="leave-request-actions">
      <button type="button" className="outline-button" onClick={onChanged} disabled={loading || mutation.saving}>Actualiser</button>
      {permissions.create && <button type="button" className="primary-button" onClick={() => open('create')} disabled={loading || mutation.saving || !usablePermissions.payrollRead}>Créer un ordre de virement</button>}
    </div></div>
    <p className="planning-notice">Cet écran suit les ordres enregistrés dans l’application. Aucun fichier de virement n’est transmis à une banque.</p>
    <p className="planning-notice">Préparez le document bancaire avec « Générer l’ordre PDF ». Les modifications et suppressions restent possibles au statut Généré, avant archivage du document et selon vos permissions.</p>
    {!permissions.create && <p className="planning-notice">La création nécessite la permission ordre_virement.create.</p>}
    {!permissions.payrollRead && permissions.create && <p className="message-box">La création depuis une paie nécessite aussi paie.read.</p>}
    {payrollError && <p className="message-box error" role="alert">Paies indisponibles : {payrollError}</p>}
    {notice && <p className="message-box" role="status">{notice}</p>}
    {file.error && <p className="message-box error" role="alert">{file.error}</p>}
    {file.busy && <p role="status">Téléchargement du document…</p>}
    <div className="payroll-filters form-grid">
      <FormField label="Période des ordres">{(a11y) => <input {...a11y} type="month" value={filters.period} onChange={(event) => setFilters((value) => ({ ...value, period: event.target.value }))} />}</FormField>
      <FormField label="Statut de l’ordre">{(a11y) => <select {...a11y} value={filters.status} onChange={(event) => setFilters((value) => ({ ...value, status: event.target.value }))}><option value="">Tous les statuts</option>{Object.entries(transferStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>}</FormField>
      <button type="button" className="outline-button" onClick={() => setFilters({ period: '', status: '' })}>Réinitialiser les filtres</button>
    </div>
    {loading ? <p className="leave-state" role="status">Chargement des ordres…</p> : error ? <p className="message-box error" role="alert">{error}</p>
      : <TransferList orders={filtered} payrolls={payrolls} permissions={usablePermissions} busy={mutation.saving || file.busy} onDetail={setDetailId} onAction={open} />}
    {documentOrder && <TransferDocumentDialog order={documentOrder} onClose={() => setDocumentOrder(null)} onChanged={onChanged} />}
    {editor && <TransferEditor order={editor.order} payrolls={payrolls} orders={orders} mutation={mutation} onClose={() => setEditor(null)} onSaved={saved} />}
    {decision && <TransferDecision {...decision} payrolls={payrolls} mutation={mutation} onClose={() => setDecision(null)} onSaved={saved} />}
    {detailId !== null && <TransferDetail orderId={detailId} onClose={() => setDetailId(null)} />}
  </section>;
}

export function TransferList({ orders, payrolls, permissions, busy, onDetail, onAction }) {
  if (!orders.length) return <p className="leave-state">Aucun ordre de virement ne correspond aux filtres.</p>;
  return <div className="leave-request-list">{orders.map((order) => {
    const payroll = payrolls.find((item) => String(item.ordre_virement) === String(order.id))
      || payrolls.find((item) => ['VALIDEE', 'PAYE'].includes(item.statut) && matchesPayroll(order, item));
    return <article key={order.id} className="leave-request-card payroll-card">
      <div className="leave-request-main"><span className="leave-status">{transferStatuses[order.statut] || order.statut}</span>
        <h3>{employeeName(order)} · {order.periode}</h3><p>Ordre #{order.id} · Matricule : {order.employe_matricule || 'Non renseigné'}</p>
        <p>Généré le {dateTime(order.date_generation)} · Traité le {dateTime(order.date_traitement)}</p>
        {order.statut === 'GENERE' && order.document_disponible && <p>Document archivé : instructions figées. Utilisez l’annulation pour préparer un remplacement.</p>}
        {order.statut !== 'GENERE' && <p>{order.statut === 'TRAITE'
          ? 'Ordre traité : modification et suppression indisponibles. L’historique est conservé.'
          : 'Ordre clôturé : modification et suppression indisponibles. Un nouvel ordre peut être créé si la paie est éligible.'}</p>}
        {order.statut === 'GENERE' && permissions.update && !permissions.payrollRead && <p>La modification nécessite aussi la consultation des paies.</p>}
        {payroll && <p>Net de la paie : {money(payroll.salaire_net, payroll.devise)} · {String(payroll.ordre_virement) === String(order.id) ? 'Paie payée et associée' : order.statut === 'TRAITE' ? 'Paie à associer' : order.statut === 'GENERE' ? 'En attente de traitement' : 'Ordre clôturé sans association'}</p>}
      </div><div className="leave-request-actions">
        <button type="button" className="outline-button" onClick={() => onDetail(order.id)} disabled={busy}>Voir le détail</button>
        {transferActions(order, permissions, payrolls).map((action) => <button type="button" key={action} disabled={busy} className={['delete', 'rejeter', 'annuler'].includes(action) ? 'danger-button' : 'outline-button'} onClick={() => onAction(action, order)}>{transferLabels[action]}</button>)}
      </div>
    </article>;
  })}</div>;
}
