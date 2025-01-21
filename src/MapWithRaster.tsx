import React, {useEffect, useRef, useState} from 'react';
import maplibreGl from 'maplibre-gl';
import './MapWithRaster.css'; // For styling the toolbox overlay

const TILE_SIZE = 256;
const CONFIG_FILE_NAME = 'metadata.json';
const INITIAL_DATE_CONFIG_PARAMETER = 'start_date';
const TIME_VALUES_CONFIG_PARAMETER = 'time_values';
const ZOOM_LEVELS_CONFIG_PARAMETER = 'zoom_levels';
const NEGATIVE_ANOMALY_COLOR_CONFIG_PARAMETER = 'negative_anomaly_color';
const NO_ANOMALY_COLOR_CONFIG_PARAMETER = 'no_anomaly_color';
const POSITIVE_ANOMALY_COLOR_CONFIG_PARAMETER = 'positive_anomaly_color';

const MapWithRaster = (): any => {
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

    // Format date plus an offset in days as string
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

    // Get URL for anomalies tiles
    const getAnomaliesTileUrl = (initialDate: Date, daysOffset: number): string => {
        const date: string = formatDateWithOffset(initialDate, daysOffset, false);
        return `${anomaliesHost}/${date}/{z}/{x}/{y}.png`;
    };

    // Parse string as date
    const parseDate = (s: string): Date => {
        return new Date(s.replace(' ', 'T'));
    }

    // Get the starting date from config
    const getInitialDate = (): Date => {
        return parseDate(config[INITIAL_DATE_CONFIG_PARAMETER]);
    }

    // Create rgb() function string for CSS from the array of RGBA values
    const getRgbCssFunction = (color: Array<number>): string => {
        return `rgb(${color[0]} ${color[1]} ${color[2]} / ${color[3]})`
    }

    // Add anomalies layer on the map with the specified tiles URL
    const addAnomaliesLayer = (map: maplibreGl.Map, tileUrl: string) => {
        // Remove existing anomalies layer and source
        if (map.getLayer('anomalies-layer')) {
            map.removeLayer('anomalies-layer');
        }
        if (map.getSource('anomalies-source')) {
            map.removeSource('anomalies-source');
        }

        const zoomLevels: Array<number> = config[ZOOM_LEVELS_CONFIG_PARAMETER];
        // Layer 3: Anomalies layer
        map.addSource('anomalies-source', {
            type: 'raster',
            minzoom: zoomLevels[0],
            maxzoom: zoomLevels[1],
            tiles: [tileUrl],
            tileSize: TILE_SIZE,
        });

        map.addLayer({
            id: 'anomalies-layer',
            type: 'raster',
            source: 'anomalies-source',
            paint: {
                'raster-opacity': anomaliesOpacity,
                'raster-resampling': 'nearest', // Disable anti-aliasing
            },
        });

        // Handle zoom events to dynamically adjust anti-aliasing if needed
        map.on('zoom', () => {
            const zoom = map.getZoom();
            if (zoom > zoomLevels[1]) {
                map.setPaintProperty('anomalies-layer', 'raster-resampling', 'nearest');
            } else {
                map.setPaintProperty('anomalies-layer', 'raster-resampling', 'linear');
            }
        });
    };

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

                addAnomaliesLayer(map, getAnomaliesTileUrl(getInitialDate(), daysOffset));

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
            const map: maplibreGl.Map = mapRef.current;

            map.setPaintProperty('osm-layer', 'raster-opacity', osmOpacity);
            map.setPaintProperty('satellite-layer', 'raster-opacity', satelliteOpacity);
            map.setPaintProperty('anomalies-layer', 'raster-opacity', anomaliesOpacity);

            addAnomaliesLayer(map, getAnomaliesTileUrl(getInitialDate(), daysOffset));
        }
    }, [osmOpacity, satelliteOpacity, anomaliesOpacity, daysOffset, config]);

    const timeValues: Array<number> = config && config[TIME_VALUES_CONFIG_PARAMETER]
    const negativeAnomalyColor: Array<number> = config && config[NEGATIVE_ANOMALY_COLOR_CONFIG_PARAMETER]
    const noAnomalyColor: Array<number> = config && config[NO_ANOMALY_COLOR_CONFIG_PARAMETER]
    const positiveAnomalyColor: Array<number> = config && config[POSITIVE_ANOMALY_COLOR_CONFIG_PARAMETER]

    return (config &&
        <div>
            <div ref={mapContainerRef} id="map"/>

            <div className="box legend">
                <div className="legend-item">
                    <span className="color-box" style={{backgroundColor: getRgbCssFunction(negativeAnomalyColor)}}></span>
                    <span>Negative Anomaly</span>
                </div>
                <div className="legend-item">
                    <span className="color-box" style={{backgroundColor: getRgbCssFunction(noAnomalyColor)}}></span>
                    <span>No Anomaly</span>
                </div>
                <div className="legend-item">
                    <span className="color-box" style={{backgroundColor: getRgbCssFunction(positiveAnomalyColor)}}></span>
                    <span>Positive Anomaly</span>
                </div>
            </div>

            <div className="box toolbox">
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
                    <label>Date: {formatDateWithOffset(getInitialDate(), timeValues[sliderDaysOffset], true)}</label>
                    <input
                        type="range"
                        min={0}
                        max={timeValues.length - 1}
                        step={1}
                        value={sliderDaysOffset}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setSliderDaysOffset(parseFloat(e.target.value))}
                        onMouseUp={() => setDaysOffset(timeValues[sliderDaysOffset])}
                        onKeyUp={() => setDaysOffset(timeValues[sliderDaysOffset])}
                    />
                </div>
            </div>
        </div>
    );
};

export default MapWithRaster;
