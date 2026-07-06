import React from 'react';
import { Target, Cpu, Briefcase, FileCode2, Info, ShieldCheck } from 'lucide-react';

export default function ProjectProfile() {
  return (
    <div className="w-full h-full flex flex-col gap-6 overflow-y-auto pr-2 pb-10 select-text">
      
      {/* Hero Banner */}
      <div className="glass-panel rounded-xl p-8 relative overflow-hidden border border-bullion/30 shadow-[0_0_40px_rgba(201,161,90,0.1)]">
        <div className="absolute top-0 right-0 w-64 h-64 bg-bullion/10 rounded-full blur-[100px] -mr-20 -mt-20"></div>
        <div className="relative z-10 flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#020408] border border-white/5 w-fit mb-2">
            <span className="w-2 h-2 rounded-full bg-bullion animate-pulse"></span>
            <span className="text-[10px] text-bullion tracking-[0.2em] font-mono uppercase">Executive Overview</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-wide">
            The Matrix: <span className="text-bullion">XAUUSD Quant Suite</span>
          </h1>
          <p className="text-sm md:text-base text-gray-400 max-w-3xl leading-relaxed mt-2">
            An autonomous, localized Multi-Agent cognitive framework designed to identify, debate, and eradicate high-frequency trading (HFT) noise and toxic order flow in commodity derivatives.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Project Vision & Value */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 border-t-4 border-t-blue-500 hover:bg-white/[0.02] transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Target className="w-5 h-5 text-blue-500" />
            </div>
            <h2 className="text-lg font-bold text-primary tracking-wider uppercase">Project Description & Value</h2>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed font-sans">
            Financial markets, particularly spot Gold (XAUUSD), are inundated with algorithmic noise, false breakouts, and spread-widening toxicity. <strong>The Matrix Quant Suite</strong> acts as a proactive shield against these microstructural anomalies. By mathematically filtering out toxic ticks before they reach execution logic, the system drastically reduces slippage, preserves institutional alpha, and prevents catastrophic drawdown during flash crashes.
          </p>
        </div>

        {/* Multi-Agent Architecture */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 border-t-4 border-t-purple-500 hover:bg-white/[0.02] transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-purple-500" />
            </div>
            <h2 className="text-lg font-bold text-primary tracking-wider uppercase">How It Works (Multi-Agent System)</h2>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed font-sans">
            The engine operates via a decentralized <strong>"Quant Council"</strong> of specialized AI agents working in a ReAct loop:
          </p>
          <ul className="text-xs text-gray-400 space-y-2 ml-2">
            <li className="flex items-start gap-2"><span className="text-purple-500 font-bold mt-0.5">1.</span> <strong>Data Analyst:</strong> Scans raw Dukascopy ticks for kurtosis and spread volatility.</li>
            <li className="flex items-start gap-2"><span className="text-purple-500 font-bold mt-0.5">2.</span> <strong>Lead Quant:</strong> Proposes algorithmic thresholds (Hampel/Kalman parameters).</li>
            <li className="flex items-start gap-2"><span className="text-purple-500 font-bold mt-0.5">3.</span> <strong>Risk Officer:</strong> Evaluates the logic; possesses absolute veto power over unsafe parameters.</li>
            <li className="flex items-start gap-2"><span className="text-purple-500 font-bold mt-0.5">4.</span> <strong>Synthesizer:</strong> Translates the approved logic into deployment-ready C++ code.</li>
          </ul>
        </div>

        {/* Business Value for Organizations */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 border-t-4 border-t-emerald-500 hover:bg-white/[0.02] transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-emerald-500" />
            </div>
            <h2 className="text-lg font-bold text-primary tracking-wider uppercase">Organizational Business Value</h2>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed font-sans">
            For proprietary trading firms and hedge funds, latency and execution quality are the defining metrics of success. This system automates the historically manual and labor-intensive process of quantitative research. 
            By bridging the gap between high-level AI reasoning and low-level execution logic, organizations can adapt to shifting market regimes in <strong>minutes rather than weeks</strong>, reducing developer overhead and significantly mitigating execution risk.
          </p>
        </div>

        {/* The Valuable Output */}
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 border-t-4 border-t-bullion hover:bg-white/[0.02] transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-bullion/10 flex items-center justify-center">
              <FileCode2 className="w-5 h-5 text-bullion" />
            </div>
            <h2 className="text-lg font-bold text-primary tracking-wider uppercase">The Production Artifact</h2>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed font-sans">
            Unlike traditional LLM wrappers that merely output text, this pipeline terminates by writing a compiled, syntactically perfect <strong>MetaQuotes Language 5 (.MQH)</strong> file. 
            This output artifact contains the highly calibrated filtering equations and is immediately ready to be injected into an institutional MetaTrader 5 Expert Advisor, crossing the boundary from theoretical AI research directly into live market execution.
          </p>
        </div>
      </div>

      {/* Strategic Disclaimer */}
      <div className="bg-[#1C2028] border-l-4 border-bullion rounded-r-lg p-6 flex flex-col gap-3 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-bullion" />
          <h3 className="font-bold text-primary text-sm uppercase tracking-wider">Vision & Scalability</h3>
        </div>
        <p className="text-xs text-gray-300 leading-relaxed font-sans">
          <strong>Note:</strong> This dashboard represents an initial demonstration version built to showcase the cognitive framework and pipeline architecture. 
          However, the true power of this system lies in its scalability. When configured with my proprietary architectures, advanced proprietary mathematical filtering systems, and specialized latency parameters, <strong>this framework can be adapted to create immense, measurable business value and distinct competitive advantages for financial organizations.</strong>
        </p>
      </div>

    </div>
  );
}
