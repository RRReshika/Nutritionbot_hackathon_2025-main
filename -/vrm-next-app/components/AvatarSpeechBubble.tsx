'use client';

import { useEffect, useState } from 'react';

interface AvatarSpeechBubbleProps {
  myTake: string | null;
}

export default function AvatarSpeechBubble({ myTake }: AvatarSpeechBubbleProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [displayText, setDisplayText] = useState('');

  useEffect(() => {
    if (myTake && myTake.trim()) {
      setDisplayText(myTake);
      setIsVisible(true);
    } else {
      setIsVisible(false);
    }
  }, [myTake]);

  if (!isVisible || !displayText) {
    return null;
  }

  return (
    <div style={{
      position: 'absolute',
      top: '20%',
      left: '5%',
      zIndex: 1000,
      animation: 'float 3s ease-in-out infinite'
    }}>
      {/* Pixel art speech bubble */}
      <div style={{
        position: 'relative',
        background: 'white',
        border: '4px solid black',
        borderRadius: '0',
        padding: '12px 16px',
        minWidth: '200px',
        maxWidth: '280px',
        boxShadow: '6px 6px 0px rgba(0,0,0,0.3)',
        clipPath: 'polygon(0 0, 100% 0, 100% 100%, 15% 100%, 15% calc(100% + 12px), 10% 100%, 0 100%)'
      }}>
        <p style={{
          margin: 0,
          fontSize: '14px',
          lineHeight: '1.4',
          color: '#000',
          fontWeight: '500',
          fontFamily: 'monospace'
        }}>
          💭 {displayText}
        </p>
      </div>
    </div>
  );
}
