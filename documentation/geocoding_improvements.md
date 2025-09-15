# Geocoding Improvements for Rural and Urban Locations

## Problem
The Google Maps API often provides inaccurate coordinates for many locations in India, especially in rural areas and some urban neighborhoods. This resulted in incorrect farm locations being displayed on the dashboard map, affecting user experience and functionality.

## Solution
We implemented a comprehensive, multi-layered geocoding system that handles locations across India:

1. **Hierarchical Location Database**
   - PIN code mapping for precise location identification
   - District-level database with sub-location mapping
   - Area/neighborhood-specific coordinates within cities
   - State-level fallbacks when other methods fail

2. **Smart Geocoding Logic**
   - Pattern recognition to identify specific neighborhoods
   - Custom coordinate mapping for known problematic locations
   - Progressive fallback system to ensure coordinates are always provided
   - Threshold-based coordinate verification to prevent false positives

3. **Maintenance Tools**
   - Comprehensive coordinate checking system for all farm locations
   - Detailed reporting of potential coordinate issues
   - Automated correction of incorrect coordinates
   - Location database expansion framework

## Location Examples
Our system now accurately maps various locations:

### Rural Areas
- **Pawas, Ratnagiri, Maharashtra (PIN: 415616)** → (16.991, 73.299)
- **Villages in Kolhapur, Maharashtra** → District-specific mapping

### Urban Neighborhoods
- **Vartak Nagar, Thane, Maharashtra** → (19.222, 72.961)
- **Thane West, Maharashtra** → (19.218, 72.978)
- **Andheri, Mumbai, Maharashtra** → (19.114, 72.870)

### Tier 2/3 Cities
- **Nashik, Maharashtra** → (19.998, 73.790)
- **Vadodara, Gujarat** → (22.307, 73.181)
- **Udaipur, Rajasthan** → (24.585, 73.713)

## Implementation Details
The geocoding system uses a tiered approach:

1. First checks against PIN code database (most accurate)
2. Then checks district + location-specific mappings
3. Attempts geocoding with Google Maps API
4. Falls back to district-level coordinates if needed
5. Uses state-level coordinates as final resort

This ensures reliable location mapping even when Internet connectivity or third-party services are unreliable.

## Google API Configuration

For the Google Maps Geocoding API integration to work properly, you need to configure your API key correctly:

1. **Enable the Correct APIs**
   - In Google Cloud Console, enable both "Maps JavaScript API" AND "Geocoding API"
   - Simply enabling the Maps JavaScript API is not sufficient

2. **Set Up Billing**
   - Geocoding API requires billing to be enabled on your project
   - Google provides $200 free credit per month (as of March 2025)

3. **API Key Restrictions**
   - Set proper API key restrictions under "Credentials" in Google Cloud Console
   - For server-side requests: configure IP address restrictions
   - For client-side requests: add HTTP referrer restrictions

4. **Pricing Considerations**
   - Geocoding API is billed separately from Maps JavaScript API
   - Current pricing: $0.005 per request (first 100,000 requests per month)

If you're experiencing "REQUEST_DENIED" errors, verify that:
- The correct API (Geocoding API) is enabled
- Billing is set up for your Google Cloud Project
- Your API key restrictions aren't blocking the requests

## Usage
To check farm coordinates:
```
python check_farm_coordinates.py
```

For regular maintenance (view only):
```
python geocode_maintenance.py --verbose
```

To fix incorrect coordinates:
```
python geocode_maintenance.py --fix
```

## Future Improvements
- Expand location database with more PIN codes and neighborhoods
- Implement user feedback mechanism for location correction
- Develop admin interface for location database management
- Integrate with additional geocoding services for validation
- Add machine learning to identify patterns in addresses for better mapping 