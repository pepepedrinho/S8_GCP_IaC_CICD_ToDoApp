const express = require('express');
function createApp({ Todo, checkDatabase, version = 'local' }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: '8kb' }));
  app.use((req, res, next) => {
    const started = Date.now();
    res.on('finish', () => console.log(JSON.stringify({ event: 'request', method: req.method, route: req.route?.path || 'unmatched', status: res.statusCode, duration_ms: Date.now() - started })));
    next();
  });
  app.get('/health/live', (_req, res) => res.json({ status: 'ok', version }));
  app.get('/health/ready', async (_req, res) => {
    let timer;
    try {
      await Promise.race([checkDatabase(), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('timeout')), 2000); })]);
      res.json({ status: 'ready', database: 'ok', version });
    } catch { res.status(503).json({ status: 'unavailable', database: 'unavailable', version }); }
    finally { clearTimeout(timer); }
  });
  app.get('/todos', async (_req, res) => res.json(await Todo.find().lean()));
  app.post('/todos', async (req, res) => {
    const text = typeof req.body?.text === 'string' ? req.body.text.trim() : '';
    if (!text || text.length > 500) return res.status(400).json({ message: 'Informe uma tarefa de 1 a 500 caracteres' });
    res.status(201).json(await Todo.create({ text, completed: false }));
  });
  app.param('id', (req, res, next, id) => {
    if (!/^[a-f\d]{24}$/i.test(id)) return res.status(400).json({ message: 'ID invalido' });
    next();
  });
  app.patch('/todos/:id', async (req, res) => {
    // Atomic toggle preserves the original method and behavior.
    const todo = await Todo.findByIdAndUpdate(req.params.id, [{ $set: { completed: { $not: '$completed' } } }], { new: true, updatePipeline: true });
    if (!todo) return res.status(404).json({ message: 'Tarefa nao encontrada' });
    res.json(todo);
  });
  app.delete('/todos/:id', async (req, res) => {
    if (!await Todo.findByIdAndDelete(req.params.id)) return res.status(404).json({ message: 'Tarefa nao encontrada' });
    res.json({ message: 'Tarefa excluida com sucesso' });
  });
  app.use((_req, res) => res.status(404).json({ message: 'Rota nao encontrada' }));
  app.use((err, _req, res, _next) => {
    const status = err.type === 'entity.too.large' ? 413 : err instanceof SyntaxError ? 400 : 503;
    res.status(status).json({ message: status === 503 ? 'Servico temporariamente indisponivel' : 'Requisicao invalida' });
  });
  return app;
}
module.exports = { createApp };
