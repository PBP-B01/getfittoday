// =================================================================================
// Global Variables & Configuration
// =================================================================================

let map;
let infoWindow;
let userLocationMarker = null; // Holds the marker for the user's current location

// Data & State Management
let markers = {}; // Caches marker objects by place_id for quick access
let clientGridCache = {}; // Caches spot data for each grid cell on the client-side
let loadedGridIds = new Set(); // Tracks which grid cells have been fetched
let currentActiveCardId = null;

// State flags to prevent race conditions and feedback loops
let isUpdatingSpots = false;
let programmaticPan = false;

// Grid System Configuration (for efficient data loading)
const GRID_ORIGIN_LAT = -6.8;
const GRID_ORIGIN_LNG = 106.5;
const GRID_CELL_SIZE_DEG = 0.09; // Approx. 10km per grid cell

// =================================================================================
// Initialization
// =================================================================================

/**
 * The main entry point for the map application.
 * It determines the initial center, fetches boundaries, and creates the map.
 */
async function initMap() {
    try {
        let initialCoords = { lat: -6.370403, lng: 106.826946 };
        let initialZoom = 17; // Default zoom (approx. 500m scale)

        // Fetch map boundaries and user's location simultaneously for faster loading
        const [boundaries, position] = await Promise.all([
            fetchMapBoundaries(),
            getUserLocation()
        ]);

        let restrictionBounds = null;
        if (boundaries) {
            const buffer = 0.018; // 2km buffer
            restrictionBounds = {
                north: boundaries.north + buffer, south: boundaries.south - buffer,
                east: boundaries.east + buffer, west: boundaries.west - buffer,
            };

            // If user grants location permission, override the default start point
            if (position) {
                const { latitude: userLat, longitude: userLng } = position.coords;
                if (userLat < boundaries.north && userLat > boundaries.south && userLng < boundaries.east && userLng > boundaries.west) {
                    initialCoords = { lat: userLat, lng: userLng };
                    initialZoom = 16; // A slightly wider zoom for context
                }
            }
        } else {
            console.error("Could not fetch map boundaries. Restrictions disabled.");
        }

        // Create the map with the calculated settings
        await initializeMap(initialCoords, initialZoom, restrictionBounds);

        // If we have an initial position, show the user's location marker
        if (position) {
            updateUserLocationMarker(position);
        }

    } catch (error) {
        console.error("Failed to initialize map:", error);
    }
}

// Creates the core Google Map object and attaches UI elements and event listeners.

async function initializeMap(center, zoom, restriction) {
    const { Map } = await google.maps.importLibrary("maps");
    map = new Map(document.getElementById("map"), {
        center, zoom,
        restriction: restriction ? { latLngBounds: restriction, strictBounds: true } : null,
        disableDefaultUI: false,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControl: true,
        myLocationControl: false, // We use a custom button instead
        mapId: "7e0c35add3b17dafe20eac87",
    });
    
    infoWindow = new google.maps.InfoWindow();

    // Attach event listeners
    map.addListener('idle', () => updateSpotsForView(map));
    document.getElementById('fullscreen-toggle-btn').addEventListener('click', toggleFullScreen);
    
    createCenterOnMeButton();
}

// Start the application
initMap();

// =================================================================================
// Data Loading (Grid System)
// =================================================================================

/**
 * Main function triggered when the map stops moving. It determines which grid
 * cells are visible and fetches/renders the data for them.
 */
async function updateSpotsForView(map) {
    if (programmaticPan) { programmaticPan = false; return; }
    if (isUpdatingSpots) return;

    const bounds = map.getBounds();
    if (!bounds) return;

    isUpdatingSpots = true;
    try {
        const visibleGridIds = getVisibleGridIds(bounds);
        const newGridIdsToLoad = [...visibleGridIds].filter(id => !clientGridCache[id]);

        if (newGridIdsToLoad.length > 0) {
            // Fetch data for all new grids in parallel for speed
            const promises = newGridIdsToLoad.map(id => fetchGridData(id));
            await Promise.all(promises);
        }

        await renderSpots(visibleGridIds);
        loadedGridIds = visibleGridIds;

    } finally {
        isUpdatingSpots = false;
    }
}

