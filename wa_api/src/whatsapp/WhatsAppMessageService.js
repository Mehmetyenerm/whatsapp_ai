import {downloadMediaMessage, getContentType, normalizeMessageContent, proto} from "baileys";
import path from "node:path";
import fs from "node:fs/promises";
import P from "pino";
import 'dotenv/config';
import { convertToOpus } from "../dependencys.js"

export class WhatsAppMessageService{
    
    constructor(whatsappClient){
        this.whatsappClient = whatsappClient 
        this.mediaPath = path.resolve(process.cwd(), process.env.MEDIA_PATH)
        this.logger = P({level:process.env.LOG_LEVEL}).child({module: "WhatsAppMessageService"})
    }
    
    getSocket(){
        const sock = this.whatsappClient.getSocket();
        if (!sock){ 
            throw new Error("WhatsApp socket is not avaible");
        }
        return sock;
    }

    async sendMessage(jid, text) {
        const sock = this.getSocket();
        if(!sock){
            throw new Error("Whatsapp socket not supported")
        }
        this.logger.info("WhatsApp message sent");
        return await sock.sendMessage(jid, {text})
    }
    
    async sendImage(jid, filePath, caption = "") {
        const sock = this.getSocket();
        return await sock.sendMessage(
            jid,
            {
                image: {
                    url: filePath
                },
                caption
            }
        );
    }

    async sendAudio(jid, filePath) {
        const sock = this.getSocket();
        const inputAbsulutePath = path.resolve(filePath);
        const convertedPath = await convertToOpus(inputAbsulutePath);
        const absolutePath = path.resolve(convertedPath);
        return await sock.sendMessage(
            jid,
            {
                audio: {
                    url: absolutePath
                },
                mimetype: "audio/ogg; codecs=opus",
                ptt: true
            }
        );
    }

    async sendDocument(jid, filePath, fileName, mimetype) {
        const sock = this.getSocket();
        return await sock.sendMessage(
            jid,
            {
                document: {
                    url: filePath
                },
                fileName,
                mimetype
            }
        );
    }
    
    async handleMessagesUpsert({messages, type})  {
        if (type === "notify") { // new messages
            for (const message of messages) {
                try {
                    const key = message.key; // mesaj key bilgisi
                    if(message.message?.imageMessage){
                        console.log("Image Received");
                        const filePath = await this.handleImage(message);
                        await this.sendToWApi(message, filePath);
                        continue;
                    }
                    if(message.message?.audioMessage){
                        console.log("Audio Received");
                        const filePath = await this.handleAudio(message);
                        await this.sendToWApi(message, filePath);
                        continue;
                    }
                    if(message.message?.documentMessage){
                        console.log("Document Received");
                        const filePath = await this.handleDocument(message);
                        await this.sendToWApi(message, filePath);
                        continue;
                    }
                    if(message.message?.videoMessage){
                        console.log("Video Received");
                        const filePath = await this.handleVideo(message);
                        await this.sendToWApi(message, filePath);
                        continue;
                    }
                    //if (process.env.FASTAPI_OPEN === true){await this.sendToWApi(message);}
                    await this.sendToWApi(message);
                }catch(err) {
                    this.logger.error({error:err}, "Mesaj işlenirken hata oluştu");
                }
            }
        } else { // old already seen / handled messages
            // handle them however you want to
        }
    }
    
