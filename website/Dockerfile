# Build stage
FROM node:18 AS build
WORKDIR /app

# Install pnpm with corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Prepare pnpm dependencies using lockfile, patches and docker cache
COPY pnpm-lock.yaml . 

# Install and build the app
COPY . .


RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store pnpm install --reporter=default
RUN pnpm build

# Production stage
FROM node:18 AS production
WORKDIR /app

# Create a non-root user and home directory
RUN groupadd -g 10001 nuxt && \
  useradd -u 10001 -g nuxt nuxt && \
  mkdir -p /home/nuxt && \
  chown nuxt:nuxt /home/nuxt

# Copy the built app from the build stage
COPY --from=build /app ./

# Temporarily switch to root user to fix permissions
USER root

# Optimizing chmod and chown: Apply only to built files
RUN chmod -R 755 /app/.output && chown -R nuxt:nuxt /app/.output

# Switch to the non-root user
USER nuxt:nuxt

# Set the environment to production
ENV NODE_ENV=production
ENV VITE_API_URL=$VITE_API_URL

# Expose the port
EXPOSE 3000

# Start the app with PM2
CMD ["npm", "run", "start"]
