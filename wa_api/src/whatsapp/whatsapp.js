import makeWASocket, {
    useMultiFileAuthState,
    DisconnectReason
} from "baileys"
import P from 'pino'
import QRCode from 'qrcode'

export async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(
        "./auth_info"
    )

    const sock = makeWASocket({
        auth: state,
        logger: P({
            level: "info"
        })
    })

    sock.ev.on("creds.update", saveCreds)

    sock.ev.on("connection.update", async (update) => {
        const {
            connection,
            lastDisconnect,
            qr
        } = update
        
        if (qr) {
            // as an example, this prints the qr code to the terminal
            console.log(await QRCode.toString(qr, {type: 'terminal'}))
        }

        if (connection === "connecting") {
            console.log("Whatsapp connecting")
        }

        if (connection === "open") {
            console.log("Whatsapp connected")
        }

        if (connection === "close") {
            console.log("Whatsapp disconnected")

            const statusCode = lastDisconnect?.error?.output?.statusCode

            if (statusCode === DisconnectReason.restartRequired) {
                console.log("Socket restarted...")
                return await startWhatsApp()
            }
            if (statusCode === DisconnectReason.loggedOut) {
                return console.log("User logged out...")
            }
            console.log("Whatsapp disconnected, restarting...")
            return await startWhatsApp()
        }
    })
    return sock
}