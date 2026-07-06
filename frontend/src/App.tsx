import React, { useState, useEffect, Suspense } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { 
  Monitor, Terminal, BarChart2, Download, User, ChevronLeft, ChevronRight, Target 
} from 'lucide-react';

// Safe component wrapper class
class ErrorBoundary extends React.Component<{children: React.ReactNode, name: string}, {hasError: boolean}> {
  constructor(props: {children: React.ReactNode, name: string}) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: any) { return { hasError: true }; }
  componentDidCatch(error: any, errorInfo: any) { console.error("Component Error:", error, errorInfo); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full w-full bg-surface rounded-xl border border-red-500/30 p-8 text-center select-text">
          <h2 className="text-status-vetoed font-bold mb-2">Component Offline: {this.props.name}</h2>
          <p className="text-muted text-sm font-mono">The module failed to load or encountered a runtime error.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// Lazy load components
const MarketClocks = React.lazy(() => import('./components/MarketClocks').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">MarketClocks Module Missing</div> })));
const CommandCenter = React.lazy(() => import('./components/CommandCenter').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">CommandCenter Module Missing</div> })));
const AgentConsole = React.lazy(() => import('./components/AgentConsole').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">AgentConsole Module Missing</div> })));
const AnalyticsGallery = React.lazy(() => import('./components/AnalyticsGallery').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">AnalyticsGallery Module Missing</div> })));
const ExportHub = React.lazy(() => import('./components/ExportHub').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">ExportHub Module Missing</div> })));
const ArchitectProfile = React.lazy(() => import('./components/ArchitectProfile').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">ArchitectProfile Module Missing</div> })));
const ProjectProfile = React.lazy(() => import('./components/ProjectProfile').catch(() => ({ default: () => <div className="p-4 bg-red-900/20 text-status-vetoed font-mono">ProjectProfile Module Missing</div> })));

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [progressPhase, setProgressPhase] = useState('Core Idle');
  const [logs, setLogs] = useState<string[]>([]);
  
  // Lifted state configuration
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-31');
  const [historyLength, setHistoryLength] = useState(100);
  const [ticks, setTicks] = useState<any[]>([]);

  // Initialize output numeric metrics strictly as null
  const [metrics, setMetrics] = useState<{
    q_score: string | null;
    kurtosis: string | null;
    regime: string | null;
  }>({
    q_score: null,
    kurtosis: null,
    regime: 'OFFLINE'
  });

  const fetchMetrics = async () => {
    try {
      const res = await fetch('/api/metrics');
      if (res.ok) {
        const data = await res.json();
        if (data.regime === 'OFFLINE') {
          setMetrics({
            q_score: null,
            kurtosis: null,
            regime: 'OFFLINE'
          });
        } else {
          setMetrics({
            q_score: data.q_score || null,
            kurtosis: data.kurtosis || null,
            regime: data.regime || null
          });
        }
      }
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    }
  };

  const fetchTicks = async () => {
    try {
      const res = await fetch('/api/ticks?limit=5000');
      if (res.ok) {
        const data = await res.json();
        setTicks(data || []);
      }
    } catch (err) {
      console.error("Failed to fetch ticks:", err);
    }
  };

  // Removed auto-fetch on mount so that data is empty on fresh reload

  const handleStartPipeline = (start: string, end: string, isMock: boolean = false) => {
    setPipelineRunning(true);
    setLogs([]);
    setTicks([]);
    setMetrics({ q_score: null, kurtosis: null, regime: 'COMPUTING' });
    setProgressPhase('Spawning Python subprocess engine...');

    const eventSource = new EventSource(`/api/run?start=${start}&end=${end}${isMock ? '&mock=true' : ''}`);

    eventSource.onmessage = (event) => {
      const line = event.data;
      if (line.includes('[FINISHED]')) {
        eventSource.close();
        setPipelineRunning(false);
        setProgressPhase('Pipeline run complete 🏁');
        fetchMetrics();
        fetchTicks();
      } else {
        setLogs(prev => [...prev, line]);
        
        // Track subprocess phase
        if (line.includes("[DATA LOADER]")) {
          setProgressPhase("Phase 1: Ingesting Microstructure Ticks 🟢");
        } else if (line.includes("DataAnalystAgent")) {
          setProgressPhase("Phase 2: Data Analyst Scanning Noise 🟢");
        } else if (line.includes("LeadQuantAgent")) {
          setProgressPhase("Phase 3: Lead Quant Calculating Thresholds 🟢");
        } else if (line.includes("RiskOfficerAgent")) {
          setProgressPhase("Phase 4: Risk Officer Evaluating Toxicity 🟡");
        } else if (line.includes("MQL5SynthesizerAgent")) {
          setProgressPhase("Phase 5: Synthesizing MQL5 Production Code 🟢");
        }
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      eventSource.close();
      setPipelineRunning(false);
      setProgressPhase('Pipeline crashed or API bridge connection lost ❌');
    };
  };

  const LoadingFallback = () => (
    <div className="flex h-full w-full items-center justify-center text-bullion font-mono animate-pulse">
      LOADING MATRIX MODULE...
    </div>
  );

  return (
    <Tabs.Root defaultValue="monitor" className="flex h-screen w-screen overflow-hidden bg-graphite text-[#EDEEF0] font-sans select-text">
      {/* Sidebar navigation */}
      <aside 
        className={`bg-surface border-r border-[#333A45] flex flex-col justify-between transition-all duration-300 ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        } shrink-0`}
      >
        <div className="flex flex-col">
          {/* Brand header */}
          <div className="p-6 flex items-center justify-between border-b border-[#333A45]">
            {!sidebarCollapsed && (
              <div className="flex flex-col gap-0.5">
                <span className="font-bold text-bullion tracking-wider text-[11px] uppercase">The-Matrix-XAUUSD-Quant-Suite</span>
              </div>
            )}
            <button 
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1 rounded hover:bg-[#333A45] text-muted hover:text-primary transition-all focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              {sidebarCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
            </button>
          </div>

          {/* Navigation Trigger List */}
          <Tabs.List className="flex flex-col gap-2 p-4">
            <Tabs.Trigger 
              value="monitor"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <Monitor className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Command Center</span>}
            </Tabs.Trigger>

            <Tabs.Trigger 
              value="console"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <Terminal className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Agent Console</span>}
            </Tabs.Trigger>

            <Tabs.Trigger 
              value="analytics"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <BarChart2 className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Analytics Gallery</span>}
            </Tabs.Trigger>

            <Tabs.Trigger 
              value="export"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <Download className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Export Hub</span>}
            </Tabs.Trigger>

            <Tabs.Trigger 
              value="project"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <Target className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Project Vision</span>}
            </Tabs.Trigger>
            
            <Tabs.Trigger 
              value="profile"
              className="flex items-center gap-4 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider text-muted hover:text-primary hover:bg-[#333A45]/30 transition-all data-[state=active]:bg-bullion/10 data-[state=active]:text-bullion focus:ring-2 focus:ring-bullion focus:outline-none"
            >
              <User className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Architect Profile</span>}
            </Tabs.Trigger>
          </Tabs.List>
        </div>

        {/* Footer info */}
        <div className="p-6 border-t border-[#333A45] text-[10px] text-muted font-mono select-text">
          {!sidebarCollapsed ? (
            <div className="flex flex-col gap-1">
              <div>BUILD v4.0.0</div>
              <div>MATRIX SYSTEMS</div>
            </div>
          ) : (
            <span className="font-bold text-bullion">v4</span>
          )}
        </div>
      </aside>

      {/* Main Workspace Canvas */}
      <main className="flex-1 flex flex-col overflow-hidden bg-graphite">
        {/* Top Status Clocks Ribbon */}
        <ErrorBoundary name="MarketClocks">
          <Suspense fallback={<div className="h-12 bg-surface border-b border-[#333A45]" />}>
            <MarketClocks />
          </Suspense>
        </ErrorBoundary>

        {/* Dynamic Workspace content frame */}
        <div className="flex-1 overflow-y-auto p-8 relative select-text">
          <Tabs.Content value="monitor" className="outline-none h-full">
            <ErrorBoundary name="CommandCenter">
              <Suspense fallback={<LoadingFallback />}>
                <CommandCenter 
                  startDate={startDate}
                  setStartDate={setStartDate}
                  endDate={endDate}
                  setEndDate={setEndDate}
                  historyLength={historyLength}
                  setHistoryLength={setHistoryLength}
                  pipelineRunning={pipelineRunning}
                  progressPhase={progressPhase}
                  onStartPipeline={handleStartPipeline}
                />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>

          <Tabs.Content value="console" className="outline-none h-full">
            <ErrorBoundary name="AgentConsole">
              <Suspense fallback={<LoadingFallback />}>
                <AgentConsole logs={logs} />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>

          <Tabs.Content value="analytics" className="outline-none h-full">
            <ErrorBoundary name="AnalyticsGallery">
              <Suspense fallback={<LoadingFallback />}>
                <AnalyticsGallery 
                  metrics={metrics}
                  pipelineRunning={pipelineRunning}
                  ticks={ticks}
                />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>

          <Tabs.Content value="export" className="outline-none h-full">
            <ErrorBoundary name="ExportHub">
              <Suspense fallback={<LoadingFallback />}>
                <ExportHub hasData={ticks.length > 0} />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>

          <Tabs.Content value="project" className="outline-none h-full">
            <ErrorBoundary name="ProjectProfile">
              <Suspense fallback={<LoadingFallback />}>
                <ProjectProfile />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>

          <Tabs.Content value="profile" className="outline-none h-full">
            <ErrorBoundary name="ArchitectProfile">
              <Suspense fallback={<LoadingFallback />}>
                <ArchitectProfile />
              </Suspense>
            </ErrorBoundary>
          </Tabs.Content>
        </div>
      </main>
    </Tabs.Root>
  );
}