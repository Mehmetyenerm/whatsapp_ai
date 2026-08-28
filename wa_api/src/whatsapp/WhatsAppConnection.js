import QRCode from "qrcode";
import {DisconnectReason} from "baileys";
import P from "pino";
import 'dotenv/config';
import { EventEmitter } from "node:events";
import fs from 'node:fs';
import path from "node:path";

export class WhatsAppConnection extends EventEmitter {
    
    constructor(whatsappClient){
        super();
        this.whatsappClient = whatsappClient;
        this.shouldReconnect = true;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectTimer = null;
        this.lastQr = null;
        this.connectedAt = 0;
        this.authPath = path.resolve(process.cwd(),'..', process.env.AUTH_PATH);
        this.logger = P({level:process.env.LOG_LEVEL}).child({module: "WhatsAppConnection"})
    }
    async handleConnectionUpdate(update)  {
        const {
            connection,
            lastDisconnect,
            qr
        } = update
        //qr
        if (qr) {
            //this.handleQrCode(qr);
            // as an example, this prints the qr code to the terminal
            this.lastQr = await QRCode.toDataURL(qr);
            //console.log(await QRCode.toString(qr, {type: 'terminal'}));
        }
        //baglanti bilgi msj.
        if (connection === "connecting") {
            this.whatsappClient.state = "Connecting";
            this.logger.info("Whatsapp connecting");
        }
        if (connection === "open") {
            this.logger.info("Whatsapp connected")
            this.whatsappClient.state = "Connected"
            this.connectedAt = Math.floor(Date.now() / 1000) - 10;
            this.emit("connected");
            this.lastQr = null;
            this.reconnectAttempts = 0 // basarılı olunca reconnect sifirlanir
        }

        if (connection === "close") {
            const statusCode = lastDisconnect?.error?.output?.statusCode
            this.logger.error(statusCode, "WhatsApp connection closed")
            this.whatsappClient.state = "Closed"
            this.lastQr = null;
            this.emit("disconnected");

            if (statusCode === DisconnectReason.restartRequired) {
                this.logger.info("WhatsApp requires socket restart")
                this.scheduleReconnect()
                return
            }
            if (statusCode === DisconnectReason.loggedOut) {
                this.logger.info("WhatsApp user logged out");
                this.sock = null;
                await this.clearAuthState();
                this.shouldReconnect = false;
                return
            }
            this.logger.error("Unexpected disconnect.")
            this.scheduleReconnect()
        }
    }

    scheduleReconnect() {
        if (!this.shouldReconnect) { return; } // reconnect kapalıysa bir sey yapma
        if (this.reconnectTimer) { return; } // reconnect lanlandıysa yeniden planlama
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {console.error("Maximum reconnect attempts reached");return} // max deneme
        this.reconnectAttempts++
        const delay = Math.min(1000*2**this.reconnectAttempts, 30000) // exponential backoff
        this.logger.warn(
            {
                attempt: this.reconnectAttempts,
                delay,
            },
            "Reconnect attempt scheduled"
        )
        this.reconnectTimer = setTimeout(async () => {
            this.reconnectTimer = null
            await this.whatsappClient.connect()
        }, delay)
    }

    async clearAuthState(){
        try {
            await fs.promises.rm(this.authPath, {recursive: true, force: true});
            this.logger.info("Cleared auth state");
        }catch(error){
            this.logger.warn(String(error), 'Error while cleared auth state');
        }
    }

    async disconnect() {
        this.shouldReconnect = false
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer)
            this.reconnectTimer = null
        }
        
        const sock = this.whatsappClient.getSocket();
        
        if (sock){
            sock.end(undefined)
        }
        this.logger.warn("Whatsapp disconnected")
    }
}