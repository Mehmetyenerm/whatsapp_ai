import path from "node:path";
import fs from "node:fs/promises";
import {spawn} from "child_process";

export function toJid(to) {
    if (to.includes("@")) return to; // zaten tam jid (g.us, s.whatsapp.net, lid)
    const digits = to.replace(/[^\d]/g, "");
    return `${digits}@s.whatsapp.net`;
}

export function convertToOpus(inputPath) {
    return new Promise((resolve, reject) => {
        const outputPath = path.join(
            path.dirname(inputPath),
            `${path.parse(inputPath).name}_converted.ogg`
        );

        const ffmpeg = spawn("ffmpeg", [
            "-y", // varsa üzerine yaz
            "-i", inputPath,
            "-c:a", "libopus",
            "-ac", "1",
            "-avoid_negative_ts", "make_zero",
            outputPath
        ]);

        let stderr = "";
        ffmpeg.stderr.on("data", (data) => {
            stderr += data.toString();
        });

        ffmpeg.on("close", (code) => {
            if (code === 0) {
                resolve(outputPath);
            } else {
                reject(new Error(`ffmpeg dönüşümü başarısız (code ${code}): ${stderr}`));
            }
        });

        ffmpeg.on("error", (err) => {
            reject(err);
        });
    });
}