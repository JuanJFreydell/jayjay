'use client';

import { Property } from '../data/mockProperties';
import Link from 'next/link';

interface ListingsViewProps {
  properties: Property[];
  searchQuery: string;
}

export default function ListingsView({ properties, searchQuery }: ListingsViewProps) {
  return (
    <div className="w-full max-w-6xl">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-black mb-2">
            {properties.length} Properties Found
          </h2>
          {searchQuery && (
            <p className="text-gray-600">
              Showing results for: <span className="font-medium">{searchQuery}</span>
            </p>
          )}
        </div>

        {/* Listings Grid */}
        <div className="grid gap-6">
          {properties.map((property) => (
            <div
              key={property.id}
              className="border border-gray-200 rounded-2xl p-6 hover:shadow-md transition-shadow"
            >
              <div className="grid md:grid-cols-3 gap-6">
                {/* Property Image Placeholder */}
                <div className="bg-gray-200 rounded-xl h-48 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl mb-2">🏠</div>
                    <p className="text-gray-600 text-sm">Photo Coming Soon</p>
                  </div>
                </div>

                {/* Property Details */}
                <div className="md:col-span-2 flex flex-col justify-between">
                  <div>
                    {/* Price and Address */}
                    <div className="mb-4">
                      <h3 className="text-2xl font-bold text-black mb-1">
                        {property.price}
                      </h3>
                      <p className="text-gray-700 text-lg">
                        {property.address}
                      </p>
                    </div>

                    {/* Property Stats */}
                    <div className="flex items-center gap-6 text-gray-600 mb-4">
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{property.bedrooms}</span>
                        <span>bed</span>
                      </div>
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{property.bathrooms}</span>
                        <span>bath</span>
                      </div>
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{property.sqft.toLocaleString()}</span>
                        <span>sqft</span>
                      </div>
                      <span>•</span>
                      <span className="capitalize">{property.propertyType}</span>
                    </div>

                    {/* Description */}
                    <p className="text-gray-700 line-clamp-2 mb-4">
                      {property.description}
                    </p>

                    {/* Listing Date */}
                    <p className="text-sm text-gray-500">
                      Listed: {new Date(property.listingDate).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-3 mt-4">
                    <Link
                      href={`/listing/${property.id}`}
                      className="bg-black text-white px-6 py-2 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                    >
                      View Details
                    </Link>
                    <button className="border border-gray-300 text-black px-6 py-2 rounded-lg hover:border-black transition-colors">
                      Save Property
                    </button>
                    <button className="border border-gray-300 text-black px-4 py-2 rounded-lg hover:border-black transition-colors">
                      ♡
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {properties.length === 0 && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🏠</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                No Properties Found
              </h3>
              <p className="text-gray-500">
                Try searching for a different area or adjust your search criteria.
              </p>
            </div>
          )}
        </div>

        {/* Load More Button */}
        {properties.length > 0 && (
          <div className="text-center mt-8">
            <button className="bg-gray-100 text-black px-8 py-3 rounded-lg hover:bg-gray-200 transition-colors font-medium">
              Load More Properties
            </button>
          </div>
        )}
      </div>
    </div>
  );
}