    async handleImage(message) {
        const sock = this.getSocket();
        const buffer = await downloadMediaMessage(message, "buffer", {},
            {
                logger: P({ level: "silent" }),
                reuploadRequest: sock.updateMediaMessage.bind(sock)
            });
        await fs.mkdir(this.mediaPath, { recursive: true });
        const fileName = `${message.key.id}.jpg`;
        const filePath = path.join(this.mediaPath, fileName); //path.resolve(process.cwd(), process.env.AUTH_PATH);
        await fs.writeFile(filePath, buffer);
        return filePath;
    }
    async handleAudio(message) {
        const sock = this.getSocket();
        const buffer = await downloadMediaMessage(message, "buffer", {},
            {
                logger: P({ level: "silent" }),
                reuploadRequest: sock.updateMediaMessage.bind(sock)
            });
        await fs.mkdir(this.mediaPath, { recursive: true });
        const fileName = `${message.key.id}.ogg`;
        const filePath = path.join(this.mediaPath, fileName);
        await fs.writeFile(filePath, buffer);
        return filePath;
    }
    async handleDocument(message) {
        const sock = this.getSocket();
        const document = message.message?.documentMessage;
        const buffer = await downloadMediaMessage(message, "buffer", {},
            {
                logger: P({ level: "silent" }),
                reuploadRequest: sock.updateMediaMessage.bind(sock)
            });
        await fs.mkdir(this.mediaPath, { recursive: true });
        const fileName = document?.fileName || `${message.key.id}.bin`;
        const filePath = path.join(this.mediaPath, fileName);
        await fs.writeFile(filePath, buffer);
        return filePath;
    }
    async handleVideo(message) {
        const sock = this.getSocket();
        const buffer = await downloadMediaMessage(message, "buffer", {},
            {
                logger: P({ level: "silent" }),
                reuploadRequest: sock.updateMediaMessage.bind(sock)
            });
        await fs.mkdir(this.mediaPath, { recursive: true });
        const fileName = `${message.key.id}.mp4`;
        const filePath = path.join(this.mediaPath, fileName);
        await fs.writeFile(filePath, buffer);
        return filePath;
    }

    createMessagePayload(message, filePath) {
        const key = message.key;
        const messageContent = message.message;
        let type = "Unknown";
        let text = null;
        if(messageContent?.conversation){
            type = "text";
            text = messageContent.conversation;
        }
        else if(messageContent?.extendedTextMessage?.text){
            type = "text";
            text = messageContent.extendedTextMessage.text;
        }
        else if(messageContent?.imageMessage){
            type = "image";
        }
        else if(messageContent?.audioMessage){
            type = "audio";
        }
        else if(messageContent?.videoMessage){
            type = "video";
        }
        else if(messageContent?.documentMessage){
            type = "document";
        }
        return {
            id: key.id,
            from_: key.remoteJid,
            fromMe: key.fromMe,
            type: type,
            text,
            filePath,
            timestamp: message.messageTimestamp,
        };
    }

    async postWithTimeout(url, data, timeout = 10000) {
        const controller = new AbortController();

        const timer = setTimeout(() => {
            controller.abort();
        }, timeout);

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": process.env.WEEBHOOK_API_KEY
                },
                body: JSON.stringify(data),
                signal: controller.signal
            });

            return response;
        } finally {
            clearTimeout(timer);
        }
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async sendToWApi(message, filePath = null) {
        const payload = this.createMessagePayload(message, filePath);
        const maxRetries = 5;
        for (let attempt =1 ; attempt <= maxRetries; attempt++) {
            try {
                this.logger.info(`Sending webhook...(${attempt}/${maxRetries})`);
                const response = await this.postWithTimeout( process.env.FASTAPI_ENDPOINT_URL, payload, 10000 );
                if (!response.ok) {
                    const errtext = await response.text();
                    if (!response.ok) {
                        this.logger.error(`Non-retryable error ${response.status}: ${errtext}`);
                        return;
                    }
                    throw new Error(`Fastify returned ${response.status}, ${errtext}`);
                }
                const result = await response.json();
                this.logger.info(`Message sent to FastApi: ${result} (attempt ${attempt})`);
                return result;
            }catch(error) {
                this.logger.error(`Failed to send message to FastApi : ${error}`);
                if(attempt === maxRetries){
                    this.logger.error(`Max retry count reached`);
                    return;
                }
                const delay = 1000 * Math.pow(2, attempt - 1);
                await this.sleep(delay);
            }
        }
    }
}