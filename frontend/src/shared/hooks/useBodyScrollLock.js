import { useEffect } from 'react';

let activeLocks = 0;
let previousOverflow = '';

// Nested dialogs must keep the page locked until the last overlay is closed.
export default function useBodyScrollLock(enabled) {
  useEffect(() => {
    if (!enabled) return undefined;
    if (activeLocks === 0) {
      previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
    }
    activeLocks += 1;
    return () => {
      activeLocks -= 1;
      if (activeLocks === 0) document.body.style.overflow = previousOverflow;
    };
  }, [enabled]);
}
