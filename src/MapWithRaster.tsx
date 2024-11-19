import React, {useEffect, useRef, useState} from 'react';
import axios from 'axios';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css';
import {parseStringPromise} from 'xml2js';

const capabilitiesUrl: string = 'view-source:http://localhost:8080/geoserver/gwc/service/wmts?layer=vegetaion-anomalies:va-test2&tilematrixset=EPSG:4326&Service=WMTS&Request=GetCapabilities&Version=1.1.1';

interface TileMatrixLimit {
    TileMatrix: string;
    MinTileRow: number;
    MaxTileRow: number;
    MinTileCol: number;
    MaxTileCol: number;
}

const MapWithRaster = () => {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const [osmOpacity, setOsmOpacity] = useState(1.0);
    const [satelliteOpacity, setSatelliteOpacity] = useState(0.0);
    const [anomaliesOpacity, setAnomaliesOpacity] = useState(0.8);
    const [daysOffset, setDaysOffset] = useState(0);
    const mapRef = useRef<maplibreGl.Map | null>(null);
    const [tileMatrixLimits, setTileMatrixLimits] = useState<TileMatrixLimit[]>([]);
    const [resourceUrl, setResourceUrl] = useState<string | null>(null);

    const formatDateWithOffset = (baseDate: Date, offsetDays: number, addHyphens: boolean): string => {
        const date: Date = new Date(baseDate)
        date.setDate(baseDate.getDate() + offsetDays);
        const separator: string = addHyphens ? '-' : '';
        const formattedDate = date.getFullYear().toString() + separator +
            (date.getMonth() + 1).toString().padStart(2, '0') + separator +
            date.getDate().toString().padStart(2, '0');
        return formattedDate;
    }

    useEffect(() => {
        if (mapContainerRef.current) {
            const map = new maplibreGl.Map({
                container: mapContainerRef.current as HTMLElement,
                style: 'https://demotiles.maplibre.org/style.json',
                center: [0, 0],
                zoom: 2,
            });

            map.on('load', () => {
                // Layer 1: OpenStreetMap base raster layer
                map.addSource('osm-source', {
                    type: 'raster',
                    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                    tileSize: 256,
                });

                map.addLayer({
                    id: 'osm-layer',
                    type: 'raster',
                    source: 'osm-source',
                    paint: {
                        'raster-opacity': osmOpacity,
                    },
                });

                // Layer 2: Stamen Terrain layer
                map.addSource('satellite-source', {
                    type: 'raster',
                    tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
                    tileSize: 256,
                });

                map.addLayer({
                    id: 'satellite-layer',
                    type: 'raster',
                    source: 'satellite-source',
                    paint: {
                        'raster-opacity': satelliteOpacity,
                    },
                });

                // Layer 3: Anomalies layer
                const date = formatDateWithOffset(new Date(2018, 0, 5), daysOffset, false);
                map.addSource('anomalies-source', {
                    type: 'raster',
                    // tiles: [`http://localhost:8080/${date}/{z}/{x}/{y}.png`],
                    tiles: [`http://localhost:8080/geoserver/gwc/service/wmts?layer=vegetaion-anomalies:va-test2&tilematrixset=EPSG:4326&Service=WMTS&Request=GetTile&Version=1.1.1&Format=image/png&TileMatrix=EPSG:4326:{z}&TileCol={y}&TileRow={x}`],
                    tileSize: 512,
                });

                map.addLayer({
                    id: 'anomalies-layer',
                    type: 'raster',
                    source: 'anomalies-source',
                    paint: {
                        'raster-opacity': anomaliesOpacity,
                    },
                });

                // Save map reference after loading is complete
                mapRef.current = map;
            });

            return () => map.remove();
        }

        const fetchAndParseXML = async () => {
            try {
                const response = await axios.get(capabilitiesUrl, {
                    headers: {
                        'Content-Type': 'application/xml'
                    }
                });

                const result = await parseStringPromise(response.data);

                // Navigate to the TileMatrixLimits for 'vegetaion-anomalies:va-test2'
                const layer = result.Capabilities.Contents[0].Layer.find(
                    (l: any) => l['ows:Identifier'][0] === 'vegetaion-anomalies:va-test2'
                );

                // Take the Tile Matrix with the projection 'EPSG:4326'
                const tileMatrixSetLink = layer.TileMatrixSetLink.find(
                    (link: any) => link.TileMatrixSet[0] === 'EPSG:4326'
                );

                const limits = tileMatrixSetLink.TileMatrixSetLimits[0].TileMatrixLimits.map(
                    (limit: any) => ({
                        TileMatrix: limit.TileMatrix[0],
                        MinTileRow: parseInt(limit.MinTileRow[0], 10),
                        MaxTileRow: parseInt(limit.MaxTileRow[0], 10),
                        MinTileCol: parseInt(limit.MinTileCol[0], 10),
                        MaxTileCol: parseInt(limit.MaxTileCol[0], 10)
                    })
                );

                setTileMatrixLimits(limits);

                // Setting the URL format for fetching tiles.
                setResourceUrl(layer.ResourceURL.find((u: any) => u['$format'] === 'image/png'));
            } catch (error) {
                console.error('Error fetching or parsing XML:', error);
            }
        };

        fetchAndParseXML().catch((error) => console.error('Error in fetchData:', error));
    }, []);

    // Update layer opacity and anomalies layer source after map load
    useEffect(() => {
        if (mapRef.current && mapRef.current.isStyleLoaded()) {
            mapRef.current.setPaintProperty('osm-layer', 'raster-opacity', osmOpacity);
            mapRef.current.setPaintProperty('satellite-layer', 'raster-opacity', satelliteOpacity);
            mapRef.current.setPaintProperty('anomalies-layer', 'raster-opacity', anomaliesOpacity);

            // Update the anomalies layer source to reflect the new date
            const newDate = formatDateWithOffset(new Date(2018, 0, 5), daysOffset, false);
            const source = mapRef.current.getSource('anomalies-source');
            if (source && 'tiles' in source) {
                // (source as maplibreGl.RasterTileSource).tiles = [`http://localhost:8080/${newDate}/{z}/{x}/{y}.png`];
                (source as maplibreGl.RasterTileSource).tiles = [`http://localhost:8080/geoserver/gwc/service/wmts?layer=vegetaion-anomalies:va-test2&tilematrixset=EPSG:4326&Service=WMTS&Request=GetTile&Version=1.1.1&Format=image/png&TileMatrix=EPSG:4326:{z}&TileCol={y}&TileRow={x}`];
                mapRef.current.style.sourceCaches['anomalies-source'].clearTiles();
                mapRef.current.style.sourceCaches['anomalies-source'].update(mapRef.current.transform);
                mapRef.current.triggerRepaint();
            }
        }
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity, daysOffset]);

    return (
        <div>
            <div ref={mapContainerRef} id="map"/>

            <div className="toolbox">
                <h3>Layer Controls</h3>
                <div className="slider-container">
                    <label>OSM Layer Opacity: {osmOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={osmOpacity}
                        onChange={(e) => setOsmOpacity(parseFloat(e.target.value))}
                    />
                </div>
                <div className="slider-container">
                    <label>Satellite Layer Opacity: {satelliteOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={satelliteOpacity}
                        onChange={(e) => setSatelliteOpacity(parseFloat(e.target.value))}
                    />
                </div>
                <div className="slider-container">
                    <label>Anomalies Layer Opacity: {anomaliesOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={anomaliesOpacity}
                        onChange={(e) => setAnomaliesOpacity(parseFloat(e.target.value))}
                    />
                </div>
                <div className="slider-container">
                    <label>Date: {formatDateWithOffset(new Date(2018, 0, 5), daysOffset, true)}</label>
                    <input
                        type="range"
                        min="0"
                        max="360"
                        step="5"
                        value={daysOffset}
                        onChange={(e) => setDaysOffset(parseInt(e.target.value))}
                    />
                </div>
            </div>
        </div>
    );
};

export default MapWithRaster;
