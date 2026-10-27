import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../shared/components/ui/card.jsx';

export default function TgmPanel({ title, description, children }) {
  return <Card className="tgm-panel">
    <CardHeader><CardTitle><h2>{title}</h2></CardTitle>
      {description && <CardDescription>{description}</CardDescription>}
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>;
}
