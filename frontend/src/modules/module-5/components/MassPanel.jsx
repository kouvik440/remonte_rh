import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../shared/components/ui/card.jsx';

/** @param {{ title: string, description?: string, actions?: React.ReactNode, children: React.ReactNode }} props */
export default function MassPanel({ title, description, actions, children }) {
  return <Card className="mass-panel">
    <CardHeader className="mass-panel-header">
      <div><CardTitle><h2>{title}</h2></CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </div>
      {actions}
    </CardHeader>
    <CardContent className="mass-panel-content">{children}</CardContent>
  </Card>;
}
