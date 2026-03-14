import Discord from "discord.js";

const { 
    SlashCommandBuilder,
    ChatInputCommandInteraction,
    EmbedBuilder,
    ActionRowBuilder,
    ModalBuilder,
    LabelBuilder,
    StringSelectMenuBuilder,
    StringSelectMenuOptionBuilder,
    ButtonBuilder,
    ButtonStyle,   
    InteractionCollector,
    InteractionType
} = Discord;
import { getInertia } from '../utilitys/inertiaHelper.js';
import { 
    update,
    findOrCreate
} from '../utilitys/databaseUsers.js'
import { ChildProcess } from "child_process";

export const data = new SlashCommandBuilder()
    .setName("avatar")
    .setDescription("Grab the skin of a selected player")
    .addSubcommand(subcommand =>
        subcommand
            .setName("general")
            .setDescription("Grab skin of a selected player")
            .addStringOption(option =>
                option
                    .setName("username")
                    .setDescription("Name of player you want to get skin from")
                    .setRequired(true)
            )
    )
    .addSubcommand(subcommand =>
        subcommand
            .setName("rate")
            .setDescription("Rate skin of a selected player")
            .addStringOption(option =>
                option
                    .setName("username")
                    .setDescription("Name of player you want rate from")
                    .setRequired(true)
            )
    );

/**
 * @param {import("discord.js").EmbedField} mainEmbed 
 */
function createItemField(mainEmbed, name, slug, item_id) {
    mainEmbed.addFields({
        name: name,
        value: `[**\`Market Link\`**](https://netisu.com/market/item/${item_id}/${slug})`,
        inline: true
    });
}

function createBodyColorsField(mainEmbed, renderConfig) {
    if (!renderConfig?.colors) return;

    const colors = renderConfig.colors;

    const grouped = {};
    const lines = [];

    const partsOrder = [
        ["Head", "Head"], ["Torso", "Torso"],
        ["RightArm", "Right Arm"], ["RightLeg", "Right Leg"],
        ["LeftArm", "Left Arm"], ["LeftLeg", "Left Leg"]
    ];

    for (const [part, label] of partsOrder) {
        const color = colors[part];
        if (!color) continue;

        if (!grouped[color]) grouped[color] = [];
        grouped[color].push(label);
    }

    const entries = Object.entries(grouped);
    if (!entries.length) return;

    if (entries.length === 1) {
        const [color] = entries[0];
        lines.push(`All: **\`#${color}\`**`);
    } else {
        for (const [color, parts] of entries) {
            lines.push(`${parts.join("/")}: **\`#${color}\`**`);
        }
    }

    mainEmbed.addFields({
        name: '**🎨 Body Colors**',
        value: lines.join("\n"),
        inline: false
    });
}

/**
 * @param {import("discord.js").EmbedField} mainEmbed 
 * @param {Array} filter
 */
export async function autoCreator(mainEmbed, currentlyResponse, filter = []) {
    mainEmbed.setFields([]);

    const emojis_type = {
        hat: "🎩", addon: "📦", tool: "⚙️",
        face: "😁", tshirt: "👕", shirt: "🧥",
        pants: "👖", showpiece: "👑"
    };

    for (const item of currentlyResponse.items) {
        const { id, name, slug, item_type } = item;

        if (filter.length && !filter.includes(item_type)) continue;
        if (mainEmbed.data.fields?.length >= 25) break;

        createItemField( mainEmbed, `${emojis_type[item_type] ?? "🧩"} ${name}`, slug, id);
    }
    
    createBodyColorsField(mainEmbed, currentlyResponse.render_config);
}

const ITEM_TYPE_OPTIONS = [ "Hat", "Addon", "Tool", "Face", "Tshirt", "Shirt", "Pants", "Head", "Torso"].map(type =>
  new StringSelectMenuOptionBuilder()
    .setLabel(type)
    .setValue(type.toLocaleLowerCase())
    .setDescription(`All equipped ${type}s`)
);

async function createFilterModal(interaction, ctx) {
    const mainModal = new ModalBuilder()
        .setCustomId("avatar_filter_modal")
        .setTitle("Select the filter for items");

    const itemsSelectMenu = new LabelBuilder()
        .setLabel('Select the items you want to filter')
        .setDescription("Select item types to be shown only")
        .setStringSelectMenuComponent(
            new StringSelectMenuBuilder()
                .setCustomId('item-filter-select-menu')
                .setMinValues(1)
                .setMaxValues(ITEM_TYPE_OPTIONS.length)
                .setPlaceholder("Item types")
                .addOptions(ITEM_TYPE_OPTIONS)
        );

    mainModal.addLabelComponents(itemsSelectMenu);
    await interaction.showModal(mainModal);

    const collector = new InteractionCollector(interaction.client, {
        interactionType: InteractionType.ModalSubmit,
        time: 60_000,
        filter: (i) => i.customId === "avatar_filter_modal" && i.user.id === ctx.interaction.user.id
    });

    collector.on("collect", async (i) => {
        const field = i.fields.fields.get("item-filter-select-menu");
        const selectedValues = field.values ?? [];

        await autoCreator(ctx.mainEmbed, ctx.currentlyResponse, selectedValues);
        await i.deferUpdate();

        await ctx.response.edit({ embeds: [ctx.mainEmbed], components: [ctx.row] });
        collector.stop();
    });
}

