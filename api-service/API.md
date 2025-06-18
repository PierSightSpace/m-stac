# PierSight STAC API Documentation

Welcome to the PierSight STAC API! This API provides access to satellite imagery and maritime surveillance data using the [SpatioTemporal Asset Catalog (STAC)](https://stacspec.org/) specification.

---

## Overview

- **Base URL:** `https://stac.eodata.piersight.space/v1/`
- **Version:** 1.0.0
- **Format:** JSON (GeoJSON for spatial data)
- **Authentication:** JWT Bearer Token (see below)
- **Rate Limiting:** 5 requests per minute per IP

---

## Authentication

Most endpoints require JWT authentication. Include your token in the `Authorization` header:

```http
Authorization: Bearer <your_token>
```

---

## Rate Limiting

- **Default:** 5 requests per minute per IP
- **Cache:** 1 hour for search results, 24 hours for static content
- **Error:** Exceeding the limit returns HTTP 429

---

## Error Codes

| Code | Meaning                        | Example Message                                      |
|------|--------------------------------|------------------------------------------------------|
| 400  | Bad Request                    | Invalid input parameters                             |
| 401  | Unauthorized                   | Missing or invalid authentication token              |
| 404  | Not Found                      | No data found for given input                        |
| 422  | Unprocessable Entity           | Invalid coordinates; Must be in WKT format           |
| 429  | Too Many Requests              | Rate limit exceeded. Try again later.                |
| 500  | Internal Server Error          | Unexpected server error                              |

---

# Table of Contents

- [Catalog APIs](#catalog-apis)
- [Collections APIs](#collections-apis)
- [Search APIs](#search-apis)
- [Items APIs](#items-apis)
- [Support](#support)

---

# Catalog APIs

## 1. Get STAC Catalog Root

**GET** `/v1/`

Returns the root STAC catalog metadata, including links to all collections and API endpoints.

**Example URL:**
```
https://stac.eodata.piersight.space/v1/
```

**Parameters:**
| Name | In   | Type | Required | Description |
|------|------|------|----------|-------------|
| -    | -    | -    | -        | No parameters |

**Response Example:**
```json
{
  "type": "Catalog",
  "id": "PierSight Space Maritime Servilliance Data",
  "title": "PierSight Catalog",
  "description": "PierSight Catalog provides access to high-resolution, all-weather Synthetic Aperture Radar (SAR) imagery and maritime surveillance data collected by the PierSight satellite constellation...",
  "stac_version": "1.0.0",
  "links": [
    { "rel": "self", "mime_type": "application/geo+json", "href": "https://stac.eodata.piersight.space/v1/" },
    { "rel": "child", "mime_type": "application/geo+json", "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01", "title": "PierSight-V01 Collection" },
    { "rel": "search", "type": "application/geo+json", "href": "https://stac.eodata.piersight.space/v1/search" }
    // ...more links
  ],
  "stac_extensions": []
}
```

---

## 2. Get API Conformance

**GET** `/v1/conformance`

Lists the conformance classes that the API implements.

**Example URL:**
```
https://stac.eodata.piersight.space/v1/conformance
```

**Parameters:**
| Name | In   | Type | Required | Description |
|------|------|------|----------|-------------|
| -    | -    | -    | -        | No parameters |

**Response Example:**
```json
{
  "conformsTo": [
    "https://api.stacspec.org/v1.0.0/core",
    "https://api.stacspec.org/v1.0.0/collections",
    "https://api.stacspec.org/v1.0.0/search",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
  ]
}
```

---

# Collections APIs

## 1. List Collections

**GET** `/v1/collections`

Returns metadata for all available collections.

**Example URL:**
```
https://stac.eodata.piersight.space/v1/collections
```

**Parameters:**
| Name | In   | Type | Required | Description |
|------|------|------|----------|-------------|
| -    | -    | -    | -        | No parameters |

**Response Example:**
```json
[
  {
    "id": "PierSight_V01",
    "type": "Collection",
    "stac_version": "1.0.0",
    "title": "PierSight V01 Collection",
    "description": "SAR imagery from PierSight V01 satellite",
    "license": "proprietary",
    "extent": {
      "spatial": { "bbox": [[-180, -90, 180, 90]] },
      "temporal": { "interval": [["2024-01-01T00:00:00Z"]] }
    },
    "links": [
      { "rel": "self", "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01" }
    ],
    "providers": []
  }
]
```

---

## 2. Get Collection by ID

**GET** `/v1/collections/{collectionId}`

Returns metadata for a specific collection.

**Example URL:**
```
https://stac.eodata.piersight.space/v1/collections/PierSight_V01
```

**Parameters:**
| Name         | In   | Type   | Required | Description                |
|--------------|------|--------|----------|----------------------------|
| collectionId | path | string | Yes      | The ID of the collection   |

**Response Example:**
```json
[
  {
    "id": "PierSight_V01",
    "type": "Collection",
    "stac_version": "1.0.0",
    "title": "PierSight V01 Collection",
    "description": "SAR imagery from PierSight V01 satellite",
    "license": "proprietary",
    "extent": {
      "spatial": { "bbox": [[-180, -90, 180, 90]] },
      "temporal": { "interval": [["2024-01-01T00:00:00Z"]] }
    },
    "links": [
      { "rel": "self", "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01" }
    ],
    "providers": []
  }
]
```

---

# Search APIs

## 1. Search STAC Items

**GET** `/v1/search`

Search for STAC items using filters.

**Query Parameters:**
| Name         | In    | Type   | Required | Description                                              | Example                  |
|--------------|-------|--------|----------|----------------------------------------------------------|--------------------------|
| collectionId | query | string | No       | Filter by collection ID                                  | PierSight_V01            |
| bbox         | query | string | No       | Bounding box: minLon,minLat,maxLon,maxLat                | -180,-90,180,90          |
| start_time   | query | string | No       | Start time (ISO 8601)                                    | 2024-01-01T00:00:00Z     |
| stop_time    | query | string | No       | End time (ISO 8601)                                      | 2024-12-31T23:59:59Z     |
| limit        | query | int    | No       | Max items per page (default: 10, max: 50)                | 10                       |
| offset       | query | int    | No       | Offset for pagination                                    | 0                        |

**Example URL:**
```
https://stac.eodata.piersight.space/v1/search?collectionId=PierSight_V01&bbox=-180,-90,180,90&start_time=2024-01-01T00:00:00Z&stop_time=2024-12-31T23:59:59Z&limit=10&offset=0
```

**Response Example:**
```json
{
  "total_count": 100,
  "products": [
    {
      "id": "item1",
      "type": "Feature",
      "geom_type": "Polygon",
      "bounding_box_wkb": { "coordinates": [[]] }
      // ...other fields
    }
  ],
  "next": "https://stac.eodata.piersight.space/v1/search?offset=10"
}
```

---

# Items APIs

## 1. List Items in a Collection

**GET** `/v1/collections/{collectionId}/items`

Returns all items for a given collection, with optional filters.

**Parameters:**
| Name         | In    | Type   | Required | Description                                              | Example                  |
|--------------|-------|--------|----------|----------------------------------------------------------|--------------------------|
| collectionId | path  | string | Yes      | The ID of the collection                                 | PierSight_V01            |
| bbox         | query | string | No       | Bounding box: minLon,minLat,maxLon,maxLat                | -180,-90,180,90          |
| start_time   | query | string | No       | Start time (ISO 8601)                                    | 2024-01-01T00:00:00Z     |
| stop_time    | query | string | No       | End time (ISO 8601)                                      | 2024-12-31T23:59:59Z     |
| limit        | query | int    | No       | Max items per page (default: 10, max: 15)                | 10                       |
| offset       | query | int    | No       | Offset for pagination                                    | 0                        |

**Example URL:**
```
https://stac.eodata.piersight.space/v1/collections/PierSight_V01/items?bbox=-180,-90,180,90&start_time=2024-01-01T00:00:00Z&stop_time=2024-12-31T23:59:59Z&limit=10&offset=0
```

**Response Example:**
```json
{
  "total_count": 100,
  "products": [
    {
      "id": "item1",
      "type": "Feature",
      "geom_type": "Polygon",
      "bounding_box_wkb": { "coordinates": [[]] }
      // ...other fields
    }
  ],
  "next": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01/items?offset=10"
}
```

---

## 2. Get Item by ID

**GET** `/v1/collections/{collectionId}/items/{itemId}`

Returns a specific item from a collection.

**Parameters:**
| Name         | In   | Type   | Required | Description                | Example         |
|--------------|------|--------|----------|----------------------------|-----------------|
| collectionId | path | string | Yes      | The ID of the collection   | PierSight_V01   |
| itemId       | path | string | Yes      | The ID of the item         | item1           |

**Example URL:**
```
https://stac.eodata.piersight.space/v1/collections/PierSight_V01/items/item1
```

**Response Example:**
```json
{
  "total_count": 1,
  "products": [
    {
      "id": "item1",
      "type": "Feature",
      "geom_type": "Polygon",
      "bounding_box_wkb": { "coordinates": [[]] }
      // ...other fields
    }
  ],
  "next": null
}
```

---

## 3. Download Item Asset (ZIP)

**GET** `/v1/collections/{collectionId}/items/{itemId}/download`

Downloads the complete asset package (ZIP) for a given STAC item.

**Parameters:**
| Name         | In   | Type   | Required | Description                | Example         |
|--------------|------|--------|----------|----------------------------|-----------------|
| collectionId | path | string | Yes      | The ID of the collection   | PierSight_V01   |
| itemId       | path | string | Yes      | The ID of the item         | item1           |

**Example URL:**
```
https://stac.eodata.piersight.space/v1/collections/PierSight_V01/items/item1/download
```

**Response:**
- **Content-Type:** `application/zip`
- **Body:** Binary ZIP file containing the item's assets
- **Success (200):** Returns the ZIP file for download
- **Error (404):** If the item or asset does not exist
- **Error (403):** If you do not have permission to access the asset

---

# Support

- **Website:** [https://piersight.space](https://piersight.space)
- **Contact:** support@piersight.space

---

© 2024 PierSight Space. All rights reserved. 