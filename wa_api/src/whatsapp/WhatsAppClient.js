import makeWASocket, {
    useMultiFileAuthState,
} from "baileys"
import P from "pino"
import path from "node:path";
import { EventEmitter } from "node:events";
import 'dotenv/config';
import { WhatsAppConnection } from "./WhatsAppConnection.js"
import { WhatsAppMessageService } from "./WhatsAppMessageService.js"
import fs from "fs";

export class WhatsAppClient extends EventEmitter{
    constructor () {
        super();
        this.sock = null;
        this.state = null;
        this.connection = new WhatsAppConnection(this);
        this.messageService = new WhatsAppMessageService(this);
        this.authPath = path.resolve(process.cwd(),'..', process.env.AUTH_PATH);
        this.logger = P({level:process.env.LOG_LEVEL}).child({module: "WhatsAppClient"})
        const ConnectionState = {
            CONNECTING:"Connecting",
            CONNECTED:"Connected",
            CLOSED:"Closed"
        };
    }

    async connect()  {
        if (this.state === "Connecting") {
            this.logger.warn("Connection already in progress");
            return 1;
        }
        this.state = "Connecting";
        try{
            const { state, saveCreds } = await useMultiFileAuthState(this.authPath,);
            this.sock = makeWASocket({
                auth: state,
                logger: this.logger,
                shouldSyncHistoryMessage: () => true,
                syncFullHistory: true,
            });
            this.sock.ev.on("creds.update", saveCreds);
            this.sock.ev.on("connection.update",(connectionUpdate) => {
                this.connection.handleConnectionUpdate(connectionUpdate);
                //console.log(Object.getOwnPropertyNames(
                //    Object.getPrototypeOf(this.sock.signalRepository.lidMapping)
                //),"----------------------------------------------");
            });
            this.sock.ev.on("messages.upsert", (messageUpdate) => this.messageService.handleMessagesUpsert(messageUpdate));
        }catch(err){
            this.state = "Closed";
            this.logger.error(err, "WhatsApp connection error");
            this.emit("error");
            throw err;
        }
    }

    getSocket(){ return this.sock }
    getState(){ return this.state }

    async clearAuthState(){
        try {
            await fs.promises.rm(this.authPath, { recursive: true, force: true });
            this.logger.info('Cleared Baileys auth state', { authPath: this.authPath });
        } catch (err) {
            this.logger.warn('Failed to clear Baileys auth state', {
                error: err instanceof Error ? err.message : String(err),
            });
        }
    }

    async disconnect(){
        try {
            await this.connection.disconnect();
            this.sock = null;
            return true;
        }catch(err){
            return err;
        }
    }

    async logout(){
        if (!this.sock) return 1;
        try {
            await this.sock?.logout();
            return true;
        } catch (err) {
            this.logger.warn('Baileys logout failed; ending socket', {
                error: err instanceof Error ? err.message : String(err),
            });
            //this.sock?.end(undefined);
            return err;
        }finally {
            this.sock = null;
            this.state = "Closed";
            //await this.clearAuthState();
        }
    }

    async waitUntilConnected(timeout=30000){
        if (this.state === "Connected") {
            return Promise.resolve();
        }
        return await new Promise((resolve, reject) => {
            const timer = setTimeout(()=>{
                this.connection.removeListener("connected", onConnected);
                reject(new Error(`WhatsApp Connection timed out`));
            }, timeout);
            const onConnected = async () => {
                clearTimeout(timer);
                resolve();
            };
            this.connection.once("connected", onConnected);
            this.connection.once("error", reject);
        });
    }

    isConnected(timeout) {
        if (this.state === "Connecting") {
            this.waitUntilConnected(timeout);
            return false;
        }
        else {
            return true;
        }
    }

    async toJid(to){
        if (to.includes("@")) return to; // zaten tam jid (g.us, s.whatsapp.net, lid)
        const digits = to.replace(/[^\d]/g, "");
        /*const lid = await this.sock.signalRepository.lidMapping.getLIDForPN(
            "905011408259@s.whatsapp.net"
        );
        console.log(to,"------------------------------------------------")
        console.log(lid,"------------------------------------------------")*/
        return `${digits}@lid`;
    }

    async sendMessage(jid, text){
        return await this.messageService.sendMessage(jid, text)
    }
    async sendImage(jid, filePath, caption){
        return await this.messageService.sendImage(jid, filePath,caption)
    }
    async sendAudio(jid, filePath){
        return await this.messageService.sendAudio(jid, filePath)
    }
    async sendDocument(jid, filePath, fileName, mimetype){
        return await this.messageService.sendDocument(jid, filePath, fileName, mimetype)
    }
    async getQr(){
        return this.connection.lastQr;
    }
}