import { 
    SlashCommandBuilder,
    ChatInputCommandInteraction,
    EmbedBuilder, 
    ActionRowBuilder, 
    ModalBuilder,
    LabelBuilder,
    StringSelectMenuBuilder,
    StringSelectMenuOptionBuilder,
    InteractionCollector,
    InteractionType
} from "discord.js";
import { getInertia } from '../utilitys/inertiaHelper.js';

export const data = new SlashCommandBuilder()
    .setName("avatar")
    .setDescription("⎡Information⎦ grab the skin of a selected player")
    .addStringOption(option => option
        .setName('username')
        .setDescription('Player name whose skin/avatar you want to see')
        .setRequired(true)
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
async function autoCreator(mainEmbed, currentlyResponse, filter = []) {
    mainEmbed.setFields([]);

    const emojis_type = {
        hat: "🎩", addon: "📦", tool: "⚙️",
        face: "😁", tshirt: "👕", shirt: "🧥",
        pants: "👖", head: "🧩", torso: "🧩",
        showpiece: "👑"
    };

    for (const item of currentlyResponse.items) {
        const { id, name, slug, item_type } = item;

        if (filter.length && !filter.includes(item_type)) continue;
        if (mainEmbed.data.fields?.length >= 25) break;

        createItemField( mainEmbed, `${emojis_type[item_type] ?? "📦"} ${name}`, slug, id);
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
export async function execute(interaction) {
    await interaction.deferReply({
        withResponse: true
    });
    const username = interaction.options.getString('username');

    const { 
        id: userId, 
        thumbnail,
        headshot
    } = (await getInertia(`https://netisu.com/@${username}`)).props.user.data;

    const userValues = {
        Sparkles: -1,
        Stars: -1
    };

    const currentlyResponse = await fetch(`https://netisu.com/api/inventory/currently-wearing/${userId}`).then(r => r.json());
    
    const mainEmbed = new EmbedBuilder()
        .setTitle(`@${username === "letas13" ? "Felix: " : ""}${username} Currently Wearing`)
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
