FROM node:12.18.2-alpine

WORKDIR usr/app/

COPY bundles-src ./
COPY package.json ./
COPY package-lock.json ./

RUN npm ci --dev
