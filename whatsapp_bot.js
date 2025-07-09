const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, delay } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const pino = require('pino');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const cron = require('node-cron');
const express = require('express');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');


const config = {
    geminiApiKey: process.env.GEMINI_API_KEY || 'AIzaSyD0FW4jIXd1dmzSvPTFLMkgQqWqKnaxJ90',
    port: process.env.PORT || 3000,
    adminNumber: process.env.ADMIN_NUMBER || '242066414173@s.whatsapp.net',
    botName: 'Assistant Bot',
    autoReply: true,
    viewStatus: true,
    alwaysOnline: true
};


const insultes = [
    'con', 'connard', 'salope', 'putain', 'merde', 'idiot', 'imbecile',
    'cretin', 'debile', 'stupide', 'nul', 'bâtard', 'enculé', 'pute', 'mboula', 'mama', 'naze', 'romano'
];

const dbPath = './bot_data.json';
let botData = {
    blockedUsers: [],
    scheduledMessages: [],
    userInteractions: {},
    lastSeen: {}
};


function loadData() {
    try {
        if (fs.existsSync(dbPath)) {
            const data = fs.readFileSync(dbPath, 'utf8');
            botData = { ...botData, ...JSON.parse(data) };
        }
    } catch (error) {
        console.log('Erreur lors du chargement des données:', error);
    }
}


function saveData() {
    try {
        fs.writeFileSync(dbPath, JSON.stringify(botData, null, 2));
    } catch (error) {
        console.log('Erreur lors de la sauvegarde:', error);
    }
}


const genAI = new GoogleGenerativeAI(config.geminiApiKey);
const model = genAI.getGenerativeModel({ model: 'gemini-pro' });

async function generateResponse(message, userNumber) {
    try {
        const context = `Tu es un assistant WhatsApp amical et utile. 
        Réponds de manière naturelle et concise en français.
        Message de l'utilisateur: "${message}"`;
        
        const result = await model.generateContent(context);
        const response = result.response;
        return response.text();
    } catch (error) {
        console.log('Erreur Gemini:', error);
        return 'Désolé, je ne peux pas répondre maintenant. Réessayez plus tard.';
    }
}


function containsInsult(message) {
    const lowerMessage = message.toLowerCase();
    return insultes.some(insulte => lowerMessage.includes(insulte));
}


