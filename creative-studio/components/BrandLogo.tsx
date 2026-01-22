import React from 'react';

export const BrandLogo: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 200 150" fill="currentColor" xmlns="http://www.w3.org/2000/svg" className={className}>
    {/* T Shape: Sharp, geometric, heavy top bar with diagonal cut */}
    <path d="M10 20 H 120 L 100 55 H 75 V 130 H 40 V 55 H 10 V 20 Z" />
    
    {/* C Shape: Matching geometry, parallel diagonal cut, square structure */}
    <path d="M130 20 H 190 V 130 H 85 V 95 H 155 V 55 H 110 L 130 20 Z" />
  </svg>
);