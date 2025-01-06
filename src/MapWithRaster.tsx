import React, {useCallback, useEffect, useRef, useState} from 'react';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css'; // For styling the toolbox overlay

const TILE_SIZE = 256;
const MIN_ZOOM = 0;
const MAX_ZOOM = 9;
const CONFIG_FILE_NAME = 'config.json';

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
    const [config, setConfig] = useState<any>(null)
    const mapRef = useRef<maplibreGl.Map | null>(null);

    const formatDateWithOffset = (baseDate: Date | null, offsetDays: number, addHyphens: boolean): string => {
        if (baseDate) {
            const date: Date = new Date(baseDate);
            date.setDate(baseDate.getDate() + offsetDays);
            const separator: string = addHyphens ? '-' : '';
            return date.getFullYear().toString() +
                separator +
                (date.getMonth() + 1).toString().padStart(2, '0') +
                separator +
                date.getDate().toString().padStart(2, '0');
        } else {
            return 'null';
        }
    };

    const getTileUrl = (initialDate: Date, daysOffset: number): string => {
        const date: string = formatDateWithOffset(initialDate, daysOffset, false);
        return `${anomaliesHost}/${date}/{z}/{x}/{y}.png`;
    };

    // Parses string as date
    const parseDate = (s: string): Date => {
        return new Date(s.replace(' ', 'T'));
    }

    const getInitialDate = (): Date => {
        return parseDate(config['start_date']);
    }

    const getMinOffset = (): number => {
        return config['time_values'][0];
    }

    const getMaxOffset = (): number => {
        const timeValues = config['time_values'];
        return timeValues[timeValues.length - 1];
    }

    const getStep = (): number => {
        const timeValues = config['time_values'];
        return timeValues[1] - timeValues[0];
    }

    useEffect(() => {
        fetch(`${anomaliesHost}/${CONFIG_FILE_NAME}`)
            .then((response: Response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw response;
                }
            })
            .then((response: any) => {
                setConfig(response);
            });
    }, []);

    useEffect(() => {
        if (config && mapContainerRef.current) {
            const map = new maplibreGl.Map({
                container: mapContainerRef.current as HTMLElement,
                style: 'https://demotiles.maplibre.org/style.json',
                center: [8.75, 47.47],
                zoom: 9,
            });

            map.on('load', () => {
                // Layer 1: OpenStreetMap base raster layer
                map.addSource('osm-source', {
                    type: 'raster',
                    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                    tileSize: TILE_SIZE,
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
                    tileSize: TILE_SIZE,
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
                    minzoom: MIN_ZOOM,
                    maxzoom: MAX_ZOOM,
                    tiles: [getTileUrl(getInitialDate(), daysOffset)],
                    tileSize: TILE_SIZE,
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
    }, [config]);

    // Update layer opacity and anomalies layer source after map load
    useEffect(() => {
        if (config && mapRef && mapRef.current && mapRef.current.isStyleLoaded()) {
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
            const newTileUrl = getTileUrl(getInitialDate(), daysOffset);
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
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity, daysOffset, config]);

    return (config &&
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
                    <label>Date: {formatDateWithOffset(getInitialDate(), sliderDaysOffset, true)}</label>
                    <input
                        type="range"
                        min={getMinOffset()}
                        max={getMaxOffset()}
                        step={getStep()}
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
