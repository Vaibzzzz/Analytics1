// src/components/Header.jsx

import { useEffect, useState } from 'react';

export default function Header({ points }) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="flex justify-between items-center bg-[#001328] border-b border-[#002b5c] px-8 py-4">
      <h2 className="text-white text-lg">
        Your AI-powered transaction intelligence hub
      </h2>
      <div className="flex items-center space-x-6">
        {/* Time Display */}
        <div className="flex items-center space-x-2">
          <span className="bg-green-400 text-[#001f3f] px-2 py-1 rounded text-sm">Time</span>
          <span className="text-gray-400 font-mono">{now.toLocaleTimeString()}</span>
        </div>
        {/* Points Display */}
        <div className="flex items-center space-x-2">
          <span className="bg-yellow-400 text-[#001f3f] px-2 py-1 rounded text-sm">Points</span>
          <span className="text-white font-mono">{points}</span>
        </div>
      </div>
    </header>
  );
}
