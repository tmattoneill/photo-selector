import { useEffect } from 'react';
import type { Selection } from '../api/types';

interface UseKeyboardProps {
  onKeyPress: (key: Selection) => void;
  enabled?: boolean;
}

export const useKeyboard = ({ onKeyPress, enabled = true }: UseKeyboardProps) => {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Prevent handling if user is typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (event.key) {
        case '1':
          event.preventDefault();
          onKeyPress('LEFT');
          break;
        case '2':
          event.preventDefault();
          onKeyPress('RIGHT');
          break;
        case '3':
          event.preventDefault();
          onKeyPress('SKIP');
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onKeyPress, enabled]);
};