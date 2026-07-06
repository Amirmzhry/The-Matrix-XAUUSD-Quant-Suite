import React, { useState, useEffect } from 'react';
import { 
  BarChart3, LineChart, Layers, HelpCircle, Activity, RadarChart, 
  Database, Gauge, ShieldAlert, TrendingUp 
} from 'lucide-react';
import { 
  Radar, RadarChart as RechartsRadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  ResponsiveContainer, LineChart as RechartsLineChart, Line, XAxis, YAxis, 
  Tooltip, ReferenceLine, BarChart as RechartsBarChart, Bar, CartesianGrid, 
  Legend, AreaChart, Area, Brush
} from 'recharts';

interface AnalyticsGalleryProps {
  metrics: {
    q_score: string | null;
    kurtosis: string | null;
    regime: string | null;
  };
  pipelineRunning: boolean;
  ticks: any[];
}

export default function AnalyticsGallery({ metrics, pipelineRunning, ticks }: AnalyticsGalleryProps) {
  const [activeSubTab, setActiveSubTab] = useState<'live' | 'charts' | 'price_chart'>('live');
  const [chartIndex, setChartIndex] = useState(0);

  const charts = [
    { title: 'Live Price & Cleaned Feed', file: 'chart1_price_overlay.html' },
    { title: 'Distribution & Skewness', file: 'chart2_density_skewness.html' },
    { title: 'Tick Spread Dynamics', file: 'chart3_spread_dynamics.html' },
  ];

  const qValStr = metrics.q_score ?? '0.00';
  const kurtosisValStr = metrics.kurtosis ?? '0.00';
  const regimeValStr = metrics.regime ?? 'OFFLINE';

  const qValue = parseFloat(qValStr) || 0.0;
  const needleRotation = (qValue * 180) - 90; // Map 0-1 to -90 to +90 deg

  const isExtreme = regimeValStr === 'EXTREME_SPIKE' || (parseFloat(kurtosisValStr) > 3.0);
  const dataFlowing = metrics.q_score !== null && regimeValStr !== 'OFFLINE';

  // Toxicity Radar Dimensions (Computed dynamically from real metrics)
  const radarData = [
    { subject: 'Info Leakage', value: dataFlowing ? (qValue * 100) : 0 },
    { subject: 'Spread Widening', value: dataFlowing ? Math.min(100, qValue * 80 + 10) : 0 },
    { subject: 'Order Book Skew', value: dataFlowing ? Math.min(100, parseFloat(kurtosisValStr) * 15 + qValue * 20) : 0 },
    { subject: 'Return Kurtosis', value: dataFlowing ? (Math.min((parseFloat(kurtosisValStr) / 6) * 100, 100)) : 0 },
    { subject: 'Hampel Delta', value: dataFlowing ? Math.min(100, 20 + qValue * 50) : 0 },
  ];

  // If no data flows and not running, block with standby wall
  if (!dataFlowing) {
    if (pipelineRunning) {
      return (
        <div className="glass-panel rounded-xl p-12 text-center max-w-2xl mx-auto flex flex-col items-center justify-center gap-4">
          <div className="w-16 h-16 rounded-full bg-bullion/20 text-bullion flex items-center justify-center mb-2 animate-pulse">
            <Activity className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="font-bold text-lg text-primary uppercase tracking-wider">Receiving information from the agents!</h3>
          <p className="text-xs text-bullion font-mono">Please wait... Data visualization engines are initializing.</p>
        </div>
      );
    }
    return (
      <div className="glass-panel rounded-xl p-12 text-center max-w-2xl mx-auto flex flex-col items-center justify-center gap-4 select-text">
        <div className="w-16 h-16 rounded-full bg-bullion/10 text-bullion flex items-center justify-center mb-2">
          <Database className="w-8 h-8" />
        </div>
        <h3 className="font-bold text-lg text-primary uppercase tracking-wider">Ready to receive telemetry!</h3>
        <p className="text-xs text-muted leading-relaxed font-sans">
          The quantitative engine is currently on standby. Please navigate to the <strong>Command Center</strong> and press <strong>Initiate Quant Core</strong> or run a test.
          Once the pipeline executes, actual market data, toxicity vectors, and live analytics will populate here.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-6 select-text">
      {/* Sub tabs navigation */}
      <div className="flex border-b border-line-hairline gap-2">
        <button
          onClick={() => setActiveSubTab('live')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${
            activeSubTab === 'live' ? 'border-bullion text-bullion' : 'border-transparent text-muted hover:text-primary'
          }`}
        >
          ⚡ Live Telemetry Desk
        </button>
        <button
          onClick={() => setActiveSubTab('charts')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${
            activeSubTab === 'charts' ? 'border-bullion text-bullion' : 'border-transparent text-muted hover:text-primary'
          }`}
        >
          📈 Interactive Overlays
        </button>
        <button
          onClick={() => setActiveSubTab('price_chart')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${
            activeSubTab === 'price_chart' ? 'border-bullion text-bullion' : 'border-transparent text-muted hover:text-primary'
          }`}
        >
          📊 React Price Overlay
        </button>
      </div>

      {/* 1. Live Telemetry Desk (Toxicity Gauge, Radar, ROC, Tick Registry) */}
      {activeSubTab === 'live' && (
        <div className="flex flex-col gap-6">
          {/* HUD Metric Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="text-[10px] text-muted font-mono uppercase tracking-wider mb-2">Toxicity Index (Q-Score)</div>
              <div className="text-3xl font-mono font-bold text-bullion" tabIndex={0} aria-label={`Q-Score is ${qValStr}`}>{qValStr}</div>
              <div className="text-[10px] text-muted mt-2">Scale: 0 to 1.0 (Low to High risk)</div>
            </div>

            <div className={`glass-panel rounded-xl p-6 relative overflow-hidden ${isExtreme ? 'border-status-vetoed bg-status-vetoed/5' : ''}`}>
              <div className="text-[10px] text-muted font-mono uppercase tracking-wider mb-2">Fat-Tail Stress (Kurtosis)</div>
              <div className={`text-3xl font-mono font-bold ${isExtreme ? 'text-status-vetoed' : 'text-primary'}`} tabIndex={0} aria-label={`Kurtosis is ${kurtosisValStr}`}>{kurtosisValStr}</div>
              <div className="text-[10px] text-muted mt-2">
                {isExtreme ? '🚨 CRITICAL FAT-TAIL SPIKE' : 'Standard Fat-tail distributions'}
              </div>
            </div>

            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="text-[10px] text-muted font-mono uppercase tracking-wider mb-2">Volatility Regime</div>
              <div className="mt-2">
                <span className={`px-2.5 py-1 rounded font-mono text-xs font-bold border ${isExtreme ? 'border-status-vetoed text-status-vetoed bg-status-vetoed/10' : 'border-bullion text-bullion bg-bullion/10'}`} tabIndex={0} aria-label={`Locked Volatility Regime is ${regimeValStr}`}>
                  {regimeValStr}
                </span>
              </div>
              <div className="text-[10px] text-muted mt-4">Microstructure noise signature</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Toxicity Needle Gauge */}
            <div className="glass-panel rounded-xl p-6 flex flex-col items-center">
              <h3 className="font-bold text-primary text-sm uppercase tracking-wider w-full pb-3 border-b border-line-hairline mb-6 flex items-center gap-2">
                <Gauge className="w-4 h-4 text-bullion" /> Toxicity Vector Gauge
              </h3>
              <div className="relative w-64 h-32 flex justify-center items-end overflow-hidden mb-4">
                <svg className="absolute w-64 h-64 transform rotate-180" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#2A2E37" strokeWidth="8" strokeDasharray="125 125" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#4E9E6E" strokeWidth="8" strokeDasharray="50 125" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#C9A15A" strokeWidth="8" strokeDasharray="95 125" strokeDashoffset="-50" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#B5514A" strokeWidth="8" strokeDasharray="125 125" strokeDashoffset="-95" />
                </svg>
                
                <div 
                  className="absolute bottom-0 w-1 h-24 bg-bullion origin-bottom transition-all duration-1000 ease-out"
                  style={{ transform: `rotate(${needleRotation}deg)` }}
                >
                  <div className="w-3 h-3 bg-bullion rounded-full absolute bottom-0 -left-1 border border-graphite" />
                </div>
              </div>
              <div className="text-center font-mono">
                <span className="text-2xl font-bold text-bullion">{qValStr}</span>
                <div className="text-[10px] text-muted uppercase tracking-wider mt-1">Toxicity Index Value</div>
              </div>
            </div>

            {/* Toxicity Dimensions Radar */}
            <div className="glass-panel rounded-xl p-6 flex flex-col items-center">
              <h3 className="font-bold text-primary text-sm uppercase tracking-wider w-full pb-3 border-b border-line-hairline mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-bullion" /> Toxicity Dimensions Radar
              </h3>
              <div className="w-full h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid stroke="#2A2E37" />
                    <PolarAngleAxis dataKey="subject" stroke="#8B909C" fontSize={10} fontFamily="Inter" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#2A2E37" tick={false} />
                    <Radar name="Toxicity Index" dataKey="value" stroke="#C9A15A" fill="#C9A15A" fillOpacity={0.25} />
                  </RechartsRadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-6 w-full">
            {/* Raw Microstructure Tick Registry Table */}
            <h4 className="font-bold text-xs uppercase tracking-wider text-primary mt-6 mb-3 flex items-center gap-2">
              <Database className="w-4 h-4 text-bullion" /> Raw Microstructure Tick Registry
            </h4>
            <div className="w-full max-h-60 overflow-y-auto border border-line-hairline rounded-lg">
              {ticks.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted italic font-mono">
                  No registry data available.
                </div>
              ) : (
                <table className="w-full text-xs font-mono" role="grid" aria-label="Microstructure Ticks">
                  <thead className="bg-[#14161A] text-muted sticky top-0 border-b border-line-hairline z-10">
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
                        <td className="py-2 px-4 text-left text-muted">{tick.time}.{tick.id * 18}</td>
                        <td className="py-2 px-4 text-right text-primary">{tick.bid.toFixed(2)}</td>
                        <td className="py-2 px-4 text-right text-ask">{tick.ask.toFixed(2)}</td>
                        <td className="py-2 px-4 text-right text-muted">{tick.spread.toFixed(2)}</td>
                        <td className="py-2 px-4 text-right text-bullion">{tick.roc.toFixed(6)}</td>
                        <td className="py-2 px-4 text-right text-muted">{tick.qScore.toFixed(3)}</td>
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
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2. Interactive Charts iframe */}
      {activeSubTab === 'charts' && (
        <div className="flex flex-col gap-4">
          <div className="flex gap-2">
            {charts.map((c, idx) => (
              <button
                key={c.file}
                onClick={() => setChartIndex(idx)}
                className={`px-4 py-1.5 rounded text-xs font-mono border transition-all ${
                  chartIndex === idx 
                    ? 'bg-bullion/10 border-bullion text-bullion' 
                    : 'border-line-hairline text-muted hover:text-primary'
                }`}
              >
                {c.title}
              </button>
            ))}
          </div>

          <div className="glass-panel rounded-xl p-0.5 overflow-hidden">
            <iframe
              src={`/api/charts/${charts[chartIndex].file}`}
              className="w-full bg-[#1C1F26] border-none"
              style={{ height: '650px' }}
              title={charts[chartIndex].title}
              scrolling="yes"
            />
          </div>
        </div>
      )}

      {/* 3. React Price Overlay (Raw vs Filtered) */}
      {activeSubTab === 'price_chart' && (
        <div className="flex flex-col gap-6">
          <div className="glass-panel rounded-xl p-6 w-full">
            <div className="flex justify-between items-center pb-3 border-b border-line-hairline mb-6">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-bullion" />
                <h3 className="font-bold text-primary text-sm uppercase tracking-wider">Raw vs. Filtered Price (React)</h3>
              </div>
              <div className="text-[10px] text-muted font-mono uppercase">Live Ticks Data Stream</div>
            </div>

            <div className="w-full h-[500px]">
              {ticks.length === 0 ? (
                <div className="w-full h-full flex items-center justify-center text-xs text-muted italic font-mono">
                  No data available to chart.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsLineChart data={ticks} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2A2E37" vertical={false} />
                    <XAxis 
                      dataKey="time" 
                      stroke="#8B909C" 
                      fontSize={10} 
                      fontFamily="JetBrains Mono" 
                      minTickGap={50}
                    />
                    <YAxis 
                      domain={['dataMin', 'dataMax']}
                      stroke="#8B909C" 
                      fontSize={10} 
                      fontFamily="JetBrains Mono" 
                      tickFormatter={(value) => value.toFixed(5)}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1C1F26', borderColor: '#2A2E37', color: '#EDEEF0', fontFamily: 'JetBrains Mono' }}
                      itemStyle={{ fontSize: 11 }}
                      labelStyle={{ color: '#8B909C', marginBottom: '8px' }}
                      formatter={(value: any, name: string) => [Number(value).toFixed(5), name === 'raw_bid' ? 'Raw Bid (Toxic)' : 'Filtered Bid']}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'Inter', paddingTop: '10px' }} />
                    <Line 
                      type="stepAfter" 
                      dataKey="raw_bid" 
                      name="raw_bid"
                      stroke="#ff4560" 
                      strokeWidth={1}
                      dot={false}
                      activeDot={{ r: 4 }} 
                      opacity={0.6}
                    />
                    <Line 
                      type="stepAfter" 
                      dataKey="bid" 
                      name="bid"
                      stroke="#00e396" 
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 6 }} 
                    />
                    <Brush 
                      dataKey="time" 
                      height={30} 
                      stroke="#8B909C" 
                      fill="#1C1F26" 
                      tickFormatter={() => ''}
                    />
                  </RechartsLineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
