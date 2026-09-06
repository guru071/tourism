FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

COPY package*.json ./
RUN npm ci || npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
