// A single InfoWindow instance to be shared by all markers for better performance.
let infoWindow;

// Main function to initialize the map
async function initMap() {
    const initialCoords = { lat: -6.2088, lng: 106.8456 }; 

    try {
        const { Map } = await google.maps.importLibrary("maps");
        
        const map = new Map(document.getElementById("map"), {
            center: initialCoords,
            zoom: 11,
            disableDefaultUI: true,
            zoomControl: true,
            mapId: "7e0c35add3b17dafe20eac87", // ❗ IMPORTANT: Paste your Map ID here
        });
        
        // Initialize the single InfoWindow, available for all markers
        infoWindow = new google.maps.InfoWindow();

        // Load the fitness spots onto the map
        loadFitnessSpots(map);

    } catch (error) {
        console.error("Gagal memuat Google Maps:", error);
    }
}

// Fetches spot data from your API (or cache in future)
async function fetchSpotsData() {
    try {
        const response = await fetch('/api/fitness-spots/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Gagal mengambil data fitness spots:', error);
        return null; // Return null on failure so the app doesn't crash
    }
}

// Creates the HTML content for a spot's InfoWindow
function createInfoContent(spot) {
    return `
        <div class="p-2 font-sans text-gray-800 max-w-xs">
            <h2 class="font-bold text-lg text-blue-800">${spot.name}</h2>
            <p class="text-sm">${spot.address}</p>
            ${spot.rating ? `<p class="text-sm">Rating: <strong>${spot.rating}</strong> (${spot.rating_count} ulasan)</p>` : ''}
            ${spot.types && spot.types.length > 0 ? `<p class="text-sm">Jenis: ${spot.types.join(', ')}</p>` : ''}
            ${spot.website ? `<p class="text-sm"><a href="${spot.website}" target="_blank" class="text-blue-500 hover:underline">Situs Web</a></p>` : ''}
            ${spot.phone_number ? `<p class="text-sm">Telepon: ${spot.phone_number}</p>` : ''}
        </div>
    `;
}

// Creates a single marker and adds it to the map
function createSpotMarker(spot, map, AdvancedMarkerElement) {
    const lat = parseFloat(spot.latitude);
    const lng = parseFloat(spot.longitude);

    if (isNaN(lat) || isNaN(lng)) {
        console.warn("Data lokasi tidak valid untuk:", spot.name);
        return; // Skip this invalid spot
    }

    const marker = new AdvancedMarkerElement({
        position: { lat, lng },
        map,
        title: spot.name,
    });

    marker.addListener("click", () => {
        // Set the content for the single infoWindow and open it
        infoWindow.setContent(createInfoContent(spot));
        infoWindow.open({
            anchor: marker,
            map,
        });
    });
}

// Main function to process and display all fitness spots
async function loadFitnessSpots(map) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    
    const data = await fetchSpotsData();

    if (data && data.spots) {
        data.spots.forEach(spot => {
            createSpotMarker(spot, map, AdvancedMarkerElement);
        });
    }
}

// Start the application
initMap();