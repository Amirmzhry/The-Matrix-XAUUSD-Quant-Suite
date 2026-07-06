import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, ShieldAlert, Cpu, Layers, CheckCircle2, ChevronRight, Sliders, Database
} from 'lucide-react';
import { 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ReferenceArea
} from 'recharts';

interface LiveMonitorProps {
  onStartPipeline: (start: string, end: string) => void;
  pipelineRunning: boolean;
  progressPhase: string;
  metrics: {
    q_score: string;
    kurtosis: string;
    regime: string;
  };
}

export default function LiveMonitor({ onStartPipeline, pipelineRunning, progressPhase, metrics }: LiveMonitorProps) {
  const [startDate, setStartDate] = useState('2025-01-06');
  const [endDate, setEndDate] = useState('2025-01-07');
  
  // Controls
  const [spikeMultiplier, setSpikeMultiplier] = useState(3.0);
  const [historyLength, setHistoryLength] = useState(100);

  // Mock Tick Stream Data driven by active parameters
  const [ticks, setTicks] = useState<any[]>([]);

  useEffect(() => {
    if (!pipelineRunning) {
      setTicks([]);
      return;
    }
    // Generate synthetic microstructural ticks to simulate live run
    const generateTicks = () => {
      const result = [];
      let price = 2350.0;
      const now = Date.now();
      for (let i = 0; i < 50; i++) {
        const timestamp = new Date(now - (50 - i) * 1000).toISOString().split('T')[1].slice(0, -1);
        const spread = parseFloat((0.1 + Math.random() * 0.2).toFixed(2));
        const roc = parseFloat((Math.sin(i / 5) * 0.2 + (Math.random() - 0.5) * 0.15).toFixed(4));
        const qScore = parseFloat((0.1 + Math.random() * 0.6).toFixed(2));
        
        // Outliers
        const isOutlier = Math.abs(roc) > 0.18;
        const verdict = isOutlier ? 'Veto' : 'Pass';

        result.push({
          id: i,
          time: timestamp,
          bid: parseFloat((price - spread/2).toFixed(2)),
          ask: parseFloat((price + spread/2).toFixed(2)),
          spread,
          roc,
          qScore,
          verdict
        });
        price += roc * 2.0;
      }
      setTicks(result);
    };
    generateTicks();
  }, [pipelineRunning]);

  // Toxicity Radar Dimensions
  const isActive = pipelineRunning || metrics.regime !== 'OFFLINE';
  const radarData = [
    { subject: 'Info Leakage', value: isActive ? (parseFloat(metrics.q_score) * 100 || 0) : 0 },
    { subject: 'Spread Widening', value: isActive ? 65 : 0 },
    { subject: 'Order Book Skew', value: isActive ? 80 : 0 },
    { subject: 'Return Kurtosis', value: isActive ? ((parseFloat(metrics.kurtosis) / 6) * 100 || 0) : 0 },
    { subject: 'Hampel Delta', value: isActive ? 30 : 0 },
  ];

  const qValue = isActive ? (parseFloat(metrics.q_score) || 0) : 0;
  const needleRotation = (qValue * 180) - 90; // Map 0-1 to -90 to +90 deg

  const handleInitiate = () => {
    onStartPipeline(startDate, endDate);
  };

  const isExtreme = metrics.regime === 'EXTREME_SPIKE' || parseFloat(metrics.kurtosis) > 3.0;

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Structural Split Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        {/* Left Column: Control Panel */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 pb-2 border-b border-line-hairline">
            <Sliders className="w-4 h-4 text-accent-bullion" />
            <h3 className="font-bold text-text-primary text-sm uppercase tracking-wider">Control Array</h3>
          </div>

          <div className="flex flex-col gap-3">
            <div>
              <label className="text-[10px] text-text-muted font-mono uppercase tracking-wider block mb-1">Start Date</label>
              <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-[#14161A] border border-line-hairline rounded px-3 py-2 text-xs font-mono text-text-primary focus:outline-none focus:border-accent-bullion"
              />
            </div>
            <div>
              <label className="text-[10px] text-text-muted font-mono uppercase tracking-wider block mb-1">End Date</label>
              <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-[#14161A] border border-line-hairline rounded px-3 py-2 text-xs font-mono text-text-primary focus:outline-none focus:border-accent-bullion"
              />
            </div>
          </div>

          {/* Radix Sliders Mock */}
          <div className="flex flex-col gap-4 pt-2 border-t border-line-hairline/30">
            <div>
              <div className="flex justify-between text-[10px] text-text-muted font-mono uppercase mb-1">
                <span>Spike Multiplier</span>
                <span className="text-accent-bullion font-bold">{spikeMultiplier}σ</span>
              </div>
              <input 
                type="range" 
                min="1" 
                max="10" 
                step="0.5" 
                value={spikeMultiplier} 
                onChange={(e) => setSpikeMultiplier(parseFloat(e.target.value))}
                className="w-full accent-accent-bullion bg-[#14161A]"
              />
            </div>

            <div>
              <div className="flex justify-between text-[10px] text-text-muted font-mono uppercase mb-1">
                <span>History Length</span>
                <span className="text-accent-bullion font-bold">{historyLength} ticks</span>
              </div>
              <input 
                type="range" 
                min="50" 
                max="500" 
                step="10" 
                value={historyLength} 
                onChange={(e) => setHistoryLength(parseInt(e.target.value))}
                className="w-full accent-accent-bullion bg-[#14161A]"
              />
            </div>
          </div>

          <button
            onClick={handleInitiate}
            disabled={pipelineRunning}
            className="w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-xs uppercase tracking-widest text-[#070A0F] bg-gradient-to-r from-accent-bullion to-[#AA7C11] hover:scale-[1.02] active:scale-100 hover:shadow-[0_0_15px_rgba(201,161,90,0.4)] disabled:opacity-50 disabled:pointer-events-none transition-all"
            aria-label="Initiate quant core engine execution"
          >
            <Play className="w-4 h-4 fill-current" />
            Initiate Quant Core
          </button>
        </div>

        {/* Right Column: Live Monitor HUD */}
        <div className="flex flex-col gap-6">
          {/* Active Phase Progress or Idle Status */}
          <div className="glass-panel rounded-xl p-6 flex flex-wrap justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${pipelineRunning ? 'bg-accent-bullion/10 text-accent-bullion animate-pulse' : 'bg-line-hairline text-text-muted'}`}>
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-text-primary">ENGINE STATUS</h4>
                <p className="text-xs text-text-muted font-mono mt-0.5">
                  {pipelineRunning ? progressPhase : 'Quantum Core Idle. Select parameters and initiate execution.'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${pipelineRunning ? 'bg-accent-bullion animate-ping' : 'bg-status-vetoed'}`} />
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-text-primary">
                {pipelineRunning ? 'COMPUTING' : 'OFFLINE'}
              </span>
            </div>
          </div>

          {/* HUD Metric Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-2">Toxicity Index (Q-Score)</div>
              <div className="text-3xl font-mono font-bold text-accent-bullion" tabIndex={0} aria-label={`Q-Score is ${metrics.q_score}`}>{metrics.q_score}</div>
              <div className="text-[10px] text-text-muted mt-2">Scale: 0 to 1.0 (Low to High risk)</div>
            </div>

            <div className={`glass-panel rounded-xl p-6 relative overflow-hidden ${isExtreme ? 'kurtosis-alert' : ''}`}>
              <div className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-2">Fat-Tail Stress (Kurtosis)</div>
              <div className={`text-3xl font-mono font-bold ${isExtreme ? 'text-status-vetoed' : 'text-text-primary'}`} tabIndex={0} aria-label={`Kurtosis is ${metrics.kurtosis}`}>{metrics.kurtosis}</div>
              <div className="text-[10px] text-text-muted mt-2">
                {isExtreme ? '🚨 CRITICAL FAT-TAIL SPIKE' : 'Standard Fat-tail distributions'}
              </div>
            </div>

            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-2">Volatility Regime</div>
              <div className="mt-2">
                <span className={`regime-badge ${isExtreme ? 'border-status-vetoed text-status-vetoed bg-status-vetoed/10' : ''}`} tabIndex={0} aria-label={`Locked Volatility Regime is ${metrics.regime}`}>
                  {metrics.regime}
                </span>
              </div>
              <div className="text-[10px] text-text-muted mt-4">Microstructure noise signature</div>
            </div>
          </div>
        </div>
      </div>

      {/* Stage 3: Toxicity Vector & Q-Score Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Box: Needle Gauge */}
        <div className="glass-panel rounded-xl p-6 flex flex-col items-center">
          <h3 className="font-bold text-text-primary text-sm uppercase tracking-wider w-full pb-3 border-b border-line-hairline mb-6">Toxicity Vector Gauge</h3>
          <div className="relative w-64 h-32 flex justify-center items-end overflow-hidden mb-4">
            {/* SVG Arc */}
            <svg className="absolute w-64 h-64 transform rotate-180" viewBox="0 0 100 100">
              {/* Background Arc */}
              <circle cx="50" cy="50" r="40" fill="none" stroke="#2A2E37" strokeWidth="8" strokeDasharray="125 125" />
              {/* Colored Segments */}
              <circle cx="50" cy="50" r="40" fill="none" stroke="#4E9E6E" strokeWidth="8" strokeDasharray="50 125" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="#C9A15A" strokeWidth="8" strokeDasharray="95 125" strokeDashoffset="-50" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="#B5514A" strokeWidth="8" strokeDasharray="125 125" strokeDashoffset="-95" />
            </svg>
            
            {/* Needle */}
            <div 
              className="absolute bottom-0 w-1 h-24 bg-accent-bullion origin-bottom transition-all duration-1000 ease-out"
              style={{ transform: `rotate(${needleRotation}deg)` }}
            >
              <div className="w-3 h-3 bg-accent-bullion rounded-full absolute bottom-0 -left-1 border border-graphite" />
            </div>
          </div>
          <div className="text-center font-mono" tabIndex={0} aria-label={`Needle points to Q-Score ${metrics.q_score}`}>
            <span className="text-2xl font-bold text-accent-bullion">{metrics.q_score}</span>
            <div className="text-[10px] text-text-muted uppercase tracking-wider mt-1">Toxicity Index Value</div>
          </div>
        </div>

        {/* Right Box: Radar Deck */}
        <div className="glass-panel rounded-xl p-6 flex flex-col items-center">
          <h3 className="font-bold text-text-primary text-sm uppercase tracking-wider w-full pb-3 border-b border-line-hairline mb-4">Toxicity Dimensions Radar</h3>
          <div className="w-full h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="#2A2E37" />
                <PolarAngleAxis dataKey="subject" stroke="#8B909C" fontSize={10} fontFamily="Inter" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#2A2E37" tick={false} />
                <Radar name="Toxicity Index" dataKey="value" stroke="#C9A15A" fill="#C9A15A" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Stage 4: Tick Stream & Volatility Shift Visualization */}
      <div className="glass-panel rounded-xl p-6 w-full">
        <div className="flex justify-between items-center pb-3 border-b border-line-hairline mb-6">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-accent-bullion" />
            <h3 className="font-bold text-text-primary text-sm uppercase tracking-wider">Tick Price Velocity (ROC) overlay</h3>
          </div>
          <div className="text-[10px] text-text-muted font-mono uppercase">Live tick processing (4-10fps throttling)</div>
        </div>

        <div className="w-full h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={ticks} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <XAxis dataKey="time" stroke="#8B909C" fontSize={10} fontFamily="JetBrains Mono" />
              <YAxis stroke="#8B909C" fontSize={10} fontFamily="JetBrains Mono" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1C1F26', borderColor: '#2A2E37', color: '#EDEEF0', fontFamily: 'JetBrains Mono' }}
                itemStyle={{ color: '#C9A15A' }}
              />
              
              {/* Session Threshold Bands */}
              <ReferenceLine y={0.18} stroke="#B5514A" strokeDasharray="3 3" label={{ value: '+ROC Threshold', fill: '#B5514A', fontSize: 9 }} />
              <ReferenceLine y={-0.18} stroke="#B5514A" strokeDasharray="3 3" label={{ value: '-ROC Threshold', fill: '#B5514A', fontSize: 9 }} />
              <ReferenceLine y={0} stroke="#2A2E37" />

              <Line 
                type="monotone" 
                dataKey="roc" 
                stroke="#C9A15A" 
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  if (payload.verdict === 'Veto') {
                    return (
                      <circle key={payload.id} cx={cx} cy={cy} r={5} fill="#B5514A" className="animate-ping" stroke="none" />
                    );
                  }
                  return null;
                }}
                activeDot={{ r: 6 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Raw Tick Data Desk (Virtualized Grid Table) */}
        <h4 className="font-bold text-xs uppercase tracking-wider text-text-primary mt-6 mb-3">Raw Microstructure Tick Registry</h4>
        <div className="w-full max-h-60 overflow-y-auto border border-line-hairline rounded-lg">
          <table className="w-full text-xs font-mono select-text" role="grid" aria-label="Microstructure Ticks">
            <thead className="bg-[#14161A] text-text-muted sticky top-0 border-b border-line-hairline z-10">
              <tr>
                <th className="py-2.5 px-4 text-left font-sans font-semibold">Timestamp</th>
                <th className="py-2.5 px-4 text-right font-sans font-semibold">Bid Price</th>
                <th className="py-2.5 px-4 text-right font-sans font-semibold">Ask Price</th>
                <th className="py-2.5 px-4 text-right font-sans font-semibold">Spread (ticks)</th>
                <th className="py-2.5 px-4 text-right font-sans font-semibold">Price ROC</th>
                <th className="py-2.5 px-4 text-right font-sans font-semibold">Q-Score</th>
                <th className="py-2.5 px-4 text-center font-sans font-semibold">Hampel Verdict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line-hairline/30 bg-[#1C1F26]">
              {ticks.slice().reverse().map((tick) => (
                <tr key={tick.id} className="hover:bg-line-hairline/20 transition-all">
                  <td className="py-2 px-4 text-left text-text-muted">{tick.time}.{tick.id * 18}</td>
                  <td className="py-2 px-4 text-right text-text-primary num-align-right">{tick.bid.toFixed(2)}</td>
                  <td className="py-2 px-4 text-right text-text-primary num-align-right">{tick.ask.toFixed(2)}</td>
                  <td className="py-2 px-4 text-right text-text-muted num-align-right">{tick.spread.toFixed(2)}</td>
                  <td className="py-2 px-4 text-right text-accent-bullion num-align-right">{tick.roc.toFixed(4)}</td>
                  <td className="py-2 px-4 text-right text-text-muted num-align-right">{tick.qScore.toFixed(2)}</td>
                  <td className="py-2 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      tick.verdict === 'Veto' 
                        ? 'bg-status-vetoed/15 text-status-vetoed border border-status-vetoed/20' 
                        : 'bg-status-approved/15 text-status-approved border border-status-approved/20'
                    }`}>
                      {tick.verdict === 'Veto' ? '❌ VETO' : '✅ PASS'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
