import React, { useState } from 'react';
import useApiMutation from '../../../shared/hooks/useApiMutation.js';
import PayrollDialog from './PayrollDialog.jsx';
import PayrollRuleEditor from './PayrollRuleEditor.jsx';
import { rateFields, ruleForm, rulesPath } from '../lib/rules.js';

/** @param {{ rules: Array, loading: boolean, error: string, permissions: Object, onChanged: Function }} props */
export default function PayrollRuleManager({ rules, loading, error, permissions, onChanged }) {
  const mutation = useApiMutation(onChanged);
  const [editor, setEditor] = useState(null);
  const [decision, setDecision] = useState(null);
  const [notice, setNotice] = useState('');
  const openEditor = (rule) => { mutation.reset(); setNotice(''); setEditor({ rule }); };
  const decide = (action, rule) => { mutation.reset(); setNotice(''); setDecision({ action, rule }); };
  const confirm = async () => {
    const deleting = decision.action === 'delete';
    if (await mutation.submit(`${rulesPath}${decision.rule.id}/${deleting ? '' : 'valider/'}`, deleting ? 'DELETE' : 'POST', deleting ? undefined : {})) {
      setNotice(deleting ? 'Profil supprimé.' : 'Profil validé. Il peut maintenant être utilisé pour le calcul.'); setDecision(null);
    }
  };
  return <section className="content-card">
    <div className="card-heading"><h2>Règles de paie</h2><div className="leave-request-actions">
      <button type="button" className="outline-button" disabled={loading || mutation.saving} onClick={onChanged}>Actualiser</button>
      {permissions.create && <button type="button" className="primary-button" disabled={loading || mutation.saving} onClick={() => openEditor(null)}>Nouvelles règles</button>}
    </div></div>
    {notice && <p className="message-box" role="status">{notice}</p>}
    {loading ? <p className="leave-state" role="status">Chargement des règles…</p> : error ? <p className="message-box error" role="alert">{error}</p>
      : !rules.length ? <p className="leave-state">Aucun profil enregistré. Créez vos règles puis validez-les avant de calculer une paie.</p>
        : <div className="leave-request-list">{rules.map((rule) => <article className="leave-request-card payroll-rule-card" key={rule.id}>
          <div className="leave-request-main"><h3>{rule.nom}</h3><p>{rule.date_debut} → {rule.date_fin || 'Sans date de fin'} · {rule.actif ? 'Actif' : 'Inactif'} · {rule.valide ? 'Validé' : 'À valider'}</p><p>Référence : {rule.source_reference || 'À renseigner'}</p>
            <details><summary>Consulter les paramètres</summary><RuleInformation rule={rule} /></details>
          </div><div className="leave-request-actions">
            {permissions.create && <button type="button" className="outline-button" onClick={() => openEditor({ ...rule, id: undefined, code: '', valide: false })}>Créer une nouvelle version</button>}
            {!rule.valide && permissions.update && <>
              <button type="button" className="outline-button" onClick={() => openEditor(rule)}>Modifier</button>
              <button type="button" className="outline-button" onClick={() => decide('validate', rule)}>Valider les règles</button>
            </>}
            {!rule.valide && permissions.delete && <button type="button" className="danger-button" onClick={() => decide('delete', rule)}>Supprimer</button>}
          </div>
        </article>)}</div>}
    {editor && <PayrollRuleEditor rule={editor.rule} mutation={mutation} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); setNotice('Règles enregistrées. Le profil doit être validé avant calcul.'); }} />}
    {decision && <PayrollDialog title={decision.action === 'delete' ? 'Supprimer le profil' : 'Valider les règles'} busy={mutation.saving} onClose={() => setDecision(null)}>
      <p>{decision.rule.nom}</p><p>{decision.action === 'delete' ? 'Le profil non validé sera supprimé définitivement.' : 'Confirmez que les paramètres et la référence ont été vérifiés. Le profil sera figé après validation.'}</p>
      {mutation.message && <p className="message-box error" role="alert">{mutation.message}</p>}
      <div className="form-footer"><button type="button" className="outline-button" onClick={() => setDecision(null)} disabled={mutation.saving} autoFocus>Fermer</button><button type="button" className={decision.action === 'delete' ? 'danger-button' : 'primary-button'} onClick={confirm} disabled={mutation.saving}>Confirmer</button></div>
    </PayrollDialog>}
  </section>;
}

function RuleInformation({ rule }) {
  const form = ruleForm(rule);
  return <dl className="leave-detail-fields payroll-detail-grid">
    <div><dt>Code</dt><dd>{rule.code}</dd></div><div><dt>Heures mensuelles</dt><dd>{rule.heures_mensuelles}</dd></div>
    <div><dt>Plafond CNSS (XOF)</dt><dd>{rule.plafond_cnss}</dd></div><div><dt>Décimales</dt><dd>{rule.decimales_montant}</dd></div>
    {rateFields.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{form[key]}</dd></div>)}
    <div><dt>Tranches IUTS</dt><dd>{form.tranches_iuts.map((row, index) => <p key={index}>{row.minimum} → {row.maximum || 'Sans plafond'} XOF : {row.taux} %</p>)}</dd></div>
    <div><dt>Réductions familiales</dt><dd>{form.reductions_iuts_charges.length ? form.reductions_iuts_charges.map((row) => <p key={row.charges}>{row.charges} charge(s) : {row.taux} %</p>) : 'Aucune'}</dd></div>
  </dl>;
}
