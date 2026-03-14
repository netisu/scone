import { 
    SlashCommandBuilder,
    EmbedBuilder,
    StringSelectMenuBuilder,
    ActionRowBuilder
} from "discord.js";
import { getInertia } from '../utilitys/inertiaHelper.js';

export const data = new SlashCommandBuilder()
    .setName("user")
    .setDescription("User related commands")
    .addSubcommand(subcommand =>
        subcommand
            .setName("general")
            .setDescription("Grab general informations of a selected player")
            .addStringOption(option =>
                option
                    .setName("username")
                    .setDescription("Name of player you want to get this information from")
                    .setRequired(true)
            )
    );

async function createBasicInformation(mainEmbed, basic) {
    /*mainEmbed.addFields({
        name: "**General**",
        value: `
        Level: **\`${level}\`**\n
        ID: **\`${userId}\`**\n
        Joined: **\`${joindate}\`**
        `,
        inline: true
    });*/

    mainEmbed.addFields({
        name: "**Player level**",
        value: `**\`${basic.level}\`**`,
        inline: true
    });

    mainEmbed.addFields({
        name: "**Player country**",
        value: `**\`${basic.settings.country.name}\`**`,
        inline: true
    });

    mainEmbed.addFields({
        name: "**Joined on**",
        value: `**\`${basic.joindate}\`**`,
        inline: true
    });

    mainEmbed.addFields({
        name: "**Last seen**",
        value: `**\`${basic.dateHum}\`**`,
        inline: true
    });

    mainEmbed.addFields({
        name: "**Primary Space**",
        value: `**${basic.settings.primarySpace 
            ? `[\`${basic.settings.primarySpace.name}\`](https://netisu.com/${basic.settings.primarySpace.id}/${basic.settings.primarySpace.slug})`
            : "\`doesn't have\`"
        }**`,
        inline: true
    });

    /*mainEmbed.addFields({
        name: "**Settings**",
        value: `
        Status: **\`${status}\`**\n
        Country: **\`${settings.country.name}\`**\n
        Primary Space: **\`${(settings.primarySpace ? `[${settings.primarySpace.name}](https://netisu.com/${settings.primarySpace.id}/${settings.primarySpace.slug})` : "Does have")}\`**
        `,
        inline: true
    });

    mainEmbed.addFields({
        name: "**Random**",
        value: `
        Last seen: **\`${dateHum}\`**\n
        About me: **\`avoid a huge description (i will change this)\`**\n
        Posts: **\`${posts}\`**
        `,
        inline: true
    });*/
}

async function selectMenuCallback(FInteraction, ctx) {
    const chosenValue = FInteraction.values[0];
    await FInteraction.deferUpdate();

    switch (chosenValue) {
        case 'spaces':
            const mainEmbed = ctx.mainEmbed;
            mainEmbed.setFields([]);
            
            const joinedSpaces = ctx.basic.spaces;
            for (const information of joinedSpaces) {
                const {
                    creator,
                    id,
                    name,
                    slug
                } = information;
                

                mainEmbed.addFields({
                    name: `**🚀 ${name}**`,
                    value: `Creator: **[${creator.display_name} (@${creator.username})](https://netisu.com/@${creator.username})**
                    Link: **[Open Space](https://netisu.com/spaces/${id}/${slug})**`,
                    inline: true
                })
            }

            await ctx.response.edit({
                embeds: [mainEmbed], 
                components: [ctx.row]
            });
            break;

        default:
            ctx.mainEmbed.setFields([]);
            createBasicInformation(ctx.mainEmbed, ctx.basic);
            await ctx.response.edit({
                embeds: [ctx.mainEmbed], 
                components: [ctx.row]
            });
            break;
    }
}

/**
* @param {ChatInputCommandInteraction} interaction
*/
async function executeGeneral(interaction) {
    await interaction.deferReply({
        withResponse: true
    });
    const username = interaction.options.getString('username');
    const {
        thumbnail,
        headshot,
        level,
        dateHum,
        joindate,
        settings,
        spaces
    } = (await getInertia(`https://netisu.com/@${username}`)).props.user.data;

    const basic = {
        thumbnail,
        headshot,
        level,
        dateHum,
        joindate,
        settings,
        spaces
    };

    const mainEmbed = new EmbedBuilder()
        .setTitle(`@${username}'s Informations`)
        .setURL(`https://netisu.com/@${username}`)
        .setDescription(`> **This will retrieve all Information listed in [Inertia](https://netisu.com/${username})**`)
        .setColor(0x6900d1)
        .setAuthor({
            name: 'Netisu Bot',
            url: 'https://netisu.com/',
            iconURL: headshot
        })
        .setTimestamp()
        .setThumbnail(thumbnail);

    const selectMenu = new StringSelectMenuBuilder()
        .setCustomId('user_select')
        .setPlaceholder('User informations')
        .addOptions([
            { label: 'Show basic informations', description: 'Pick up all basic informations!', value: 'normal' },
            { label: 'Show joined spaces', description: 'See all the spaces player entered!', value: 'spaces' }
            //{ label: 'Create Fetch', description: 'Creates a fetch to equip user skin (I recommend saving your skin\'s fetch first)', value: 'fetch' }
        ]);
    
    const row = new ActionRowBuilder().addComponents(selectMenu);  
    createBasicInformation(mainEmbed, basic);

    const response = await interaction.editReply({
        embeds: [mainEmbed], 
        components: [row]
    });
    const context = {
        basic, 
        mainEmbed,
        response,
        row
    };

    const collector = response.createMessageComponentCollector({ 
        filter: i => i.customId === 'user_select' && i.user.id == interaction.user.id,
        time: 60000,
        dispose: false
    });

    collector.on('collect', i => { selectMenuCallback(i, context) });
    collector.on('end', collected => { response.edit({  embeds: [mainEmbed], components: [] }); });
}

export async function execute(interaction) {
    const subcommand = interaction.options.getSubcommand();
    switch (subcommand)
    {
        case "general":
            executeGeneral(interaction);
            break;
    }
}