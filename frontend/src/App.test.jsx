import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, test, expect, afterEach } from 'vitest';
import App from './App.jsx';
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
test('same-origin list, create, complete, reopen and delete', async () => {
  const todo = { _id: '1', text: 'Estudar', completed: false };
  const mock = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => [] })
    .mockResolvedValueOnce({ ok: true, json: async () => todo })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ ...todo, completed: true }) })
    .mockResolvedValueOnce({ ok: true, json: async () => todo })
    .mockResolvedValueOnce({ ok: true, json: async () => ({}) });
  vi.stubGlobal('fetch', mock);
  const user = userEvent.setup(); render(<App />);
  await waitFor(() => expect(mock).toHaveBeenCalledWith('/todos', undefined));
  await user.type(screen.getByLabelText('Nova tarefa'), 'Estudar');
  await user.click(screen.getByText('Adicionar'));
  await user.click(await screen.findByLabelText('Concluir Estudar'));
  await user.click(await screen.findByLabelText('Reabrir Estudar'));
  await user.click(await screen.findByLabelText('Excluir Estudar'));
  await waitFor(() => expect(screen.queryByText('Estudar')).not.toBeInTheDocument());
  expect(mock.mock.calls.map(c => c[1]?.method)).toEqual([undefined, 'POST', 'PATCH', 'PATCH', 'DELETE']);
});
test('network failure is visible', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false })); render(<App />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível');
});
