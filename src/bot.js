import "dotenv/config";
import fs from "fs";
import path from "path";
import { pathToFileURL } from "url";
import { Client, GatewayIntentBits, Collection, ActivityType } from "discord.js";

const client = new Client({
  intents: [GatewayIntentBits.Guilds]
});

client.commands = new Collection();
/*
    I GOT A PLAN ARTHUR...
*/

async function loadCogs() {
    const cogsPath = path.join(process.cwd(), "src", "commands");
    const files = fs.readdirSync(cogsPath).filter(f => f.endsWith(".js"));

    for (const file of files) {
        const filePath = path.join(cogsPath, file);
        const fileUrl = pathToFileURL(filePath).href;

        const command = await import(fileUrl);

        client.commands.set(command.data.name, command);
    }
}

client.once("clientReady", async () => {
    await loadCogs();

    await client.application.commands.set(
        [...client.commands.values()].map(cmd => cmd.data)
    );

    await client.user.setPresence({
        status: "idle",
        activities: [{
            name: process.env.STATUS_MESSAGE,
            type: ActivityType.Playing
        }]
    });

    console.log("Loaded");
});

client.on("interactionCreate", async interaction => {
    const command = client.commands.get(interaction.commandName);
    if (!command) return;

    try {
        await command.execute(interaction);
    } catch (err) {
        console.error(err);

        if (interaction.deferred || interaction.replied) {
            await interaction.editReply("It looks like we're having problems, try again a little later", ephemeral=true);
        } else {
            await interaction.reply({
                content: "It looks like we're having problems, try again a little later",
                ephemeral: true
            });
        }
    }
});

client.login(process.env.DISCORD_TOKEN);
