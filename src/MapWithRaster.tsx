import React, {useEffect, useRef, useState} from 'react';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css'; // For styling the toolbox overlay

const MapWithRaster = () => {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const [osmOpacity, setOsmOpacity] = useState(1.0);
    const [satelliteOpacity, setSatelliteOpacity] = useState(0.0);
    const [anomaliesOpacity, setAnomaliesOpacity] = useState(0.8);
    const [daysOffset, setDaysOffset] = useState(0);
    const mapRef = useRef<maplibreGl.Map | null>(null);

    const formatDateWithOffset = (baseDate: Date, offsetDays: number, addHyphens: boolean): string => {
        const date: Date = new Date(baseDate)
        date.setDate(baseDate.getDate() + offsetDays);
        const separator: string = addHyphens ? '-' : '';
        const formattedDate = date.getFullYear().toString() + separator +
            (date.getMonth() + 1).toString().padStart(2, '0') + separator +
            date.getDate().toString().padStart(2, '0');
        return formattedDate;
    }

    const getTileUrl = (): string => {
        const date: string = formatDateWithOffset(new Date(2018, 0, 5), daysOffset, false);
        return `http://localhost:8080/${date}/{z}/{x}/{y}.png`;
    };

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
                const url = getTileUrl();
                map.addSource('anomalies-source', {
                    type: 'raster',
                    tiles: [url],
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

    // Update layer opacity and anomalies layer source after map load
    useEffect(() => {
        if (mapRef.current && mapRef.current.isStyleLoaded()) {
            mapRef.current.setPaintProperty('osm-layer', 'raster-opacity', osmOpacity);
            mapRef.current.setPaintProperty('satellite-layer', 'raster-opacity', satelliteOpacity);
            mapRef.current.setPaintProperty('anomalies-layer', 'raster-opacity', anomaliesOpacity);

            // Update the anomalies layer source to reflect the new date
            const source = mapRef.current.getSource('anomalies-source');
            if (source && 'tiles' in source) {
                (source as maplibreGl.RasterTileSource).tiles = [getTileUrl()];
                mapRef.current.style.sourceCaches['anomalies-source'].clearTiles();
                mapRef.current.style.sourceCaches['anomalies-source'].update(mapRef.current.transform);
                mapRef.current.triggerRepaint();
            }
        }
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity, daysOffset]);

    const handleSliderChange = (setter: React.Dispatch<React.SetStateAction<number>>) => (e: React.ChangeEvent<HTMLInputElement>) => {
        setter(parseFloat(e.target.value));
    };

    const handleSliderMouseUp = (setter: React.Dispatch<React.SetStateAction<number>>) => (e: React.MouseEvent<HTMLInputElement>) => {
        setter(parseFloat(e.currentTarget.value));
    };

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
                        onChange={handleSliderChange(setOsmOpacity)}
                        onMouseUp={handleSliderMouseUp(setOsmOpacity)}
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
                        onChange={handleSliderChange(setSatelliteOpacity)}
                        onMouseUp={handleSliderMouseUp(setSatelliteOpacity)}
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
                        onChange={handleSliderChange(setAnomaliesOpacity)}
                        onMouseUp={handleSliderMouseUp(setAnomaliesOpacity)}
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
                        onChange={handleSliderChange(setDaysOffset)}
                        onMouseUp={handleSliderMouseUp(setDaysOffset)}
                    />
                </div>
            </div>
        </div>
    );
};

export default MapWithRaster;
