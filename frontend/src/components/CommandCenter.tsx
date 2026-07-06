import React from 'react';
import { Play, Sliders, Cpu, Info, BookOpen, Terminal } from 'lucide-react';

interface CommandCenterProps {
  startDate: string;
  setStartDate: (val: string) => void;
  endDate: string;
  setEndDate: (date: string) => void;
  historyLength: number;
  setHistoryLength: (length: number) => void;
  pipelineRunning: boolean;
  progressPhase: string;
  onStartPipeline: (start: string, end: string, isMock?: boolean) => void;
}

export default function CommandCenter({
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  historyLength,
  setHistoryLength,
  pipelineRunning,
  progressPhase,
  onStartPipeline
}: CommandCenterProps) {

  const handleInitiate = () => {
    onStartPipeline(startDate, endDate);
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto select-text">
      {/* Engine Status Banner */}
      <div className="glass-panel rounded-xl p-6 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${pipelineRunning ? 'bg-bullion/10 text-bullion animate-pulse' : 'bg-line-hairline text-muted'}`}>
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-primary uppercase tracking-wider">Quant Engine Status</h4>
            <p className="text-xs text-muted font-mono mt-0.5">
              {pipelineRunning ? progressPhase : 'QUANT CORE STANDBY. Select parameters and initiate execution.'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${pipelineRunning ? 'bg-bullion animate-ping' : 'bg-status-vetoed'}`} />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-primary">
            {pipelineRunning ? 'COMPUTING' : 'OFFLINE'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] gap-6">
        {/* Left Control array */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-5">
          <div className="flex items-center gap-2 pb-2 border-b border-line-hairline">
            <Sliders className="w-4 h-4 text-bullion" />
            <h3 className="font-bold text-primary text-sm uppercase tracking-wider">Control Array</h3>
          </div>

          <div className="flex flex-col gap-3">
            <div>
              <label className="text-[10px] text-muted font-mono uppercase tracking-wider block mb-1">Start Ingestion Date</label>
              <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-graphite border border-line-hairline rounded px-3 py-2 text-xs font-mono text-primary focus:outline-none focus:border-bullion"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted font-mono uppercase tracking-wider block mb-1">End Ingestion Date</label>
              <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-graphite border border-line-hairline rounded px-3 py-2 text-xs font-mono text-primary focus:outline-none focus:border-bullion"
              />
            </div>
          </div>

          <div className="flex flex-col gap-4 pt-2 border-t border-line-hairline/30">


            <div>
              <div className="flex justify-between text-[10px] text-muted font-mono uppercase mb-1">
                <span>History Length</span>
                <span className="text-bullion font-bold">{historyLength} ticks</span>
              </div>
              <input 
                type="range" 
                min="50" 
                max="500" 
                step="10" 
                value={historyLength} 
                onChange={(e) => setHistoryLength(parseInt(e.target.value))}
                className="w-full accent-bullion bg-graphite"
              />
            </div>
          </div>

          <button
            onClick={handleInitiate}
            disabled={pipelineRunning}
            className="w-full mt-2 flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-xs uppercase tracking-widest text-[#070A0F] bg-gradient-to-r from-bullion to-[#AA7C11] hover:scale-[1.02] active:scale-100 hover:shadow-[0_0_15px_rgba(201,161,90,0.4)] disabled:opacity-50 disabled:pointer-events-none transition-all"
            aria-label="Initiate quant core engine execution"
          >
            <Play className="w-4 h-4 fill-current" />
            Initiate Quant Core
          </button>
          
          <div className="mt-4 pt-4 border-t border-line-hairline flex flex-col gap-2">
            <button
              onClick={() => onStartPipeline(startDate, endDate, true)}
              disabled={pipelineRunning}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg font-bold text-[10px] uppercase tracking-widest text-muted border border-line-hairline bg-graphite hover:bg-[#333A45]/30 transition-all disabled:opacity-50 disabled:pointer-events-none"
            >
              <Terminal className="w-3 h-3" />
              Test Pipeline (Mock Data)
            </button>
            <p className="text-[9px] text-muted text-center italic">
              This is for when you want to test quickly and we don't have live data!
            </p>
          </div>
        </div>

        {/* Right Dashboard Explanation */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 pb-2 border-b border-line-hairline">
            <BookOpen className="w-4 h-4 text-bullion" />
            <h3 className="font-bold text-primary text-sm uppercase tracking-wider">Technical System Explanations</h3>
          </div>

          <div className="text-xs text-muted leading-relaxed flex flex-col gap-4 font-sans">
            <p>
              <strong>The Matrix: XAUUSD Quant Suite</strong> is an institutional-grade high-frequency trading (HFT) microstructural noise filtering platform. It sits between raw interbank liquidity feeds and MetaTrader 5 (MT5) execution terminals to isolate price discovery from toxicity spikes.
            </p>

            <div className="bg-graphite/50 p-4 rounded-lg border border-line-hairline/50 flex flex-col gap-3">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-bullion shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-semibold text-primary mb-1 uppercase tracking-wide text-[10px]">5-Agent Quantitative consensus Engine</h5>
                  <p className="text-[11px]">
                    This platform uses a multi-agent framework to evaluate volatility regimes and execute filtering:
                  </p>
                </div>
              </div>
              <ul className="list-disc pl-5 space-y-1.5 text-[11px]">
                <li><strong className="text-primary font-mono">DataAnalystAgent</strong>: Ingests tick-level microstructure logs and computes Bid/Ask imbalances and arrival rates.</li>
                <li><strong className="text-primary font-mono">LeadQuantAgent</strong>: Dynamically optimizes the Hampel filter threshold ($\sigma$) and Kalman transition variance ($R$).</li>
                <li><strong className="text-primary font-mono">RiskOfficerAgent</strong>: Audits information leakage ($Q$-Score) and return distribution kurtosis to prevent execution during toxicity shocks.</li>
                <li><strong className="text-primary font-mono">VisualizerAgent</strong>: Compiles dense HTML visual overlays showing the original feed versus the filtered, denoised curve.</li>
                <li><strong className="text-primary font-mono">MQL5SynthesizerAgent</strong>: Compiles parameters into a production-ready C++ `.mqh` library for the MT5 Expert Advisor.</li>
              </ul>
            </div>

            <p>
              To begin, adjust the <strong>Spike Multiplier</strong> (which sets the threshold bounds for Hampel vetoing) and the <strong>History Length</strong> (the sliding window size for local median estimation), select a target date range, and press <strong>Initiate Quant Core</strong>. The live progress logs will stream under the <em>Agent Console</em> and analytics will unlock in the <em>Analytics Gallery</em>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
