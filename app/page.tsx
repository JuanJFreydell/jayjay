'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { mockProperties, getPropertiesNearLocation } from './data/mockProperties';
import ListingsView from './components/ListingsView';

const MapComponent = dynamic(() => import('./components/MapComponent'), {
  ssr: false
});

interface SearchSuggestion {
  place_id: string;
  display_name: string;
  lat: string;
  lon: string;
}

type ViewMode = 'map' | 'listings';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('map');
  const [currentProperties, setCurrentProperties] = useState(mockProperties);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const fetchSuggestions = async (query: string) => {
    if (!query.trim() || query.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`
      );
      const data = await response.json();
      setSuggestions(data || []);
      setShowSuggestions(true);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);
  };

  const handleSearch = async (query?: string) => {
    const searchTerm = query || searchQuery;
    if (searchTerm.trim()) {
      setShowResults(true);
      setShowSuggestions(false);
      setSelectedIndex(-1);

      // Filter properties based on search location
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchTerm)}&limit=1&addressdetails=1`
        );
        const data = await response.json();

        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lon = parseFloat(data[0].lon);
          const nearbyProperties = getPropertiesNearLocation(lat, lon, 10); // 10km radius
          setCurrentProperties(nearbyProperties);
        } else {
          // If no geocoding result, show all properties
          setCurrentProperties(mockProperties);
        }
      } catch (error) {
        console.error('Error filtering properties:', error);
        setCurrentProperties(mockProperties);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions) {
      if (e.key === 'Enter') {
        handleSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > -1 ? prev - 1 : prev);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          const selected = suggestions[selectedIndex];
          setSearchQuery(selected.display_name);
          handleSearch(selected.display_name);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const selectSuggestion = (suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.display_name);
    handleSearch(suggestion.display_name);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <div className="flex flex-col items-center justify-center min-h-screen px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-black mb-8">
            Find Your Dream Home Faster Than Ever
          </h1>

          <div className="w-full max-w-2xl relative" ref={searchRef}>
            <input
              type="text"
              value={searchQuery}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              placeholder="Search for neighborhoods, cities, or areas..."
              className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-full focus:outline-none focus:border-black transition-colors"
            />

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-2xl shadow-lg z-10 max-h-64 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={suggestion.place_id}
                    className={`px-6 py-3 cursor-pointer transition-colors ${
                      index === selectedIndex
                        ? 'bg-gray-100'
                        : 'hover:bg-gray-50'
                    } ${index === 0 ? 'rounded-t-2xl' : ''} ${
                      index === suggestions.length - 1 ? 'rounded-b-2xl' : 'border-b border-gray-100'
                    }`}
                    onClick={() => selectSuggestion(suggestion)}
                  >
                    <div className="text-black font-medium text-sm">
                      {suggestion.display_name}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {showResults && (
          <div className="w-full max-w-6xl mt-8">
            {/* View Toggle Bar */}
            <div className="mb-6">
              <div className="bg-white border border-gray-200 rounded-2xl p-2 inline-flex">
                <button
                  onClick={() => setViewMode('map')}
                  className={`px-6 py-3 rounded-xl font-medium transition-all ${
                    viewMode === 'map'
                      ? 'bg-black text-white shadow-sm'
                      : 'text-gray-600 hover:text-black hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Map View
                  </div>
                </button>
                <button
                  onClick={() => setViewMode('listings')}
                  className={`px-6 py-3 rounded-xl font-medium transition-all ${
                    viewMode === 'listings'
                      ? 'bg-black text-white shadow-sm'
                      : 'text-gray-600 hover:text-black hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    Listings View
                  </div>
                </button>
              </div>

              <div className="ml-4 inline-flex items-center text-sm text-gray-600">
                <span>{currentProperties.length} properties found</span>
              </div>
            </div>

            {/* Content Area */}
            {viewMode === 'map' ? (
              <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                <div className="h-96">
                  <MapComponent searchQuery={searchQuery} />
                </div>
              </div>
            ) : (
              <ListingsView properties={currentProperties} searchQuery={searchQuery} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
