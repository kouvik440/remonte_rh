import React from 'react';
import { createRoot } from 'react-dom/client';
import AppRouter from './AppRouter.jsx';
import { applyTheme, readTheme } from '../shared/lib/theme.js';
import '../shared/styles/styles.css';
import '../shared/styles/shadcn.css';
import '../shared/styles/themes.css';

applyTheme(readTheme());

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>,
);
