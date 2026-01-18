const INERTIA_VERSION = "23ce0741650b665eea51f528e7148771"

/**
 * @param {string} url 
 * @param {Object|null} cookies
 * @param {Object|null} extraHeaders
 */
export async function getInertia(url, cookies = null, extraHeaders = null) {
    const headers = {
        "X-Inertia": "true",
        "X-Inertia-Version": INERTIA_VERSION,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    };

    if (extraHeaders) {
        Object.assign(headers, extraHeaders);
    }

    if (cookies) {
        headers["Cookie"] = Object.entries(cookies)
        .map(([k, v]) => `${k}=${v}`)
        .join("; ");
    }

    const response = await fetch(url, {
        method: "GET",
        headers,
        redirect: "follow",
    });

    if (response.status === 409) {
        const newLocation = response.headers.get("x-inertia-location");
        if (newLocation) {
        return await getInertia(newLocation, cookies, extraHeaders);
        }
    }

    if (!response.ok) {
        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
    }

    return await response.json();
}