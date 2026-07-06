import React, { useState, useEffect } from 'react';
import { Download, FileText, Code2, AlertTriangle, ChevronDown, ChevronRight, Info } from 'lucide-react';

interface ExportHubProps {
  hasData: boolean;
}

export default function ExportHub({ hasData }: ExportHubProps) {
  const [mqhCode, setMqhCode] = useState('');
  const [reportMarkdown, setReportMarkdown] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    if (!hasData) return;
    const fetchArtifacts = async () => {
      try {
        setLoading(true);
        const mqhRes = await fetch('/api/download/mqh');
        if (mqhRes.ok) {
          const mqh = await mqhRes.text();
          setMqhCode(mqh);
        }

        const reportRes = await fetch('/api/download/report');
        if (reportRes.ok) {
          const report = await reportRes.text();
          setReportMarkdown(report);
        }
      } catch (err) {
        console.error("Failed to fetch artifacts from API bridge:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchArtifacts();
  }, [hasData]);

  const handleDownload = (type: 'mqh' | 'report') => {
    window.open(`/api/download/${type}`);
  };


  if (loading) {
    return (
      <div className="glass-panel rounded-xl p-8 flex items-center justify-center text-muted select-text">
        <span className="animate-spin mr-3">⌛</span> Loading Production Artifacts...
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="glass-panel rounded-xl p-8 flex flex-col items-center justify-center text-center text-muted select-text min-h-[400px]">
        <AlertTriangle className="w-8 h-8 text-bullion mb-3" />
        <h4 className="font-bold text-primary mb-1 uppercase tracking-wider">Waiting for data</h4>
        <p className="text-xs max-w-sm text-gray-400">
          Normally, the codes are already written, but right now the system is on standby. Please navigate to the Command Center and <strong>start the agent</strong>!
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full items-start select-text">
      {/* Column A: MQL5 Source */}
      <div className="glass-panel rounded-xl p-6 flex flex-col gap-4">
        <div className="flex items-center gap-2 pb-2 border-b border-line-hairline">
          <Code2 className="w-4 h-4 text-bullion" />
          <h3 className="font-bold text-primary text-sm uppercase tracking-wider">Production MQL5 Source</h3>
        </div>

        <div className="bg-[#1C2028] border border-[#2A2E37] rounded-lg p-4 flex flex-col gap-2 relative overflow-hidden">
          <div className="absolute left-0 top-0 w-1 h-full bg-bullion opacity-50"></div>
          <div className="flex items-start gap-3">
            <Info className="w-4 h-4 text-bullion mt-0.5 flex-shrink-0" />
            <div className="text-xs text-muted leading-relaxed font-sans">
              <strong className="text-primary block mb-1">Generated HFT Tick Filter (.MQH)</strong>
              This header file contains the optimal Hampel and Kalman filter thresholds specifically calibrated by the Quant Core agents. 
              To deploy this in your live trading environment:
              <ul className="list-disc ml-4 mt-2 space-y-1 text-gray-400">
                <li>Download the file and place it inside your MetaTrader 5 Include directory: 
                  <br /><code className="text-[10px] bg-black/30 px-1 py-0.5 rounded text-bullion">%AppData%\MetaQuotes\Terminal\&lt;ID&gt;\MQL5\Include\</code>
                </li>
                <li>In your main Expert Advisor (.mq5), add: <code className="text-[10px] bg-black/30 px-1 py-0.5 rounded text-bullion">#include &lt;HFT_Tick_Factory.mqh&gt;</code></li>
                <li>Call <code className="text-[10px] bg-black/30 px-1 py-0.5 rounded text-bullion">HFT_Tick_Filter::ProcessTick()</code> within your <code className="text-[10px] bg-black/30 px-1 py-0.5 rounded text-bullion">OnTick()</code> function.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={() => setShowCode(!showCode)}
            className="flex items-center justify-between w-full p-3 bg-[#020408] border border-white/5 rounded-lg text-left hover:bg-white/5 transition-colors"
          >
            <span className="text-xs font-mono text-gray-300">View Source Code ({mqhCode.split('\n').length} lines)</span>
            {showCode ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
          
          {showCode && (
            <div className="bg-[#020408] rounded-lg p-4 max-h-[500px] overflow-y-auto border border-white/5 font-mono text-xs select-text">
              <pre className="text-gray-200 leading-relaxed whitespace-pre select-text">{mqhCode}</pre>
            </div>
          )}
        </div>

        <button
          onClick={() => handleDownload('mqh')}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-xs uppercase tracking-widest text-[#070A0F] bg-gradient-to-r from-bullion to-[#AA7C11] hover:scale-[1.02] active:scale-100 hover:shadow-[0_0_15px_rgba(201,161,90,0.4)] transition-all"
        >
          <Download className="w-4 h-4" />
          Download Expert Advisor Engine .MQH
        </button>
      </div>

      {/* Column B: Audit Compliance Report */}
      <div className="glass-panel rounded-xl p-6 flex flex-col gap-4">
        <div className="flex items-center gap-2 pb-2 border-b border-line-hairline">
          <FileText className="w-4 h-4 text-bullion" />
          <h3 className="font-bold text-primary text-sm uppercase tracking-wider">HFT Compliance Digest</h3>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={() => setShowReport(!showReport)}
            className="flex items-center justify-between w-full p-3 bg-[#020408] border border-white/5 rounded-lg text-left hover:bg-white/5 transition-colors"
          >
            <span className="text-xs font-mono text-gray-300">View Execution Report ({reportMarkdown.split('\n').length} lines)</span>
            {showReport ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
          
          {showReport && (
            <div className="bg-[#020408] rounded-lg p-6 max-h-[500px] overflow-y-auto border border-white/5 text-xs text-primary select-text leading-relaxed font-sans overflow-x-hidden">
              <div className="prose prose-invert prose-xs max-w-none select-text">
                {reportMarkdown.split('\n').map((line, idx) => {
                  if (line.startsWith('# ')) return <h1 key={idx} className="text-lg font-bold text-bullion mt-4 mb-2">{line.replace('# ', '')}</h1>;
                  if (line.startsWith('## ')) return <h2 key={idx} className="text-base font-bold text-bullion mt-3 mb-1.5">{line.replace('## ', '')}</h2>;
                  if (line.startsWith('### ')) return <h3 key={idx} className="text-sm font-bold text-primary mt-2 mb-1">{line.replace('### ', '')}</h3>;
                  if (line.startsWith('- ') || line.startsWith('* ')) return <li key={idx} className="ml-4 list-disc text-gray-400 select-text">{line.substring(2)}</li>;
                  return <p key={idx} className="text-gray-200 mb-2 font-mono select-text">{line}</p>;
                })}
              </div>
            </div>
          )}
        </div>

        <button
          onClick={() => handleDownload('report')}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-xs uppercase tracking-widest text-status-approved border-2 border-status-approved hover:bg-status-approved/15 hover:shadow-[0_0_15px_rgba(78,158,110,0.3)] transition-all"
        >
          <Download className="w-4 h-4" />
          Export Audit Summary .MD
        </button>
      </div>
    </div>
  );
}
