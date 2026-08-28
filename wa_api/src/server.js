import Fastify from 'fastify'
import fs from 'node:fs';
import path from 'node:path';
import swagger from '@fastify/swagger';
import swaggerUI from '@fastify/swagger-ui';
import dotenv from 'dotenv';
import { fileURLToPath } from 'node:url';
import { WhatsAppClient } from "./whatsapp/WhatsAppClient.js"
import routers from "./routers.js"

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

dotenv.config({
    path: path.join(PROJECT_ROOT, '.env')
});

console.log("path: ",path.join(PROJECT_ROOT, '.env'), "proje_root: ", PROJECT_ROOT)

const required = ["AUTH_PATH", "MEDIA_PATH", "FASTAPI_ENDPOINT_URL", "API_HOST", "API_PORT"];
for (const key of required) {
    if (!process.env[key]) throw new Error(`Eksik ortam değişkeni: ${key}`);
}

//---------------------------wa connection
const whatsapp = new WhatsAppClient();

//---------------------------api config
const app = Fastify({
    http2: true,
    https: {
        allowHTTP1: true,
        key: fs.readFileSync(path.join(PROJECT_ROOT, 'localhost-key.pem')),
        cert: fs.readFileSync(path.join(PROJECT_ROOT, 'localhost.pem'))
    },
    logger: true,
})

app.decorate("whatsapp", whatsapp);// whatsapp nesnesinin routers.js den erişilmesi için
//------------------------------swagger
await app.register(swagger, {
    openapi: {
        info: {
            title: 'WhatsApp API',
            description: 'WhatsApp Message API',
            version: '1.0.0'
        },
        servers: [
            {
                url: `https://${process.env.API_HOST}:${process.env.API_PORT}`
            }
        ]
    }
});

await app.register(swaggerUI, {
    routePrefix: '/docs'
});

await app.register(routers);

app.listen({ port: process.env.API_PORT, host: process.env.API_HOST }, (err, address) => {
    if (err) throw err;
    app.log.info(`Docs published on ${address}/docs`)
})
await whatsapp.connect();