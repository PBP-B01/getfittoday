// =================================================================================
// Global Variables & Configuration
// =================================================================================

let map;
let infoWindow;
let userLocationMarker = null;

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
async function initMap() {
    try {
        let initialCoords = { lat: -6.370403, lng: 106.826946 };
        let initialZoom = 17;

        const [boundaries, position] = await Promise.all([
            fetchMapBoundaries(),
            getUserLocation()
        ]);

        let restrictionBounds = null;
        if (boundaries) {
            const buffer = 0.018;
            restrictionBounds = {
                north: boundaries.north + buffer, south: boundaries.south - buffer,
                east: boundaries.east + buffer, west: boundaries.west - buffer,
            };

            // If user grants location permission, override the default start point
            if (position) {
                const { latitude: userLat, longitude: userLng } = position.coords;
                if (userLat < boundaries.north && userLat > boundaries.south && userLng < boundaries.east && userLng > boundaries.west) {
                    initialCoords = { lat: userLat, lng: userLng };
                    initialZoom = 16;
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
        myLocationControl: false,
        clickableIcons: false,
        mapId: "7e0c35add3b17dafe20eac87",
    });
    
    infoWindow = new google.maps.InfoWindow({
        pixelOffset: new google.maps.Size(0, -10), 
    });

    google.maps.event.addListener(infoWindow, 'domready', () => {
        const iwOuter = document.querySelector('.gm-style-iw-c');
        if (!iwOuter) return;

        const closeBtn = iwOuter.querySelector('button');
        if (closeBtn) closeBtn.style.display = 'none';

        const iwBackground = iwOuter.parentElement;
        iwBackground.style.boxShadow = 'none';
        iwBackground.style.background = 'transparent';
        
        const tail = iwBackground.querySelector('.gm-style-iw-tc');
        if (tail) tail.style.display = 'none';
    });


    // Attach event listeners
    map.addListener('idle', () => updateSpotsForView(map));
    document.getElementById('fullscreen-toggle-btn').addEventListener('click', toggleFullScreen);
    document.getElementById('sidebar-toggle-btn').addEventListener('click', () => {
        document.body.classList.toggle('sidebar-visible');
    });
    
    createCenterOnMeButton();
}

initMap();

// =================================================================================
// Data Loading (Grid System)
// =================================================================================
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
            const promises = newGridIdsToLoad.map(id => fetchGridData(id));
            await Promise.all(promises);
        }

        await renderSpots(visibleGridIds);
        loadedGridIds = visibleGridIds;

    } finally {
        isUpdatingSpots = false;
    }
}

