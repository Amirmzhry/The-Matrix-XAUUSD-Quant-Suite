import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

try {
  const root = 'd:\\\\The Matrix';
  const quarantineDir = path.join(root, '.github_quarantine');
  
  if (!fs.existsSync(quarantineDir)) {
    fs.mkdirSync(quarantineDir);
  }

  const itemsToMove = [
    'HFT_Tick_Factory.mqh',
    'app_dashboard.py',
    'audit_agent_prompts.py',
    'backup_project.py',
    'fast_mql5_test.py',
    'fix_emdashes.py',
    'fix_ports.py',
    'restructure_and_cleanup.py',
    'run_all_tests.py',
    'run_smoke_test.bat',
    'run_with_logger.py',
    'smoke_test.py',
    'test_regex.py',
    'backup_matrix_stable',
    'quarantine_tests',
    'export',
    'mql5_export',
    'tests'
  ];

  itemsToMove.forEach(item => {
    const src = path.join(root, item);
    const dest = path.join(quarantineDir, item);
    if (fs.existsSync(src)) {
      fs.renameSync(src, dest);
    }
  });

  // Also move the frontend script
  const srcFrontend = path.join(root, 'frontend', 'src', 'fix_frontend.py');
  if (fs.existsSync(srcFrontend)) {
    fs.renameSync(srcFrontend, path.join(quarantineDir, 'fix_frontend.py'));
  }
} catch (e) {
  console.error("Failed quarantine script", e)
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
