FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* ./

# Install dependencies
RUN npm install

# Copy app code
COPY src ./src
COPY public ./public 2>/dev/null || true
COPY next.config.ts tsconfig.json tailwind.config.ts postcss.config.js ./

EXPOSE 3000

CMD ["npm", "run", "dev"]