async function startBot() {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info_baileys');
    const { version, isLatest } = await fetchLatestBaileysVersion();
    
    console.log(`Version Baileys: ${version}, Latest: ${isLatest}`);

    const sock = makeWASocket({
        version,
        logger: pino({ level: 'silent' }),
        auth: state,
        browser: ['JACOB', 'Desktop', '1.0.0'],
        defaultQueryTimeoutMs: 60000,
        keepAliveIntervalMs: 10000,
        markOnlineOnConnect: config.alwaysOnline
    });

    
    function keepOnline() {
        if (config.alwaysOnline) {
            sock.sendPresenceUpdate('available');
        }
    }

    
    setInterval(keepOnline, 30000);


    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log('📱 QR Code reçu, scannez avec WhatsApp:');
            qrcode.generate(qr, { small: true });
        }
        
        if (connection === 'close') {
            let shouldReconnect = true;
            
            if (lastDisconnect && lastDisconnect.error) {
                if (lastDisconnect.error instanceof Boom) {
                    shouldReconnect = lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut;
                }
            }
                
            console.log('Connexion fermée, reconnexion:', shouldReconnect);
            
            if (shouldReconnect) {
                setTimeout(startBot, 5000);
            }
        } else if (connection === 'open') {
            console.log('✅ Bot connecté avec succès!');
            keepOnline();
            
            
            sock.sendMessage(config.adminNumber, { 
                text: `🤖 ${config.botName} est maintenant en ligne!\n\n` +
                      `Heure de connexion: ${new Date().toLocaleString()}\n` +
                      `${Object.keys(botData.userInteractions).length} utilisateurs interactifs`
            }).catch(e => console.log('Erreur notification connexion:', e));
        }
    });

    sock.ev.on('creds.update', saveCreds);


    sock.ev.on('messages.upsert', async (m) => {
        try {
            const message = m.messages[0];
            if (!message || message.key.fromMe || message.key.remoteJid === 'status@broadcast') return;

            const from = message.key.remoteJid;
            
          
            if (from.includes('@g.us')) {
                console.log('Message de groupe ignoré:', from);
                return;
            }

            const messageText = message.message?.conversation || 
                              message.message?.extendedTextMessage?.text || '';
            
          
            if (botData.blockedUsers.includes(from)) {
                console.log(`Message ignoré de ${from} (utilisateur bloqué)`);
                return;
            }

            
            if (containsInsult(messageText)) {
                console.log(`Insulte détectée de ${from}, blocage...`);
                
                botData.blockedUsers.push(from);
                saveData();
                
                await sock.sendMessage(from, {
                    text: '⚠️ Vous avez été bloqué pour langage inapproprié. Contactez l\'admin pour être débloqué.'
                });
                
                try {
                    await sock.updateBlockStatus(from, 'block');
                } catch (blockError) {
                    console.log('Erreur lors du blocage:', blockError);
                }
                return;
            }


            try {
                await sock.readMessages([message.key]);
            } catch (readError) {
                console.log('Erreur lecture message:', readError);
            }

           
            if (config.autoReply && messageText.trim()) {
                try {
                    await sock.sendPresenceUpdate('composing', from);
                    
                    const response = await generateResponse(messageText, from);
                    
                    await delay(1000 + Math.random() * 2000);
                    
                    await sock.sendMessage(from, { text: response });
                    
                    botData.userInteractions[from] = {
                        lastMessage: messageText,
                        lastResponse: response,
                        timestamp: Date.now()
                    };
                    saveData();
                    
                } catch (error) {
                    console.log('Erreur lors de la réponse automatique:', error);
                }
            }
        } catch (error) {
            console.log('Erreur dans messages.upsert:', error);
        }
    });

    
    sock.ev.on('messages.upsert', async (m) => {
        if (!config.viewStatus) return;
        
        try {
            const message = m.messages[0];
            if (message?.key?.remoteJid === 'status@broadcast') {
                await sock.readMessages([message.key]);
                console.log('Statut vu automatiquement');
            }
        } catch (error) {
            console.log('Erreur lors de la lecture du statut:', error);
        }
    });

    
    async function sendScheduledMessage(to, text) {
        try {
            await sock.sendMessage(to, { text });
            console.log(`Message programmé envoyé à ${to}`);
        } catch (error) {
            console.log('Erreur envoi message programmé:', error);
        }
    }

    
    sock.ev.on('messages.upsert', async (m) => {
        try {
            const message = m.messages[0];
            if (!message || message.key.fromMe) return;
            
            const from = message.key.remoteJid;
            const messageText = message.message?.conversation || 
                              message.message?.extendedTextMessage?.text || '';
            
            
            if (from === config.adminNumber) {
                if (messageText.startsWith('/unblock ')) {
                    const userToUnblock = messageText.split(' ')[1];
                    botData.blockedUsers = botData.blockedUsers.filter(u => u !== userToUnblock);
                    saveData();
                    
                    await sock.sendMessage(from, { text: `✅ Utilisateur ${userToUnblock} débloqué` });
                    try {
                        await sock.updateBlockStatus(userToUnblock, 'unblock');
                    } catch (unblockError) {
                        console.log('Erreur déblocage:', unblockError);
                    }
                }
                
                if (messageText === '/stats') {
                    const stats = `📊 Statistiques du bot:
                    
👥 Utilisateurs bloqués: ${botData.blockedUsers.length}
💬 Interactions totales: ${Object.keys(botData.userInteractions).length}
⏰ Dernière activité: ${new Date().toLocaleString()}
🟢 Statut: En ligne`;
                    
                    await sock.sendMessage(from, { text: stats });
                }
                
                if (messageText.startsWith('/broadcast ')) {
                    const broadcastText = messageText.replace('/broadcast ', '');
                    let sent = 0;
                    
                    for (const [user] of Object.entries(botData.userInteractions)) {
                        if (!botData.blockedUsers.includes(user)) {
                            await sendScheduledMessage(user, broadcastText);
                            sent++;
                            await delay(2000);
                        }
                    }
                    
                    await sock.sendMessage(from, { text: `📢 Message diffusé à ${sent} utilisateurs` });
                }
            }
        } catch (error) {
            console.log('Erreur dans commandes admin:', error);
        }
    });

    return sock;
}


const app = express();

app.get('/', (req, res) => {
    res.send(`
        <h1>🤖 Bot WhatsApp Actif</h1>
        <p>Statut: En ligne ✅</p>
        <p>Heure: ${new Date().toLocaleString()}</p>
        <p>Utilisateurs bloqués: ${botData.blockedUsers.length}</p>
    `);
});

app.get('/ping', (req, res) => {
    res.json({ status: 'online', timestamp: Date.now() });
});


function keepAppAlive() {
    setInterval(() => {
        try {
            const http = require('http');
            const options = {
                hostname: 'localhost',
                port: config.port,
                path: '/ping',
                method: 'GET'
            };
            
            const req = http.request(options, (res) => {
                console.log('Keep alive ping:', res.statusCode);
            });
            
            req.on('error', (error) => {
                console.log('Keep alive error:', error.message);
            });
            
            req.end();
        } catch (error) {
            console.log('Keep alive error:', error.message);
        }
    }, 280000);
}


async function main() {
    loadData();
    
    app.listen(config.port, () => {
        console.log(`🚀 Bot démarré sur le port ${config.port}`);
    });
    
    keepAppAlive();
    
    try {
        await startBot();
    } catch (error) {
        console.error('Erreur lors du démarrage:', error);
        setTimeout(main, 10000);
    }
}


process.on('unhandledRejection', (error) => {
    console.error('Erreur non gérée:', error);
});

process.on('uncaughtException', (error) => {
    console.error('Exception non capturée:', error);
});

main();
