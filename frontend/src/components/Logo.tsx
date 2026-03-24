export default function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        {/* Glow filters */}
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="glowStrong" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        {/* Gradients */}
        <linearGradient id="tealGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2dd4bf" />
          <stop offset="100%" stopColor="#0d9488" />
        </linearGradient>
        <linearGradient id="goldGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fbbf24" />
          <stop offset="100%" stopColor="#d97706" />
        </linearGradient>
        <linearGradient id="amberGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#b45309" />
        </linearGradient>
        <radialGradient id="sphereGrad" cx="40%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#134e4a" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#042f2e" stopOpacity="0.05" />
        </radialGradient>
        <linearGradient id="orbitGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0" />
          <stop offset="50%" stopColor="#2dd4bf" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Background sphere fill */}
      <circle cx="60" cy="60" r="44" fill="url(#sphereGrad)" />

      {/* Globe grid lines - longitude */}
      <ellipse cx="60" cy="60" rx="44" ry="44" stroke="#0d9488" strokeWidth="1.2" strokeOpacity="0.5" fill="none" />
      <ellipse cx="60" cy="60" rx="22" ry="44" stroke="#0d9488" strokeWidth="0.7" strokeOpacity="0.35" fill="none" />
      <ellipse cx="60" cy="60" rx="36" ry="44" stroke="#0d9488" strokeWidth="0.7" strokeOpacity="0.3" fill="none" />
      <ellipse cx="60" cy="60" rx="8" ry="44" stroke="#0d9488" strokeWidth="0.5" strokeOpacity="0.2" fill="none" />

      {/* Globe grid lines - latitude */}
      <ellipse cx="60" cy="60" rx="44" ry="12" stroke="#0d9488" strokeWidth="0.7" strokeOpacity="0.3" fill="none" />
      <ellipse cx="60" cy="42" rx="38" ry="10" stroke="#0d9488" strokeWidth="0.7" strokeOpacity="0.25" fill="none" />
      <ellipse cx="60" cy="78" rx="38" ry="10" stroke="#0d9488" strokeWidth="0.7" strokeOpacity="0.25" fill="none" />
      <line x1="16" y1="60" x2="104" y2="60" stroke="#0d9488" strokeWidth="0.8" strokeOpacity="0.35" />

      {/* Highlighted strategic borders / continent outlines (abstract) */}
      <path d="M38 38 Q45 32 55 35 Q62 30 70 36 Q75 40 72 48" stroke="#2dd4bf" strokeWidth="1" strokeOpacity="0.6" fill="none" filter="url(#glow)" />
      <path d="M48 55 Q55 50 65 52 Q72 55 78 60 Q82 65 76 72" stroke="#2dd4bf" strokeWidth="1" strokeOpacity="0.5" fill="none" filter="url(#glow)" />
      <path d="M32 58 Q36 52 42 55 Q46 60 42 66" stroke="#2dd4bf" strokeWidth="0.8" strokeOpacity="0.4" fill="none" />

      {/* Geopolitical influence vectors - glowing lines connecting regions */}
      <line x1="40" y1="36" x2="72" y2="48" stroke="url(#goldGrad)" strokeWidth="1" strokeOpacity="0.7" filter="url(#glow)" strokeDasharray="3 2" />
      <line x1="35" y1="60" x2="65" y2="52" stroke="url(#goldGrad)" strokeWidth="0.8" strokeOpacity="0.5" filter="url(#glow)" strokeDasharray="2 2" />
      <line x1="50" y1="72" x2="78" y2="60" stroke="url(#goldGrad)" strokeWidth="0.8" strokeOpacity="0.5" filter="url(#glow)" strokeDasharray="2 2" />

      {/* Influence vector dots at endpoints */}
      <circle cx="40" cy="36" r="2" fill="#fbbf24" fillOpacity="0.8" filter="url(#glow)" />
      <circle cx="72" cy="48" r="2" fill="#fbbf24" fillOpacity="0.8" filter="url(#glow)" />
      <circle cx="65" cy="52" r="1.5" fill="#fbbf24" fillOpacity="0.6" />
      <circle cx="78" cy="60" r="1.5" fill="#fbbf24" fillOpacity="0.6" />

      {/* Orbital ring */}
      <ellipse cx="60" cy="60" rx="52" ry="16" transform="rotate(-25 60 60)" stroke="url(#orbitGrad)" strokeWidth="1" fill="none" />

      {/* Commodity symbols on orbit */}
      {/* Gold bar - geometric (top-right) */}
      <g transform="translate(92, 38) rotate(-25)" filter="url(#glow)">
        <path d="M-5 -3 L5 -3 L4 3 L-4 3 Z" fill="none" stroke="#fbbf24" strokeWidth="1.2" />
        <line x1="-2" y1="-3" x2="-1.5" y2="3" stroke="#fbbf24" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="2" y1="-3" x2="1.5" y2="3" stroke="#fbbf24" strokeWidth="0.5" strokeOpacity="0.5" />
      </g>

      {/* Oil drop - geometric (bottom-left) */}
      <g transform="translate(24, 78)" filter="url(#glow)">
        <path d="M0 -6 Q4 -1 4 2 Q4 6 0 6 Q-4 6 -4 2 Q-4 -1 0 -6 Z" fill="none" stroke="#d97706" strokeWidth="1.2" />
        <path d="M0 -2 Q1.5 0 1.5 1.5 Q1.5 3 0 3" stroke="#d97706" strokeWidth="0.5" strokeOpacity="0.5" fill="none" />
      </g>

      {/* Wheat/grain - geometric (bottom-right) */}
      <g transform="translate(96, 72)" filter="url(#glow)">
        <line x1="0" y1="6" x2="0" y2="-4" stroke="#f59e0b" strokeWidth="1" />
        <path d="M0 -4 Q-3 -2 0 0" stroke="#f59e0b" strokeWidth="0.8" fill="none" />
        <path d="M0 -4 Q3 -2 0 0" stroke="#f59e0b" strokeWidth="0.8" fill="none" />
        <path d="M0 -2 Q-2.5 0 0 2" stroke="#f59e0b" strokeWidth="0.8" fill="none" />
        <path d="M0 -2 Q2.5 0 0 2" stroke="#f59e0b" strokeWidth="0.8" fill="none" />
      </g>

      {/* Outer glow ring */}
      <circle cx="60" cy="60" r="44" stroke="#2dd4bf" strokeWidth="0.5" strokeOpacity="0.15" fill="none" />
      <circle cx="60" cy="60" r="46" stroke="#2dd4bf" strokeWidth="0.3" strokeOpacity="0.08" fill="none" />
    </svg>
  )
}
