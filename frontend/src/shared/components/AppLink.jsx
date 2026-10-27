import React from 'react';
import { navigate, routeKey } from '../lib/navigation.js';

/** A real link: modified clicks, downloads and external URLs keep browser behavior. */
export default function AppLink({ href, onClick, children, ...props }) {
  const follow = (event) => {
    onClick?.(event);
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
      || event.shiftKey || event.altKey || props.download !== undefined
      || (props.target && props.target !== '_self') || props.rel?.split(/\s+/).includes('external')) return;
    const url = new URL(href, window.location.href);
    if (url.origin !== window.location.origin || !routeKey(url.pathname) || href.startsWith('#')) return;
    event.preventDefault();
    navigate(url.href);
  };
  return <a {...props} href={href} onClick={follow}>{children}</a>;
}