/**
 * Fetches spot data for a specific grid ID from the Django API.
 */
async function fetchGridData(gridId) {
    console.log(`Fetching grid ${gridId} from server...`);
    const url = `/api/fitness-spots/?gridId=${gridId}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        clientGridCache[gridId] = data; // Store in client-side cache
        return data;
    } catch (error) {
        console.error(`Failed to fetch data for grid ${gridId}:`, error);
        clientGridCache[gridId] = { spots: [] }; // Cache empty result on error
        return null;
    }
}

/**
 * Renders all markers and sidebar cards for the currently visible grid cells.
 */
async function renderSpots(visibleGridIds) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    
    // Clear all existing markers and cards from the UI
    Object.values(markers).forEach(marker => marker.map = null);
    markers = {};
    document.getElementById('spot-cards-container').innerHTML = '';
    
    // Render spots from each visible grid
    for (const gridId of visibleGridIds) {
        const data = clientGridCache[gridId];
        if (data && data.spots) {
            data.spots.forEach(spot => {
                if (markers[spot.place_id]) return; // Avoid duplicates

                const lat = parseFloat(spot.latitude);
                const lng = parseFloat(spot.longitude);
                if (isNaN(lat) || isNaN(lng)) return;

                const marker = new AdvancedMarkerElement({ position: { lat, lng }, map, title: spot.name });
                markers[spot.place_id] = marker;
                
                const card = createSpotCard(spot);
                document.getElementById('spot-cards-container').appendChild(card);
                
                marker.addListener("click", () => showSpotDetails(spot));
                card.addEventListener('click', () => showSpotDetails(spot, true));
            });
        }
    }
    // Re-highlight the active card if it's still in view
    if (currentActiveCardId && document.getElementById(`card-${currentActiveCardId}`)) {
        highlightSpotCard(currentActiveCardId);
    }
}

// =================================================================================
// UI Interaction & User Location
// =================================================================================

/**
 * A unified function to handle all logic for displaying a spot's details.
 * @param {object} spot - The spot data object.
 * @param {boolean} shouldZoom - Whether to zoom in closer.
 */
function showSpotDetails(spot, shouldZoom = false) {
    const marker = markers[spot.place_id];
    if (!marker) return;

    programmaticPan = true; // Prevent the 'idle' listener from re-triggering an update
    map.panTo(marker.position);
    if (shouldZoom) map.setZoom(16);

    infoWindow.setContent(createInfoContent(spot));
    infoWindow.open({ anchor: marker, map });

    highlightSpotCard(spot.place_id);
}

/**
 * Creates or updates a blue dot marker representing the user's location.
 */
async function updateUserLocationMarker(position) {
    const { Marker } = await google.maps.importLibrary("marker");
    const userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };

    const svgIcon = {
        path: 'M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2z',
        fillColor: '#4285F4', fillOpacity: 1,
        strokeColor: 'white', strokeWeight: 2.5,
        scale: 0.7, anchor: new google.maps.Point(12, 12)
    };

    if (userLocationMarker) {
        userLocationMarker.position = userLocation;
    } else {
        userLocationMarker = new Marker({
            position: userLocation, map: map, icon: svgIcon, title: "Your Location"
        });
    }
}

/**
 * Creates the "Center on Me" button and adds it to the map controls.
 */
function createCenterOnMeButton() {
    const controlButton = document.createElement("button");
    controlButton.className = 'custom-map-control-button';
    controlButton.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/></svg>`;
    controlButton.title = "Center map on my location";

    controlButton.addEventListener("click", async () => {
        const position = await getUserLocation();
        if (position) {
            updateUserLocationMarker(position);
            programmaticPan = true;
            map.panTo({ lat: position.coords.latitude, lng: position.coords.longitude });
            map.setZoom(16);
        } else {
            alert("Could not get your location. Please ensure location permissions are granted.");
        }
    });

    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(controlButton);
}

// =================================================================================
// Helper Functions (Boilerplate)
// =================================================================================

