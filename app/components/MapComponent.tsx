'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { mockProperties, getPropertiesNearLocation, Property } from '../data/mockProperties';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: '/leaflet/marker-icon-2x.png',
  iconUrl: '/leaflet/marker-icon.png',
  shadowUrl: '/leaflet/marker-shadow.png',
});

// Custom icon for property listings
const propertyIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25" fill="none">
      <circle cx="12.5" cy="12.5" r="12" fill="#000000" stroke="#ffffff" stroke-width="1"/>
      <text x="12.5" y="17" text-anchor="middle" fill="white" font-size="12" font-weight="bold">$</text>
    </svg>
  `),
  iconSize: [25, 25],
  iconAnchor: [12.5, 25],
  popupAnchor: [0, -25],
});

// Custom icon for search location
const searchIcon = new L.Icon({
  iconRetinaUrl: '/leaflet/marker-icon-2x.png',
  iconUrl: '/leaflet/marker-icon.png',
  shadowUrl: '/leaflet/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

interface MapComponentProps {
  searchQuery: string;
}

// Component to handle map center changes
function ChangeMapView({ center }: { center: LatLngTuple }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 13);
  }, [center, map]);
  return null;
}

export default function MapComponent({ searchQuery }: MapComponentProps) {
  const [position, setPosition] = useState<LatLngTuple>([37.7858, -122.4835]); // Default to Seacliff, SF
  const [loading, setLoading] = useState(false);
  const [locationName, setLocationName] = useState('');
  const [nearbyProperties, setNearbyProperties] = useState<Property[]>([]);

  const geocodeLocation = async (query: string) => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1&addressdetails=1`
      );
      const data = await response.json();

      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);
        const newPosition: LatLngTuple = [lat, lon];
        setPosition(newPosition);
        setLocationName(data[0].display_name);

        // Get nearby properties
        const nearby = getPropertiesNearLocation(lat, lon, 5); // 5km radius
        setNearbyProperties(nearby);

        console.log('Found location:', data[0].display_name, 'at', newPosition);
        console.log('Nearby properties:', nearby.length);
      } else {
        console.log('No results found for:', query);
      }
    } catch (error) {
      console.error('Geocoding error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Show all Seacliff properties by default
    setNearbyProperties(mockProperties);

    if (searchQuery.trim()) {
      geocodeLocation(searchQuery);
    }
  }, [searchQuery]);

  return (
    <div className="relative w-full h-full">
      {loading && (
        <div className="absolute top-4 left-4 z-[1000] bg-white px-3 py-1 rounded-lg shadow-md">
          <span className="text-sm text-gray-600">Searching for {searchQuery}...</span>
        </div>
      )}

      {/* Properties count indicator */}
      <div className="absolute top-4 right-4 z-[1000] bg-black text-white px-3 py-1 rounded-lg shadow-md">
        <span className="text-sm font-medium">{nearbyProperties.length} Listings</span>
      </div>

      <MapContainer
        center={position}
        zoom={15}
        style={{ height: '100%', width: '100%', filter: 'grayscale(100%)' }}
        scrollWheelZoom={true}
      >
        <ChangeMapView center={position} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Search location marker */}
        <Marker position={position} icon={searchIcon}>
          <Popup>
            <div className="text-black">
              <div className="font-medium">{searchQuery}</div>
              {locationName && (
                <div className="text-xs text-gray-600 mt-1">{locationName}</div>
              )}
            </div>
          </Popup>
        </Marker>

        {/* Property markers */}
        {nearbyProperties.map((property) => (
          <Marker
            key={property.id}
            position={[property.lat, property.lng]}
            icon={propertyIcon}
          >
            <Popup maxWidth={300} className="property-popup">
              <div className="text-black p-2">
                <div className="font-bold text-lg text-black mb-1">{property.price}</div>
                <div className="text-sm font-medium mb-2">{property.address}</div>
                <div className="text-xs text-gray-600 mb-2">
                  {property.bedrooms} bed • {property.bathrooms} bath • {property.sqft.toLocaleString()} sqft
                </div>
                <div className="text-xs text-gray-700 leading-relaxed mb-3">
                  {property.description}
                </div>
                <div className="text-xs text-gray-500 mb-3">
                  Listed: {new Date(property.listingDate).toLocaleDateString()}
                </div>
                <a
                  href={`/listing/${property.id}`}
                  className="inline-block w-full bg-black text-white text-center py-2 px-3 rounded-lg text-xs font-medium hover:bg-gray-800 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(`/listing/${property.id}`, '_blank');
                  }}
                >
                  View Details →
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}