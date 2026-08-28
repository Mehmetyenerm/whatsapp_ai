//import { startWhatsApp } from "./whatsapp/whatsapp.js"
import { WhatsAppClient } from "./whatsapp/WhatsAppClient.js"

const whatsapp = new WhatsAppClient();
await whatsapp.connect();
await whatsapp.waitUntilConnected();
/*
await whatsapp.sendMessage(
    "117996022452338@lid",
    "merhaba"
);
*/

/*
await whatsapp.sendImage(
    "117996022452338@lid",
    "./media/ACE4F7060D1153E26CDD57A094DEE148.jpg",
    ""
)
*/

/*
async function main() {
    await startWhatsApp()
}
main()
*/
