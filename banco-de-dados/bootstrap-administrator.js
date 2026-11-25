// Used only when normal administrator authentication failed. MongoDB's
// localhost exception allows this exclusively when NO users/roles exist.
// Existing users/passwords are never reset or removed.
const fs = require('fs');
db.getSiblingDB('admin').createUser({
  user: 'administrator',
  pwd: fs.readFileSync('/run/secrets/mongo_root_password', 'utf8').trim(),
  roles: [{ role: 'root', db: 'admin' }],
});
print('created');
