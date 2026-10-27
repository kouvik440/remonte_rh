import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../shared/components/ui/card.jsx';

export default function TimesheetPanel({ title, description, actions, children }) {
  return <Card className="timesheet-panel">
    <CardHeader className="timesheet-panel-header"><div><CardTitle><h2>{title}</h2></CardTitle>
      {description && <CardDescription>{description}</CardDescription>}</div>{actions}
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>;
}
