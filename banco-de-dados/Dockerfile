FROM mongo:8.0
COPY init-mongo.js /docker-entrypoint-initdb.d/10-todo.js
COPY healthcheck.sh /usr/local/bin/todo-mongo-health
