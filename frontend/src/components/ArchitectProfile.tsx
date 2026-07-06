import React from 'react';

const GithubIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
  </svg>
);

const KaggleIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
    <path d="M18.825 23.859c-.022.092-.117.141-.281.141h-3.139c-.187 0-.351-.082-.492-.248l-5.178-5.641-1.453 1.359v4.272c0 .164-.094.246-.281.246H5.063c-.187 0-.281-.082-.281-.246V.268c0-.187.094-.281.281-.281h2.938c.187 0 .281.094.281.281v15.22l5.74-5.945c.141-.164.305-.246.492-.246h3.209c.164 0 .258.058.281.176.023.117-.035.211-.176.281l-5.459 5.383 5.764 8.414c.141.117.187.211.141.281z"/>
  </svg>
);

const EmailIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
    <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
  </svg>
);

export default function ArchitectProfile() {
  return (
    <div className="glass-panel rounded-xl p-8 max-w-4xl mx-auto select-text">
      <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-8 items-center">
        {/* Left Side: Profile Photo */}
        <div className="flex justify-center relative group">
          <div className="w-56 h-64 rounded-xl border-2 border-bullion shadow-[0_0_30px_rgba(201,161,90,0.4)] overflow-hidden relative transition-transform duration-500 hover:-translate-y-1">
            <img 
              src="/amir_profile.jpg" 
              alt="Amir Mazaheri" 
              className="w-full h-full object-cover object-top filter contrast-125 saturate-50 group-hover:saturate-100 transition-all duration-700 scale-105 group-hover:scale-100" 
            />
            <div className="absolute inset-0 ring-1 ring-inset ring-white/10 pointer-events-none rounded-xl"></div>
            <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-[#020408] via-[#020408]/70 to-transparent pt-12 pb-3 px-4 text-center">
              <span className="text-[10px] text-bullion tracking-[0.25em] font-bold font-mono uppercase bg-bullion/10 px-2 py-1 rounded border border-bullion/30 shadow-[0_0_10px_rgba(201,161,90,0.2)]">
                Matrix Core Leader
              </span>
            </div>
          </div>
        </div>

        {/* Right Side: Credentials */}
        <div className="flex flex-col">
          <h2 className="text-3xl font-extrabold text-bullion tracking-wide">Amir Mazaheri</h2>
          <h4 className="text-sm font-medium italic text-muted mt-1 uppercase tracking-wider">
            IT Engineer & Algorithmic Systems Engineer
          </h4>

          <div className="h-px bg-[#2A2E37]/50 my-6" />

          <p className="text-base text-gray-300 leading-8 tracking-wide font-light text-justify mb-8">
            I am an IT engineer specializing in building high-performance trading robots and quantitative systems. Architecting zero-latency multi-agent cognitive frameworks, real-tick filtration algorithms, and institutional network microstructures for commodity derivative execution.
          </p>

          {/* Action Footer Badge Links */}
          <div className="flex flex-wrap gap-3 font-mono text-xs">
            <a 
              href="mailto:amir.mazaherii1995@gmail.com" 
              className="flex items-center gap-2 px-4 py-2 bg-[#14161A] border border-bullion/30 hover:border-bullion rounded text-bullion hover:bg-bullion/5 transition-all focus:ring-2 focus:ring-bullion focus:outline-none"
              aria-label="Send email to Amir Mazaheri"
            >
              <EmailIcon />
              <span>Email Desk</span>
            </a>
            <a 
              href="https://github.com/Amirmzhry/The-Matrix-XAUUSD-Quant-Suite" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="flex items-center gap-2 px-4 py-2 bg-[#14161A] border border-bullion/30 hover:border-bullion rounded text-bullion hover:bg-bullion/5 transition-all focus:ring-2 focus:ring-bullion focus:outline-none"
              aria-label="View the GitHub Source repository"
            >
              <GithubIcon />
              <span>GitHub Source</span>
            </a>
            <a 
              href="https://www.kaggle.com/amirmzhry" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="flex items-center gap-2 px-4 py-2 bg-[#14161A] border border-bullion/30 hover:border-bullion rounded text-bullion hover:bg-bullion/5 transition-all focus:ring-2 focus:ring-bullion focus:outline-none"
              aria-label="Connect with Amir Mazaheri on Kaggle"
            >
              <KaggleIcon />
              <span>Kaggle Profile</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
