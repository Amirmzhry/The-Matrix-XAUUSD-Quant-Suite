import React, { useEffect, useState } from 'react';
import { Shield, Radio, Activity } from 'lucide-react';

interface Session {
  name: string;
  color: string;
  hours: string;
  active: boolean;
}

export default function MarketClocks() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getSessionStatus = (hours: number): { asian: boolean; london: boolean; ny: boolean } => {
    // Basic UTC session hours
    // Asian: 00:00 - 09:00 UTC
    // London: 08:00 - 17:00 UTC
    // New York: 13:00 - 22:00 UTC
    const utcHour = new Date().getUTCHours();
    return {
      asian: utcHour >= 0 && utcHour < 9,
      london: utcHour >= 8 && utcHour < 17,
      ny: utcHour >= 13 && utcHour < 22,
    };
  };

  const activeSessions = getSessionStatus(time.getUTCHours());

  const formatLocalTime = (timeZone: string) => {
    return new Intl.DateTimeFormat('en-GB', {
      timeZone,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(time);
  };

  const sessions = [
    { name: 'Asian Session', hours: `TOKYO: ${formatLocalTime('Asia/Tokyo')}`, active: activeSessions.asian },
    { name: 'London Session', hours: `LONDON: ${formatLocalTime('Europe/London')}`, active: activeSessions.london },
    { name: 'New York Session', hours: `NY: ${formatLocalTime('America/New_York')}`, active: activeSessions.ny },
  ];

  return (
    <div className="w-full bg-[#1C1F26] border-b border-line-hairline px-6 py-3 flex flex-wrap justify-between items-center gap-4 text-xs font-mono select-none" role="region" aria-label="Market Session Monitor">
      {/* Session Windows */}
      <div className="flex gap-4">
        {sessions.map((sess) => (
          <div
            key={sess.name}
            className={`flex items-center gap-2 px-3 py-1 rounded border transition-all ${
              sess.active ? 'text-[#C9A15A] border-[#C9A15A] bg-[#C9A15A]/10 shadow-[0_0_8px_rgba(201,161,90,0.1)]' : 'text-[#8B909C] border-[#333A45] opacity-40'
            }`}
            tabIndex={0}
            aria-label={`${sess.name}: ${sess.hours}. Status: ${sess.active ? 'Active' : 'Closed'}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${sess.active ? 'bg-accent-bullion animate-ping' : 'bg-gray-500'}`} />
            <span className={`font-semibold ${sess.active ? 'text-[#C9A15A]' : 'text-[#EDEEF0]'}`}>{sess.name}</span>
            <span className="text-[10px] text-text-muted">{sess.hours}</span>
          </div>
        ))}
      </div>

      {/* Clock & Status */}
      <div className="flex items-center gap-6">
        {/* Symbol */}
        <div className="flex items-center gap-2 border-r border-line-hairline pr-6" tabIndex={0} aria-label="Selected Asset: Gold Spot (XAUUSD)">
          <Shield className="w-4 h-4 text-accent-bullion" />
          <span className="font-bold text-accent-bullion text-sm">XAUUSD</span>
          <span className="text-[10px] text-text-muted font-sans font-medium px-1.5 py-0.5 rounded bg-line-hairline">SPOT</span>
        </div>

        {/* System Time */}
        <div className="flex items-center gap-2 border-r border-line-hairline pr-6" tabIndex={0} aria-label={`UTC System Time: ${time.toUTCString().split(' ')[4]}`}>
          <span className="text-text-muted text-[10px]">UTC NOW:</span>
          <span className="font-bold text-text-primary text-sm">{time.toISOString().split('T')[1].split('.')[0]}</span>
        </div>

        {/* Status link */}
        <div className="flex items-center gap-2" tabIndex={0} aria-label="Core Engine Connection Status: Connected">
          <Activity className="w-4 h-4 text-status-approved animate-pulse" />
          <span className="font-bold text-status-approved text-xs">QUANT CORE ONLINE</span>
        </div>
      </div>
    </div>
  );
}
