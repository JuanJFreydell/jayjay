export interface Property {
  id: string;
  address: string;
  price: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  lat: number;
  lng: number;
  imageUrl?: string;
  description: string;
  propertyType: 'house' | 'condo' | 'townhouse';
  listingDate: string;
}

// Mock properties in Seacliff, Richmond District, San Francisco
export const mockProperties: Property[] = [
  {
    id: '1',
    address: '850 El Camino Del Mar, San Francisco, CA 94121',
    price: '$8,950,000',
    bedrooms: 5,
    bathrooms: 4,
    sqft: 4200,
    lat: 37.7858,
    lng: -122.4835,
    description: 'Stunning oceanfront estate with panoramic views of the Golden Gate Bridge and Pacific Ocean. Recently renovated with luxury finishes throughout.',
    propertyType: 'house',
    listingDate: '2024-11-01'
  },
  {
    id: '2',
    address: '920 Sea Cliff Avenue, San Francisco, CA 94121',
    price: '$6,750,000',
    bedrooms: 4,
    bathrooms: 3,
    sqft: 3600,
    lat: 37.7863,
    lng: -122.4842,
    description: 'Mediterranean-style villa in prestigious Sea Cliff neighborhood. Features grand entertaining spaces and mature gardens.',
    propertyType: 'house',
    listingDate: '2024-10-28'
  },
  {
    id: '3',
    address: '975 California Street, San Francisco, CA 94121',
    price: '$4,200,000',
    bedrooms: 3,
    bathrooms: 2,
    sqft: 2800,
    lat: 37.7851,
    lng: -122.4828,
    description: 'Contemporary home with floor-to-ceiling windows and private garden. Walking distance to China Beach and Lands End.',
    propertyType: 'house',
    listingDate: '2024-11-05'
  },
  {
    id: '4',
    address: '840 El Camino Del Mar, San Francisco, CA 94121',
    price: '$7,500,000',
    bedrooms: 4,
    bathrooms: 4,
    sqft: 3900,
    lat: 37.7856,
    lng: -122.4832,
    description: 'Architect-designed modern masterpiece with smart home technology. Breathtaking views and premium location.',
    propertyType: 'house',
    listingDate: '2024-10-15'
  },
  {
    id: '5',
    address: '950 Sea Cliff Avenue, San Francisco, CA 94121',
    price: '$5,850,000',
    bedrooms: 3,
    bathrooms: 3,
    sqft: 3200,
    lat: 37.7865,
    lng: -122.4838,
    description: 'Classic San Francisco architecture meets modern amenities. Private courtyard and gourmet kitchen with ocean glimpses.',
    propertyType: 'house',
    listingDate: '2024-11-08'
  }
];

// Function to get properties within a radius of a location
export const getPropertiesNearLocation = (
  lat: number,
  lng: number,
  radiusKm: number = 2
): Property[] => {
  return mockProperties.filter(property => {
    const distance = calculateDistance(lat, lng, property.lat, property.lng);
    return distance <= radiusKm;
  });
};

// Helper function to calculate distance between two coordinates
const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};