import { 
    SlashCommandBuilder
} from "discord.js";

export const data = new SlashCommandBuilder()
    .setName("market")
    .setDescription("Market commands!")

    .addSubcommand(subcommand =>
        subcommand
            .setName("item")
            .setDescription("Get information about public items")
            .addStringOption(option =>
                option
                    .setName("id")
                    .setDescription("ID of item you want to analyze")
                    .setRequired(true)
            )
    );

/**
* @param {ChatInputCommandInteraction} interaction
*/
async function executeItem(interaction) {
    //later
}

/**
* @param {ChatInputCommandInteraction} interaction
*/
export async function execute(interaction) {
    const subcommand = interaction.options.getSubcommand();
    switch (subcommand)
    {
        case "item":
            executeItem(interaction);
            break;
    }
}
