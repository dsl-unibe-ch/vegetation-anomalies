import React, {useCallback, useEffect, useRef, useState} from 'react';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css'; // For styling the toolbox overlay

const INITIAL_DATE = new Date(2023, 0, 4);

const MapWithRaster = () => {
    const anomaliesHost: string | undefined = process.env.REACT_APP_ANOMALIES_MAPS_API_URL;
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const [osmOpacity, setOsmOpacity] = useState(1.0);
    const [sliderOsmOpacity, setSliderOsmOpacity] = useState(1.0);
    const [satelliteOpacity, setSatelliteOpacity] = useState(0.0);
    const [sliderSatelliteOpacity, setSliderSatelliteOpacity] = useState(0.0);
    const [anomaliesOpacity, setAnomaliesOpacity] = useState(0.8);
    const [sliderAnomaliesOpacity, setSliderAnomaliesOpacity] = useState(0.8);
    const [daysOffset, setDaysOffset] = useState(0);
    const [sliderDaysOffset, setSliderDaysOffset] = useState(0);
    const mapRef = useRef<maplibreGl.Map | null>(null);

    const formatDateWithOffset = (baseDate: Date, offsetDays: number, addHyphens: boolean): string => {
        const date: Date = new Date(baseDate);
        date.setDate(baseDate.getDate() + offsetDays);
        const separator: string = addHyphens ? '-' : '';
        return date.getFullYear().toString() +
            separator +
            (date.getMonth() + 1).toString().padStart(2, '0') +
            separator +
            date.getDate().toString().padStart(2, '0');
    };

    const getTileUrl = (daysOffset: number): string => {
        const date: string = formatDateWithOffset(INITIAL_DATE, daysOffset, false);
        return `${anomaliesHost}/${date}/{z}/{x}/{y}.png`;
    };

    useEffect(() => {
        if (mapContainerRef.current) {
            const map = new maplibreGl.Map({
                container: mapContainerRef.current as HTMLElement,
                style: 'https://demotiles.maplibre.org/style.json',
                center: [8.75, 47.47],
                zoom: 13,
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

                // Layer 2: Satellite layer
                map.addSource('satellite-source', {
                    type: 'raster',
                    tiles: [
                        'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    ],
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
                    minzoom: 0,
                    maxzoom: 13,
                    tiles: [getTileUrl(daysOffset)],
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

            return (): void => map.remove();
        }
    }, []);

    // Update layer opacity and anomalies layer source after map load
    useEffect(() => {
        if (mapRef && mapRef.current && mapRef.current.isStyleLoaded()) {
            // Update layer opacities
            mapRef.current.setPaintProperty('osm-layer', 'raster-opacity', osmOpacity);
            mapRef.current.setPaintProperty('satellite-layer', 'raster-opacity', satelliteOpacity);
            mapRef.current.setPaintProperty('anomalies-layer', 'raster-opacity', anomaliesOpacity);

            // Remove existing anomalies layer and source
            if (mapRef.current.getLayer('anomalies-layer')) {
                mapRef.current.removeLayer('anomalies-layer');
            }
            if (mapRef.current.getSource('anomalies-source')) {
                mapRef.current.removeSource('anomalies-source');
            }

            // Add the anomalies source with the updated tile URL
            const newTileUrl = getTileUrl(daysOffset);
            mapRef.current.addSource('anomalies-source', {
                type: 'raster',
                tiles: [newTileUrl],
                tileSize: 256,
            });

            // Add the anomalies layer back to the map
            mapRef.current.addLayer({
                id: 'anomalies-layer',
                type: 'raster',
                source: 'anomalies-source',
                paint: {
                    'raster-opacity': anomaliesOpacity,
                },
            });
        }
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity, daysOffset]);

    return (
        <div>
            <div ref={mapContainerRef} id="map" />

            <div className="toolbox">
                <h3>Layer Controls</h3>
                <div className="slider-container">
                    <label>OSM Layer Opacity: {sliderOsmOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={sliderOsmOpacity}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setSliderOsmOpacity(parseFloat(e.target.value))}
                        onMouseUp={() => setOsmOpacity(sliderOsmOpacity)}
                        onKeyUp={() => setOsmOpacity(sliderOsmOpacity)}
                    />
                </div>
                <div className="slider-container">
                    <label>Satellite Layer Opacity: {sliderSatelliteOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={sliderSatelliteOpacity}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setSliderSatelliteOpacity(parseFloat(e.target.value))}
                        onMouseUp={() => setSatelliteOpacity(sliderSatelliteOpacity)}
                        onKeyUp={() => setSatelliteOpacity(sliderSatelliteOpacity)}
                    />
                </div>
                <div className="slider-container">
                    <label>Anomalies Layer Opacity: {sliderAnomaliesOpacity}</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={sliderAnomaliesOpacity}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setSliderAnomaliesOpacity(parseFloat(e.target.value))}
                        onMouseUp={() => setAnomaliesOpacity(sliderAnomaliesOpacity)}
                        onKeyUp={() => setAnomaliesOpacity(sliderAnomaliesOpacity)}
                    />
                </div>
                <div className="slider-container">
                    <label>Date: {formatDateWithOffset(INITIAL_DATE, sliderDaysOffset, true)}</label>
                    <input
                        type="range"
                        min="0"
                        max="360"
                        step="5"
                        value={sliderDaysOffset}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setSliderDaysOffset(parseFloat(e.target.value))}
                        onMouseUp={() => setDaysOffset(sliderDaysOffset)}
                        onKeyUp={() => setDaysOffset(sliderDaysOffset)}
                    />
                </div>
            </div>
        </div>
    );
};

export default MapWithRaster;
