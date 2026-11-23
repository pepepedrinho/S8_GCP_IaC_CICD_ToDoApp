const fs = require('fs');
const password = fs.readFileSync('/run/secrets/mongo_app_password', 'utf8').trim();
if (password.length < 24) throw new Error('Application password is too short');
db = db.getSiblingDB('todo-app');
db.createUser({ user: 'todo', pwd: password, roles: [{ role: 'readWrite', db: 'todo-app' }] });
db.todos.insertMany([{ text: 'Estudar Cloud', completed: true }, { text: 'Validar infraestrutura', completed: false }, { text: 'Testar backup e restauracao', completed: false }]);