// Fetches spot data for a specific grid ID from the Django API.
async function fetchGridData(gridId) {
    console.log(`Fetching grid ${gridId} from server...`);
    const url = `/api/fitness-spots/?gridId=${gridId}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        clientGridCache[gridId] = data;
        return data;
    } catch (error) {
        console.error(`Failed to fetch data for grid ${gridId}:`, error);
        clientGridCache[gridId] = { spots: [] };
        return null;
    }
}

// Renders all markers and sidebar cards for the currently visible grid cells.
async function renderSpots(visibleGridIds) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    
    Object.values(markers).forEach(marker => marker.map = null);
    markers = {};
    const cardsContainer = document.getElementById('spot-cards-container');
    cardsContainer.innerHTML = '';
    
    let totalSpotsRendered = 0;

    for (const gridId of visibleGridIds) {
        const data = clientGridCache[gridId];
        if (data && data.spots) {
            data.spots.forEach(spot => {
                if (markers[spot.place_id]) return;

                totalSpotsRendered++;
                const lat = parseFloat(spot.latitude);
                const lng = parseFloat(spot.longitude);
                if (isNaN(lat) || isNaN(lng)) return;

                const marker = new AdvancedMarkerElement({ position: { lat, lng }, map, title: spot.name });
                markers[spot.place_id] = marker;
                
                const card = createSpotCard(spot);
                cardsContainer.appendChild(card);
                
                marker.addListener("click", () => showSpotDetails(spot));
                card.addEventListener('click', () => showSpotDetails(spot, true));
            });
        }
    }

    const emptyState = document.getElementById('sidebar-empty-state');
    if (totalSpotsRendered === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }

    if (currentActiveCardId && document.getElementById(`card-${currentActiveCardId}`)) {
        highlightSpotCard(currentActiveCardId);
    }
}

// =================================================================================
// UI Interaction & User Location
// =================================================================================

function showSpotDetails(spot, shouldZoom = false) {
    const marker = markers[spot.place_id];
    if (!marker) return;

    const isMobile = window.innerWidth < 768;
    const isCardClick = shouldZoom;

    // Pan the map and show the InfoWindow
    const showMarkerInfo = () => {
        programmaticPan = true;
        map.panTo(marker.position);
        if (isCardClick) map.setZoom(16);

        infoWindow.setContent(createInfoContent(spot));
        infoWindow.open({ anchor: marker, map });
        highlightSpotCard(spot.place_id);
    };

    let sidebarVisibilityChanged = false; // Flag to track if we need a delay

    // --- Logic for Marker Clicks ---
    if (!isCardClick) {
        // On desktop, if sidebar is hidden, show it. This is a change in visibility.
        if (!isMobile && document.body.classList.contains('full-screen-mode') && !document.body.classList.contains('sidebar-visible')) {
            document.body.classList.add('sidebar-visible');
            sidebarVisibilityChanged = true;
        }
    }
    // --- Logic for Card Clicks ---
    else {
        // On mobile, hide the sidebar. This is a change in visibility.
        if (isMobile) {
            document.body.classList.remove('sidebar-visible');
            sidebarVisibilityChanged = true;
        }
    }
    
    // --- Execute the Action ---
    if (sidebarVisibilityChanged) {
        // If the sidebar started an animation, wait for it to begin before showing the marker info
        setTimeout(showMarkerInfo, 100);
    } else {
        // If the sidebar's state did not change, show the info immediately
        showMarkerInfo();
    }
}

//Creates or updates a blue dot marker representing the user's location.
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

// Creates the "Center on Me" button and adds it to the map controls.
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
// Helper Functions
// =================================================================================

function highlightSpotCard(placeId) {
    if (currentActiveCardId && currentActiveCardId !== placeId) {
        const oldCard = document.getElementById(`card-${currentActiveCardId}`);
        if (oldCard) oldCard.classList.remove('active');
    }
    const newCard = document.getElementById(`card-${placeId}`);
    if (newCard) {
        newCard.classList.add('active');
        // Only scroll if the sidebar is visible
        if (document.body.classList.contains('sidebar-visible')) {
            setTimeout(() => newCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
        }
    }
    currentActiveCardId = placeId;
}

function createSpotCard(spot) {
    const card = document.createElement('div');
    card.id = `card-${spot.place_id}`;
    card.className = 'spot-card';
    
    const starIcon = `<svg viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/></svg>`;

    const ratingHTML = spot.rating 
        ? `<div class="spot-card-rating">
                ${starIcon}
                <strong>${spot.rating}</strong> 
                <span style="color: #4a4a4a; font-weight: 400; margin-left: 4px;">(${spot.rating_count} reviews)</span>
           </div>` 
        : '';

    card.innerHTML = `
        <h3>${spot.name}</h3>
        <p>${spot.address}</p>
        ${ratingHTML}
    `;
    return card;
}

function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) { resolve(null); return; }
        navigator.geolocation.getCurrentPosition(resolve, () => resolve(null), { timeout: 5000 });
    });
}

function toggleFullScreen() {
    const isFullScreen = document.body.classList.toggle('full-screen-mode');

    if (!isFullScreen) {
        document.body.classList.remove('sidebar-visible');
    }

    const enterIcon = document.getElementById('fullscreen-enter-icon');
    const exitIcon = document.getElementById('fullscreen-exit-icon');

    if (isFullScreen) {
        enterIcon.classList.add('hidden');
        exitIcon.classList.remove('hidden');
    } else {
        enterIcon.classList.remove('hidden');
        exitIcon.classList.add('hidden');
    }
    
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
    const starIcon = `<svg width="16" height="16" viewBox="0 0 20 20" style="vertical-align: middle; fill: #233D8C;"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/></svg>`;
    
    let ratingHTML = '';
    if (spot.rating) {
        ratingHTML = `
            <div style="display: flex; align-items: center; gap: 5px; font-size: 0.9rem; margin-top: 10px; color: #233D8C;">
                ${starIcon}
                <strong style="font-weight: 700;">${spot.rating}</strong>
                <span style="color: #4a4a4a; font-weight: 400; margin-left: 4px;">(${spot.rating_count} reviews)</span>
            </div>
        `;
    }

    return `
        <div style="font-family: sans-serif; max-width: 280px; border-radius: 12px; overflow: hidden;">
            <div style="background-color: #233D8C; color: white; padding: 10px 15px; font-weight: bold; font-size: 1.1rem; position: relative;">
                ${spot.name}
                <button title="Close" onclick="infoWindow.close()" style="position: absolute; top: 0px; right: 8px; background: none; border: none; color: white; font-size: 24px; cursor: pointer; line-height: 1.5; font-weight: 300;">&times;</button>
            </div>
            <div style="background-color: #E8B400; color: #233D8C; padding: 15px;">
                <p style="font-size: 0.85rem; color: #333; margin-bottom: 4px; margin-top: 0;">${spot.address}</p>
                ${ratingHTML}
            </div>
        </div>
    `;
}