import React, { useEffect, useRef, useState } from 'react';
import { Terminal, Shield } from 'lucide-react';

interface AgentConsoleProps {
  logs: string[];
}

export default function AgentConsole({ logs }: AgentConsoleProps) {
  const terminalEndRef = useRef<HTMLDivElement>(null);
  
  const [typedLines, setTypedLines] = useState<string[]>(logs);
  const [currentLineIndex, setCurrentLineIndex] = useState(logs.length);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);

  // Auto-scroll to bottom of terminal
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [typedLines, currentCharIndex]);

  // Reset typewriter when logs array is cleared
  useEffect(() => {
    if (logs.length === 0) {
      setTypedLines([]);
      setCurrentLineIndex(0);
      setCurrentCharIndex(0);
    }
  }, [logs]);

  // Typewriter effect
  useEffect(() => {
    if (currentLineIndex < logs.length) {
      const targetLine = logs[currentLineIndex];
      
      if (currentCharIndex < targetLine.length) {
        const timeout = setTimeout(() => {
          setCurrentCharIndex(prev => prev + 1);
        }, Math.random() * 15 + 5); // 5 to 20ms per char
        return () => clearTimeout(timeout);
      } else {
        // Line finished typing
        setTypedLines(prev => [...prev, targetLine]);
        setCurrentLineIndex(prev => prev + 1);
        setCurrentCharIndex(0);
      }
    }
  }, [logs, currentLineIndex, currentCharIndex]);

  const getLineStyle = (line: string) => {
    if (line.includes('⚠️') || line.includes('VETOED') || line.includes('REJECTED') || line.includes('ERR') || line.includes('Error')) {
      return 'text-[#ff4560] [text-shadow:0_0_5px_rgba(255,69,96,0.8)] font-semibold'; // Ruby red
    }
    if (line.includes('WARN')) {
      return 'text-[#ffb700] [text-shadow:0_0_5px_rgba(255,183,0,0.8)] font-semibold'; // Amber warning
    }
    // Default matrix green
    return 'text-[#00FF41] [text-shadow:0_0_5px_rgba(0,255,65,0.5)]'; 
  };

  return (
    <div className="w-full flex flex-col gap-4">
      <style>{`
        @keyframes blinkCursor {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .matrix-cursor {
          display: inline-block;
          width: 8px;
          height: 14px;
          background-color: #00FF41;
          box-shadow: 0 0 5px #00FF41;
          animation: blinkCursor 1s step-end infinite;
          vertical-align: middle;
          margin-left: 2px;
        }
      `}</style>
      
      <div className="flex justify-between items-center pb-3 border-b border-line-hairline">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-accent-bullion" />
          <h2 className="font-bold text-text-primary text-sm uppercase tracking-wider">Agent Debate Console</h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-text-muted font-mono bg-[#14161A] px-2.5 py-1 rounded border border-line-hairline">
          <Shield className="w-3.5 h-3.5 text-accent-bullion" />
          REACT CONSENSUS DESK
        </div>
      </div>

      <div className="glass-panel rounded-xl p-1 overflow-hidden">
        {/* Terminal Canvas */}
        <div className="bg-[#050a0f] rounded-lg p-6 h-[550px] overflow-y-auto font-mono text-xs flex flex-col gap-1.5 shadow-[inset_0_0_20px_rgba(0,255,65,0.05),_0_0_15px_rgba(0,255,65,0.1)] border border-[#00FF41]/20">
          {logs.length === 0 ? (
            <div className="text-[#00FF41]/50 italic flex flex-col items-center justify-center h-full select-none gap-2">
              <div>Quant Core Offline. Awaiting parameters.</div>
              <div className="matrix-cursor opacity-50" />
            </div>
          ) : (
            <>
              {typedLines.map((line, idx) => (
                <div 
                  key={idx} 
                  className={`leading-relaxed whitespace-pre-wrap ${getLineStyle(line)}`}
                  tabIndex={0}
                >
                  {line}
                </div>
              ))}
              
              {currentLineIndex < logs.length && (
                <div className={`leading-relaxed whitespace-pre-wrap ${getLineStyle(logs[currentLineIndex])}`}>
                  {logs[currentLineIndex].slice(0, currentCharIndex)}
                  <span className="matrix-cursor" />
                </div>
              )}
              
              {currentLineIndex >= logs.length && logs.length > 0 && (
                 <div className="leading-relaxed whitespace-pre-wrap mt-1">
                    <span className="matrix-cursor" />
                 </div>
              )}
            </>
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
