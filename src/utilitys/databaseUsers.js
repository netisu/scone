/*
    just to make this easier for future changes
*/
import Datastore from 'nedb-promises';
let db;

/**
 * @param {string} [filepath='./src/database.db']
 */
export async function startDatabase(filepath = './src/database.db') {
    db = Datastore.create({
        filename: filepath,
        autoload: true
    });
}

/**
 * @param {Object} data 
 * @returns {Promise<Object>}
 */
export async function create(data) {
    return await db.insert(data);
}

/**
 * @param {Object} query 
 * @returns {Promise<Array>}
 */
export async function find(query = {}) {
    return await db.find(query);
}

/**
 * @param {Object} query 
 * @returns {Promise<Object|null>}
 */
export async function findOne(query = {}) {
    return await db.findOne(query);
}

/**
 * @param {Object} query 
 * @param {Object} update 
 * @param {Object} options 
 * @returns {Promise<number>}
 */
export async function update(query, updateData, options = {}) {
    const { numAffected } = await db.update(query, { $set: updateData }, options);
    return numAffected;
}

/**
 * @param {Object} query 
 * @param {Object} options 
 * @returns {Promise<number>} 
 */
export async function remove(query, options = {}) {
    return await db.remove(query, options);
}

/**
 * @param {Object} query 
 * @param {Object} defaultData 
 * @returns {Promise<Object>} 
 */
export async function findOrCreate(query, defaultData = {}) {
    const doc = await db.findOne(query);
    if (doc) return doc;

    return await db.insert(defaultData);
}
