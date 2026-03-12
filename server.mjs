import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.join(__dirname, 'site');
const PORT = 5173;

const app = express();

// Serve static files with proper MIME types
app.use((req, res, next) => {
  // map clean URLs to index.html for SPA routing (Nuxt handles routing in JS)
  const url = req.path;
  const filePath = path.join(SITE, url);

  // Check if file exists
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    return next();
  }
  // Check with index.html
  const indexPath = path.join(SITE, url, 'index.html');
  if (fs.existsSync(indexPath)) {
    return res.sendFile(indexPath);
  }
  // Fallback to root index.html for SPA routing
  if (!url.startsWith('/_nuxt') && !url.startsWith('/media') && !url.startsWith('/polyfills') && !url.startsWith('/assets')) {
    return res.sendFile(path.join(SITE, 'index.html'));
  }
  next();
});

app.use(express.static(SITE, {
  setHeaders(res, filePath) {
    if (filePath.endsWith('.js')) {
      res.setHeader('Content-Type', 'application/javascript');
    }
    if (filePath.endsWith('.json')) {
      res.setHeader('Content-Type', 'application/json');
    }
    // Allow fonts from any origin
    res.setHeader('Access-Control-Allow-Origin', '*');
  }
}));

// 404 fallback → index.html (SPA)
app.use((req, res) => {
  res.sendFile(path.join(SITE, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ BuildIT site running at http://localhost:${PORT}`);
});
