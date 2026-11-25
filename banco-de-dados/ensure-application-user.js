const fs = require('fs');
db.getSiblingDB('admin').auth('administrator', fs.readFileSync('/run/secrets/mongo_root_password', 'utf8').trim());
const applicationDb = db.getSiblingDB('todo-app');
if (!applicationDb.getUser('todo')) {
  applicationDb.createUser({
    user: 'todo',
    pwd: fs.readFileSync('/run/secrets/mongo_app_password', 'utf8').trim(),
    roles: [{ role: 'readWrite', db: 'todo-app' }],
  });
  if (applicationDb.todos.countDocuments({}) === 0) {
    applicationDb.todos.insertMany([
      { text: 'Estudar Cloud', completed: true },
      { text: 'Validar infraestrutura', completed: false },
      { text: 'Testar backup e restauracao', completed: false },
    ]);
  }
  print('created');
} else {
  print('existing');
}
