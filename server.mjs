import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = 5173;

const app = express();

// Set proper MIME types and CORS for all static assets
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const ext = path.extname(req.path).toLowerCase();
  if (ext === '.js') res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
  else if (ext === '.json') res.setHeader('Content-Type', 'application/json; charset=utf-8');
  else if (ext === '.css') res.setHeader('Content-Type', 'text/css; charset=utf-8');
  next();
});

// Serve static files from root directory
app.use(express.static(__dirname, {
  index: false, // handle index manually for SPA fallback
  dotfiles: 'ignore',
}));

// SPA fallback — all non-file requests get index.html (Nuxt client-side routing)
app.get('*', (req, res) => {
  // If it looks like a file request but doesn't exist, still serve index.html
  const filePath = path.join(__dirname, req.path);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    return res.sendFile(filePath);
  }
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ BuildIT running at http://localhost:${PORT}`);
});
