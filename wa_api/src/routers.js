import {opts, optsText, optsFile, optsUser } from "./schemas.js"
import {WhatsAppClient} from "./whatsapp/WhatsAppClient.js"

export default async function (app) {

    const whatsapp = new WhatsAppClient();

    app.get('/',opts, async function (request, reply) {
        return { hello: 'world' }
    })

    app.get('/qr', async function (request, reply) {
        const dataUrl = await app.whatsapp.getQr();

        if (!dataUrl?.startsWith("data:image")) {
            return reply.code(404).send("QR henüz oluşturulmadı.");
        }

        const [, base64] = dataUrl.split(",");

        reply
            .type("image/png")
            .send(Buffer.from(base64, "base64"));
    })

    app.post('/message/text', optsText, async function (request, reply) {
        await app.whatsapp.isConnected()
        try {
            const { to, message } = request.body
            if (!to || !message) {
                return reply.code(400).send({error: "to and message are required"});
            }
            const jid = await app.whatsapp.toJid(String(to));
            const result = await app.whatsapp.sendMessage(jid, message)
            return {
                success: true,
                messageId: result?.key?.id
            }
        }catch(err) {
            request.log.error(err);
            return reply.code(500).send({
                success: false,
                error: err.message
            });
        }
    })

    app.post('/message/media', optsFile, async function (request, reply) {
        await app.whatsapp.isConnected()
        try {
            const { to, filePath } = request.body
            if (!to || !filePath) {
                return reply.code(400).send({error: "to and file path are required"});
            }
            const jid = await app.whatsapp.toJid(String(to));
            let result
            if (filePath.endsWith(".jpg")) {
                result = await app.whatsapp.sendImage(jid, filePath)
            }
            else if (filePath.endsWith(".ogg")) {
                result = await app.whatsapp.sendAudio(jid, filePath)
            }
            else {
                return reply.code(400).send({ success: false, error: "Unsupported file type"});
            }
            return { success: true, messageId: result?.key?.id }
        }catch(err) {
            request.log.error(err);
            return reply.code(500).send({ success: false, error: err.message});
        }
    })

    app.post('/message/image', optsFile, async function (request, reply) {
        try {
            const { to, filePath } = request.body
            if (!to || !filePath) {
                return reply.code(400).send({error: "to and file path are required"});
            }
            const jid = to.includes("@s.whatsapp.net") ? to: `${to}@s.whatsapp.net`;
            const result = await app.whatsapp.sendImage(jid, filePath)
            return {
                success: true,
                messageId: result?.key?.id
            }
        }catch(err) {
            request.log.error(err);
            return reply.code(500).send({
                success: false,
                error: err.message
            });
        }
    })

    app.post('/message/audio', optsFile, async function (request, reply) {
        await app.whatsapp.isConnected()
        try {
            const { to, filePath} = request.body
            if (!to || !filePath) {
                return reply.code(400).send({error: "to and file path are required"});
            }
            const jid = await app.whatsapp.toJid(String(to));
            const result = await app.whatsapp.sendAudio(jid, filePath)
            return {
                success: true,
                messageId: result?.key?.id
            }
        }catch(err) {
            request.log.error(err);
            return reply.code(500).send({
                success: false,
                error: err.message
            });
        }
    })

    app.get('/user/logout',optsUser, async function (request, reply) {
        const result = await app.whatsapp.logout();
        if(result === true){
            return reply.code(200).send({msg:"success"});
        }
        else if (result === 1){
            return reply.code(200).send({msg:"already logged out"});
        }
        else{
            return reply.code(400).send({msg:"unable to logged out", result});
        }
    })

    app.get('/user/disconnect',optsUser, async function (request, reply) {
        const result = await app.whatsapp.disconnect();
        if(result === true){
            return reply.code(200).send({msg:"success"});
        }
        else{
            return reply.code(400).send({msg:"unable to logged out", result});
        }
    })

    app.get('/user/connect',optsUser, async function (request, reply) {
        try {
            await app.whatsapp.connect();

            return reply.code(200).send({
                msg: "Success",
                state: app.whatsapp.getState()
            });

        } catch(err) {
            request.log.error(err);

            return reply.code(400).send({
                msg:"unable to connect",
                error: err.message
            });
        }
    })
}