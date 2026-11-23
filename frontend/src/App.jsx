import React, { useState, useEffect } from 'react';
import './App.css';
async function request(path = '', options) {
  const r = await fetch(`/todos${path}`, options);
  if (!r.ok) throw new Error('Não foi possível acessar as tarefas. Tente novamente.');
  return r.json();
}
export default function App() {
  const [todos, setTodos] = useState([]), [task, setTask] = useState('');
  const [error, setError] = useState(''), [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    request().then(data => { if (active) setTodos(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, []);
  const perform = async action => {
    setBusy(true); setError('');
    try { await action(); } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const add = e => {
    e.preventDefault(); if (!task.trim()) return;
    perform(async () => {
      const todo = await request('', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: task }) });
      setTodos(previous => [...previous, todo]); setTask('');
    });
  };
  const toggle = id => perform(async () => {
    const updated = await request(`/${id}`, { method: 'PATCH' });
    setTodos(previous => previous.map(todo => todo._id === id ? updated : todo));
  });
  const remove = id => perform(async () => {
    await request(`/${id}`, { method: 'DELETE' });
    setTodos(previous => previous.filter(todo => todo._id !== id));
  });
  return <main className="App">
    <h1>Lista de Tarefas</h1>
    <form onSubmit={add}>
      <input aria-label="Nova tarefa" placeholder="Adicione uma tarefa" maxLength={500} value={task} onChange={e => setTask(e.target.value)} disabled={busy} />
      <button disabled={busy}>Adicionar</button>
    </form>
    {error && <p role="alert">{error}</p>}
    <ul>{todos.map(todo => <li key={todo._id}>
      <button className="task" disabled={busy} style={{ textDecoration: todo.completed ? 'line-through' : 'none' }} onClick={() => toggle(todo._id)} aria-label={`${todo.completed ? 'Reabrir' : 'Concluir'} ${todo.text}`}>{todo.text}</button>
      <button disabled={busy} onClick={() => remove(todo._id)} aria-label={`Excluir ${todo.text}`}>Excluir</button>
    </li>)}</ul>
  </main>;
}
