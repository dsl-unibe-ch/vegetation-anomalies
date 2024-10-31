import React, {useEffect, useRef, useState} from 'react';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css'; // For styling the toolbox overlay

const MapWithRaster = () => {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const [osmOpacity, setOsmOpacity] = useState(0.0);
    const [satelliteOpacity, setSatelliteOpacity] = useState(0.0);
    const [anomaliesOpacity, setAnomaliesOpacity] = useState(0.5);
    const [daysOffset, setDaysOffset] = useState(0);
    const mapRef = useRef<maplibreGl.Map | null>(null);

    const formatDateWithOffset = (baseDate: Date, offsetDays: number): string => {
        // Create a date object
        const date: Date = new Date()

        // Add the offset in days
        date.setDate(baseDate.getDate() + offsetDays);

        // Format the date in 'YYYYMMDD' format
        const formattedDate = date.getFullYear().toString() +
            (date.getMonth() + 1).toString().padStart(2, '0') +
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

            const date: string = formatDateWithOffset(new Date(2018, 1, 5), daysOffset);

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
                map.addSource('anomalies-source', {
                    type: 'raster',
                    tiles: [`http://localhost:8080/${date}/{z}/{x}/{y}.png`],
                    tileSize: 256,
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
    }, []);

    // Update layer opacity after map load
    useEffect(() => {
        if (mapRef.current && mapRef.current.isStyleLoaded()) {
            mapRef.current.setPaintProperty('osm-layer', 'raster-opacity', osmOpacity);
            mapRef.current.setPaintProperty('satellite-layer', 'raster-opacity', satelliteOpacity);
            mapRef.current.setPaintProperty('anomalies-layer', 'raster-opacity', anomaliesOpacity);
        }
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity]);

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
                    <label>Days since 2018-01-05: {daysOffset}</label>
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