function getSkinValue(currentlyResponse) {
    let TotalSparkles = 0;
    for (const information of currentlyResponse.items) {
        const cost_sparkles = information.cost_sparkles;
        TotalSparkles += cost_sparkles;
    }

    return TotalSparkles
}

/**
 * @param {SelectMenuInteraction} FInteraction 
 */
async function selectMenuCallback(FInteraction, ctx) {
    const chosenValue = FInteraction.values[0];
    switch(chosenValue){
        case 'skinvalue':
            await FInteraction.deferUpdate();
            const {
                mainEmbed,
                currentlyResponse,
                row
            } = ctx;

            if (ctx.userValues.Sparkles === -1) {
                ctx.userValues.Sparkles = await getSkinValue(currentlyResponse);
            }

            ctx.userValues.Stars = Math.round(ctx.userValues.Sparkles / 10);

            mainEmbed.setFields([]);
            mainEmbed.addFields({ name: '**✨ Sparkles**', value: `**\`${ctx.userValues.Sparkles}\`**`, inline: true });
            mainEmbed.addFields({ name: '**🌟 Stars**', value: `**\`${ctx.userValues.Stars}\`**`, inline: true });

            await ctx.response.edit({
                embeds: [mainEmbed], 
                components: [row]
            });
            break;
        case 'filter':
            await createFilterModal(FInteraction, ctx);
            break;
        default:
            await FInteraction.deferUpdate();

            await autoCreator(ctx.mainEmbed, ctx.currentlyResponse, []);
            await ctx.response.edit({ embeds: [ctx.mainEmbed], components: [ctx.row] });
            break;
    };
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
        id: userId, 
        thumbnail,
        headshot
    } = (await getInertia(`https://netisu.com/@${username}`)).props.user.data;
    
    let selectedUserDB = await findOrCreate(
        { id: userId },
        { id: userId, avatarRates: { likes: 0, dislikes: 0 }, avatarVotes: {} }
    );

    const userValues = {
        Sparkles: -1,
        Stars: -1
    };

    const currentlyResponse = await fetch(`https://netisu.com/api/inventory/currently-wearing/${userId}`).then(r => r.json());
    
    const mainEmbed = new EmbedBuilder()
        .setTitle(`@${username === "letas13" ? "Felix: " : ""}${username}'s Currently Wearing`)
        .setURL(`https://netisu.com/@${username}`)
        .setDescription(`> **This will retrieve all items listed in the [API](https://netisu.com/api/inventory/currently-wearing/${userId})**`)
        .setColor(0x6900d1)
        .setAuthor({
            name: 'Netisu Bot',
            url: 'https://netisu.com/',
            iconURL: headshot
        })
        .setTimestamp()
        .setThumbnail(thumbnail);
    
    await autoCreator(mainEmbed, currentlyResponse);

    const likes = selectedUserDB.avatarRates.likes || 0;
    const dislikes = selectedUserDB.avatarRates.dislikes || 0;
    const total = likes + dislikes;
    const currentRate = total === 0 ? 0 : (likes / total) * 10;

    mainEmbed.addFields(
        { name: '🌟 Current rate', value: `${currentRate.toFixed(1)}/10`, inline: true },
        { name: '👍 Likes', value: `${likes}`, inline: true },
        { name: '👎 Dislikes', value: `${dislikes}`, inline: true }
    );

    const selectMenu = new StringSelectMenuBuilder()
        .setCustomId('avatar_select')
        .setPlaceholder('Avatar options')
        .addOptions([
            { label: 'Show Every Items', description: 'Pick up all items that are currently equipped!', value: 'normal' },
            { label: 'Select a filter', description: 'Select filters you want to see!', value: 'filter' },
            { label: 'Estimate price of Avatar', description: 'It estimates how much user spent based on their items!', value: 'skinvalue' }
            //{ label: 'Create Fetch', description: 'Creates a fetch to equip user skin (I recommend saving your skin\'s fetch first)', value: 'fetch' }
        ]);
    
    const row = new ActionRowBuilder().addComponents(selectMenu);
    const response = await interaction.editReply({
        embeds: [mainEmbed], 
        components: [row]
    });

    const collector = response.createMessageComponentCollector({ 
        filter: i => i.customId === 'avatar_select' && i.user.id == interaction.user.id,
        time: 60000,
        dispose: false
    });

    const context = {
        interaction, 
        response, 
        mainEmbed, 
        row, 
        currentlyResponse, 
        userValues
    };
    collector.on('collect', i => { selectMenuCallback(i, context) });
    collector.on('end', collected => { response.edit({  embeds: [mainEmbed], components: [] }); });
}