function highlightSpotCard(placeId) {
    if (currentActiveCardId && currentActiveCardId !== placeId) {
        const oldCard = document.getElementById(`card-${currentActiveCardId}`);
        if (oldCard) oldCard.classList.remove('active');
    }
    const newCard = document.getElementById(`card-${placeId}`);
    if (newCard) {
        newCard.classList.add('active');
        setTimeout(() => newCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
    }
    currentActiveCardId = placeId;
}

function createSpotCard(spot) {
    const card = document.createElement('div');
    card.id = `card-${spot.place_id}`;
    card.className = 'spot-card';
    card.innerHTML = `<h3>${spot.name}</h3><p>${spot.address}</p>${spot.rating ? `<p>Rating: <strong>${spot.rating}</strong></p>` : ''}`;
    return card;
}

function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) { resolve(null); return; }
        navigator.geolocation.getCurrentPosition(resolve, () => resolve(null), { timeout: 5000 });
    });
}

function toggleFullScreen() {
    document.body.classList.toggle('full-screen-mode');
    const btn = document.getElementById('fullscreen-toggle-btn');
    const enterIcon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-5v4m0 0h-4m0 0l-5 5m0 5v4m0 0h4m0 0l-5-5m11 5h-4m0 0v-4m0 0l-5-5"></path></svg>`;
    const exitIcon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5m0 0l-1-1m1 1l1 1m4-11h5m0 0l1 1m-1-1l-1-1M5 19v-4m0 0l-1 1m1-1l1-1m10 4v-4m0 0l1 1m-1-1l-1-1"></path></svg>`;
    btn.innerHTML = document.body.classList.contains('full-screen-mode') ? exitIcon : enterIcon;
    setTimeout(() => google.maps.event.trigger(map, 'resize'), 400);
}

async function fetchMapBoundaries() {
    try {
        const response = await fetch('/api/map-boundaries/');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        return (data && typeof data.north === 'number') ? data : null;
    } catch (error) {
        console.error('Failed to fetch map boundaries:', error);
        return null;
    }
}

function getGridIdForLatLng(lat, lng) {
    if (lat < GRID_ORIGIN_LAT || lng < GRID_ORIGIN_LNG) return null;
    const row = Math.floor((lat - GRID_ORIGIN_LAT) / GRID_CELL_SIZE_DEG);
    const col = Math.floor((lng - GRID_ORIGIN_LNG) / GRID_CELL_SIZE_DEG);
    return `${row}-${col}`;
}

function getVisibleGridIds(bounds) {
    const visibleIds = new Set();
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    const startRow = Math.max(0, Math.floor((sw.lat() - GRID_ORIGIN_LAT) / GRID_CELL_SIZE_DEG));
    const endRow = Math.floor((ne.lat() - GRID_ORIGIN_LAT) / GRID_CELL_SIZE_DEG);
    const startCol = Math.max(0, Math.floor((sw.lng() - GRID_ORIGIN_LNG) / GRID_CELL_SIZE_DEG));
    const endCol = Math.floor((ne.lng() - GRID_ORIGIN_LNG) / GRID_CELL_SIZE_DEG);
    for (let row = startRow; row <= endRow; row++) {
        for (let col = startCol; col <= endCol; col++) {
            visibleIds.add(`${row}-${col}`);
        }
    }
    return visibleIds;
}

function createInfoContent(spot) {
    return `<div class="p-2 font-sans text-gray-800 max-w-xs"><h2 class="font-bold text-lg text-blue-800">${spot.name}</h2><p class="text-sm">${spot.address}</p>${spot.rating ? `<p class="text-sm">Rating: <strong>${spot.rating}</strong> (${spot.rating_count} ulasan)</p>` : ''}${spot.types && spot.types.length > 0 ? `<p class="text-sm">Jenis: ${spot.types.join(', ')}</p>` : ''}${spot.website ? `<p class="text-sm"><a href="${spot.website}" target="_blank" class="text-blue-500 hover:underline">Situs Web</a></p>` : ''}${spot.phone_number ? `<p class="text-sm">Telepon: ${spot.phone_number}</p>` : ''}</div>`;
}