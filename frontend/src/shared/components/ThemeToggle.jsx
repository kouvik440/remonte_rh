import React, { useSyncExternalStore } from 'react';
import { Moon, Sun } from 'lucide-react';
import { getTheme, setTheme, subscribeTheme } from '../lib/theme.js';

/** @param {{ compact?: boolean }} props */
export default function ThemeToggle({ compact = false }) {
  const theme = useSyncExternalStore(subscribeTheme, getTheme, getTheme);
  const dark = theme === 'dark';
  const Icon = dark ? Moon : Sun;

  return <button type="button" role="switch" aria-checked={dark} aria-label="Mode nuit"
    className={`theme-toggle${compact ? ' theme-toggle-compact' : ''}`}
    title={dark ? 'Passer en mode clair' : 'Passer en mode nuit'}
    onClick={() => setTheme(dark ? 'light' : 'dark')}>
    <Icon size={18} strokeWidth={1.6} aria-hidden="true" />
    <span>{dark ? 'Mode nuit' : 'Mode clair'}</span>
    {!compact && <span className="theme-toggle-track" aria-hidden="true"><span /></span>}
  </button>;
}
