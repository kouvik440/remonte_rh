import React, { useMemo, useState } from 'react';
import PlanningRoster from './PlanningRoster.jsx';
import { indexPlanningDays, groupPlanningPeople } from '../lib/planning.js';
import { dateKey, firstDayOfMonth, lastDayOfMonth } from '../lib/calendar.js';

/** @param {{ month: Date, setMonth: Function, events: Array, loading: boolean, error: string, onRetry: Function, canViewAll: boolean }} props */
export default function LeavePlanning({ month, setMonth, events, loading, error, onRetry, canViewAll }) {
  const monthStart = dateKey(firstDayOfMonth(month));
  const monthEnd = dateKey(lastDayOfMonth(month));
  const calendarDays = useMemo(() => {
    const start = firstDayOfMonth(month);
    const end = lastDayOfMonth(month);
    const offset = (start.getDay() + 6) % 7;
    const days = [];
    for (let i = 0; i < offset; i += 1) days.push(null);
    for (let day = 1; day <= end.getDate(); day += 1) days.push(new Date(month.getFullYear(), month.getMonth(), day));
    while (days.length % 7) days.push(null);
    return days;
  }, [month]);

  const [selectedDate, setSelectedDate] = useState(() => dateKey(new Date()));
  const [department, setDepartment] = useState('');
  const [search, setSearch] = useState('');
  const activeDate = selectedDate >= monthStart && selectedDate <= monthEnd ? selectedDate : monthStart;
  const departments = [...new Set(events.map((event) => event.departement_nom).filter(Boolean))].sort();
  const normalizedSearch = search.trim().toLocaleLowerCase('fr');
  const filteredEvents = useMemo(() => events.filter((event) =>
    (!department || event.departement_nom === department)
    && `${event.employe_prenom} ${event.employe_nom}`.toLocaleLowerCase('fr').includes(normalizedSearch),
  ), [events, department, normalizedSearch]);
  const eventsByDay = useMemo(() => indexPlanningDays(filteredEvents, monthStart, monthEnd), [filteredEvents, monthStart, monthEnd]);
  const selectedPeople = groupPlanningPeople(filteredEvents.filter((event) => event.date_debut <= activeDate && event.date_fin >= activeDate));

  const changeMonth = (offset) => {
    setMonth((value) => new Date(value.getFullYear(), value.getMonth() + offset, 1));
  };

  return (
    <section className="content-card">
      <div className="card-heading leave-calendar-heading">
        <div>
          <h2>Planning d’équipe</h2>
          <p>{canViewAll ? "Vue de tous les employés autorisés, tous rôles confondus." : "Vue de votre planning personnel."}</p>
        </div>
        <div className="month-controls">
          <button type="button" className="outline-button" onClick={() => changeMonth(-1)} aria-label="Mois précédent">←</button>
          <strong>{new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' }).format(month)}</strong>
          <button type="button" className="outline-button" onClick={() => changeMonth(1)} aria-label="Mois suivant">→</button>
        </div>
      </div>
      <p className="planning-notice">La présence prévue ne confirme pas un pointage réel.</p>
      {loading ? (
        <p className="leave-state" role="status" aria-live="polite">Chargement du planning…</p>
      ) : error ? (
        <div className="planning-error" role="alert">
          <p>Le planning n’a pas pu être chargé : {error}</p>
          <button type="button" className="outline-button" onClick={onRetry}>Réessayer</button>
        </div>
      ) : (
        <>
        <div className="planning-filters">
          <label className="form-field">Rechercher une personne
            <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
          <label className="form-field">Département
            <select value={department} onChange={(event) => setDepartment(event.target.value)}>
              <option value="">Tous les départements</option>
              {departments.map((name) => <option key={name} value={name}>{name}</option>)}
            </select>
          </label>
          <label className="form-field">Jour à consulter
            <input type="date" min={monthStart} max={monthEnd} value={activeDate} onChange={(event) => { if (event.target.value) setSelectedDate(event.target.value); }} />
          </label>
        </div>
        <div className="leave-calendar" aria-busy={loading}>
          <div className="calendar-weekdays">
            {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="calendar-grid">
            {calendarDays.map((day, index) => (
              <CalendarDay
                key={day ? dateKey(day) : `blank-${index}`}
                day={day}
                events={day ? eventsByDay[dateKey(day)] || [] : []}
                selected={Boolean(day && dateKey(day) === activeDate)}
                onSelect={() => day && setSelectedDate(dateKey(day))}
              />
            ))}
          </div>
        </div>
        <PlanningRoster people={selectedPeople} date={activeDate} />
        </>
      )}
    </section>
  );
}

/** @param {{ day: Date | null, events: Array, selected: boolean, onSelect: Function }} props */
function CalendarDay({ day, events, selected, onSelect }) {
  if (!day) return <div className="calendar-day calendar-day-empty" />;
  const people = groupPlanningPeople(events);
  const absentCount = people.filter((person) => person.absences.length > 0).length;
  return (
    <button type="button" className={`calendar-day planning-day-button ${selected ? 'planning-day-selected' : ''}`}
      aria-pressed={selected} onClick={onSelect}
      aria-label={`${day.toLocaleDateString('fr-FR')} : ${people.length - absentCount} présents prévus, ${absentCount} absents`}>
      <strong>{day.getDate()}</strong>
      {people.length > 0 ? <span className="calendar-events">
        <span className="calendar-event presence-event">{people.length - absentCount} prévu(s)</span>
        <span className="calendar-event absence-event">{absentCount} absent(s)</span>
      </span> : <span className="planning-no-event">Aucun événement</span>}
    </button>
  );
}
