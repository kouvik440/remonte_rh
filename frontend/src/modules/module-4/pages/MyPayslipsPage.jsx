import React, { useEffect, useState } from 'react';
import { navigate } from '../../../shared/lib/navigation.js';
import useApiResource from '../../../shared/hooks/useApiResource.js';
import { clearSession, downloadApiFile, formatApiError, getUser } from '../../../shared/lib/api.js';
import { money, payrollStatuses } from '../lib/payroll.js';
import PersonalPayslipViewer from '../components/PersonalPayslipViewer.jsx';

export default function MyPayslipsPage() {
  const [user] = useState(getUser);
  const valid = Boolean(localStorage.getItem('access_token')) && Array.isArray(user?.permissions);
  const data = useApiResource('/api/mes-bulletins/', valid, { refreshOnFocus: true });
  const [year, setYear] = useState('');
  const [viewing, setViewing] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (valid) return;
    clearSession(); navigate('/connexion?session=permissions', { replace: true });
  }, [valid]);
  async function download(payroll) {
    if (downloading !== null) return;
    setDownloading(payroll.id); setError('');
    try { await downloadApiFile(`/api/paiements/${payroll.id}/bulletin/`, `bulletin-paie-${payroll.periode}.pdf`); }
    catch (failure) {
      if (failure.status === 401) { clearSession(); navigate('/connexion?session=expired', { replace: true }); }
      else setError(formatApiError(failure.details || failure.message));
    } finally { setDownloading(null); }
  }
  const payrolls = data.report || [];
  const years = [...new Set(payrolls.map((item) => item.periode.slice(0, 4)))].sort().reverse();
  const filtered = payrolls.filter((item) => !year || item.periode.startsWith(`${year}-`));
  if (!valid) return null;
  return <>
    <section className="page-heading"><div><p className="eyebrow">MON ESPACE PERSONNEL</p><h1>Mes bulletins de paie</h1>
      <p className="page-description">Retrouvez vos fiches de paie validées, consultez-les et téléchargez leur PDF.</p></div></section>
    <section className="personal-payslips" aria-label="Mes fiches de paie" aria-busy={data.loading}>
      <div className="personal-payslip-actions">
        <label className="form-field">Année<select aria-label="Année" value={year} onChange={(event) => setYear(event.target.value)}>
          <option value="">Toutes les années</option>{years.map((item) => <option key={item} value={item}>{item}</option>)}
        </select></label>
        <button type="button" className="outline-button" disabled={data.loading} onClick={data.reload}>Actualiser mes bulletins</button>
      </div>
      {data.loading && <p role="status">Chargement de vos bulletins…</p>}
      {data.error && <p className="message-box error" role="alert">{data.error}</p>}
      {error && <p className="message-box error" role="alert">{error}</p>}
      {!data.loading && !data.error && (!filtered.length ? <p role="status">{year ? 'Aucun bulletin pour cette année.' : 'Aucun bulletin de paie validé pour le moment.'}</p>
        : <div className="personal-payslip-grid">{filtered.map((payroll) => <article className="personal-payslip-card" key={payroll.id}>
          <h2>Bulletin de {payroll.periode}</h2><p>{payroll.libelle} · {payrollStatuses[payroll.statut]}</p>
          <dl><div><dt>Salaire brut</dt><dd>{money(payroll.salaire_brut, payroll.devise)}</dd></div>
            <div><dt>Net à payer</dt><dd>{money(payroll.salaire_net, payroll.devise)}</dd></div></dl>
          {payroll.bulletin_disponible ? <div className="personal-payslip-actions">
            <button className="outline-button" type="button" onClick={() => setViewing(payroll)} aria-label={`Consulter mon bulletin de ${payroll.periode}`}>Consulter ma fiche</button>
            <button className="primary-button" type="button" disabled={downloading !== null} onClick={() => download(payroll)} aria-label={`Télécharger mon bulletin de ${payroll.periode}`}>{downloading === payroll.id ? 'Téléchargement…' : 'Télécharger le PDF'}</button>
          </div> : <p>Le PDF n’est pas encore disponible. Contactez le gestionnaire de paie.</p>}
        </article>)}</div>)}
    </section>
    {viewing && <PersonalPayslipViewer key={viewing.id} payroll={viewing} onClose={() => setViewing(null)} />}
  </>;
}
