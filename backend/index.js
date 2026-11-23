const fs = require('node:fs');
const mongoose = require('mongoose');
const { createApp } = require('./src/app');
async function main() {
  const uri = process.env.MONGODB_URI_FILE ? fs.readFileSync(process.env.MONGODB_URI_FILE, 'utf8').trim() : process.env.MONGODB_URI;
  if (!uri) throw new Error('Configure MONGODB_URI_FILE ou MONGODB_URI');
  mongoose.set('bufferCommands', false);
  await mongoose.connect(uri, { serverSelectionTimeoutMS: 5000, maxPoolSize: 5 });
  const schema = new mongoose.Schema({ text: { type: String, required: true, trim: true, maxlength: 500 }, completed: { type: Boolean, default: false } });
  const app = createApp({ Todo: mongoose.model('Todo', schema), checkDatabase: () => mongoose.connection.db.admin().ping(), version: process.env.APP_VERSION || 'local' });
  const server = app.listen(Number(process.env.PORT || 5000), '0.0.0.0', () => console.log(JSON.stringify({ event: 'api_ready' })));
  let stopping = false;
  const stop = () => {
    if (stopping) return;
    stopping = true;
    const timeout = setTimeout(() => process.exit(1), 10000).unref();
    server.close(async () => { await mongoose.disconnect(); clearTimeout(timeout); process.exit(0); });
    server.closeIdleConnections();
  };
  process.on('SIGTERM', stop); process.on('SIGINT', stop);
}
main().catch(() => {
  // Connection errors can contain credentials; never log the driver error.
  console.error(JSON.stringify({ event: 'startup_failed', message: 'Banco indisponivel ou configuracao invalida' }));
  process.exitCode = 1;
});
