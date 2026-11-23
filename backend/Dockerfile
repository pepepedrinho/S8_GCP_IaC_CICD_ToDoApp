FROM node:24-alpine
ENV NODE_ENV=production NODE_OPTIONS=--max-old-space-size=160
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --chown=node:node index.js ./
COPY --chown=node:node src ./src
USER node
EXPOSE 5000
CMD ["node", "index.js"]