async function rateVoteCallback(FInteraction, ctx) {
    const chosenValue = FInteraction.customId;
    const { selectedUserDB, mainEmbed } = ctx;

    if (!selectedUserDB.avatarRates) selectedUserDB.avatarRates = { likes: 0, dislikes: 0 };
    if (!selectedUserDB.avatarVotes) selectedUserDB.avatarVotes = {};

    const prevVote = selectedUserDB.avatarVotes[FInteraction.user.id];

    if (prevVote) {
        if (prevVote === chosenValue) {
            return FInteraction.reply({ content: "You already voted this way!", ephemeral: true });
        }

        if (prevVote === "like") selectedUserDB.avatarRates.likes--;
        if (prevVote === "dislike") selectedUserDB.avatarRates.dislikes--;
    }

    if (chosenValue === "like") selectedUserDB.avatarRates.likes++;
    if (chosenValue === "dislike") selectedUserDB.avatarRates.dislikes++;

    selectedUserDB.avatarVotes[FInteraction.user.id] = chosenValue;

    await update({ id: selectedUserDB.id }, {
        avatarRates: selectedUserDB.avatarRates,
        avatarVotes: selectedUserDB.avatarVotes
    });

    const totalVotes = selectedUserDB.avatarRates.likes + selectedUserDB.avatarRates.dislikes;
    const newRate = totalVotes === 0 ? 0 : (selectedUserDB.avatarRates.likes / totalVotes) * 10;

    mainEmbed.setFields(
        { name: "🌟 New rate", value: `**\`${newRate.toFixed(1)}/10\`**`, inline: true },
        { name: "👍 Likes", value: `**\`${selectedUserDB.avatarRates.likes}\`**`, inline: true },
        { name: "👎 Dislikes", value: `**\`${selectedUserDB.avatarRates.dislikes}\`**`, inline: true }
    );

    await FInteraction.update({ embeds: [mainEmbed], components: [] });
}


/**
* @param {ChatInputCommandInteraction} interaction
*/
async function executeRate(interaction) {
    const username = interaction.options.getString('username');
    const { 
        thumbnail,
        headshot,
        id: userId
    } = (await getInertia(`https://netisu.com/@${username}`)).props.user.data;
    
    let selectedUserDB = await findOrCreate(
        { id: userId },
        { id: userId, avatarRates: { likes: 0, dislikes: 0 }, avatarVotes: {} }
    );

    const randomRateInt = Math.floor((Math.random() * 10) + 1);

    const mainEmbed = new EmbedBuilder()
        .setTitle(`@${username === "letas13" ? "Felix: " : ""}${username}'s Currently Wearing`)
        .setURL(`https://netisu.com/@${username}`)
        .setDescription(`> **hmm, I think the rating of this avatar is ${randomRateInt}/10**`)
        .setColor(0x6900d1)
        .setAuthor({
            name: 'Netisu Bot',
            url: 'https://netisu.com/',
            iconURL: headshot
        })
        .setTimestamp()
        .setThumbnail(thumbnail);
    
    // top 10 values
    // talveka deserves 1000 dislikes bt-
    const likes = selectedUserDB.avatarRates?.likes ?? 0;
    const dislikes = selectedUserDB.avatarRates?.dislikes ?? 0;
    const totalVotes = likes + dislikes;
    const currentRate = totalVotes === 0 ? 0 : (likes / totalVotes) * 10;

    mainEmbed.addFields(
        { name: '✨ Avatar Rate', value: `**\`${currentRate.toFixed(1)}/10\`**`, inline: true },
        { name: '👍 Likes', value: `**\`${likes}\`**`, inline: true },
        { name: '👎 Dislikes', value: `**\`${dislikes}\`**`, inline: true }
    );

    const likeButton = new ButtonBuilder()
        .setCustomId("like")
        .setLabel("Like")
        .setStyle(ButtonStyle.Primary);

    const dislikeButton = new ButtonBuilder()
        .setCustomId("dislike")
        .setLabel("Dislike")
        .setStyle(ButtonStyle.Secondary);

    const row = new ActionRowBuilder().addComponents(likeButton, dislikeButton);
    await interaction.reply({
        embeds: [mainEmbed],
        components: [row],
        withResponse: true
    });
    const response = await interaction.fetchReply();

    const collector = response.createMessageComponentCollector({ 
        filter: i => (i.customId === 'like' || i.customId === 'dislike') && i.user.id == interaction.user.id,
        time: 60000,
        dispose: false
    });

    const context = {
        interaction, 
        response, 
        mainEmbed, 
        row, 
        userId, 
        selectedUserDB
    };
    collector.on('collect', i => { rateVoteCallback(i, context) });
    collector.on('end', collected => { response.edit({  embeds: [mainEmbed], components: [] }); });
}

/**
* @param {ChatInputCommandInteraction} interaction
*/
export async function execute(interaction) {
    const subcommand = interaction.options.getSubcommand();
    switch (subcommand)
    {
        case "general":
            executeGeneral(interaction);
            break;
        case "rate":
            executeRate(interaction);
            break;
    }
}