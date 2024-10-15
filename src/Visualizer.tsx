import React, {useEffect, useState} from 'react';
import L from 'leaflet';
import Slider from '@mui/material/Slider';
import Box from '@mui/material/Box';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Define types for cube predictions
type CubePrediction = {
    lat: number[];
    lon: number[];
    anomaly: number[][];
};

type AnomalyLayer = {
    bounds: L.LatLngBoundsExpression;
    imageUrl: string;
};

const Visualizer: React.FC = () => {
    const [mapCenter, setMapCenter] = useState<[number, number]>([0, 0]);
    const [mapBounds, setMapBounds] = useState<L.LatLngBoundsExpression[]>([]);
    const [anomalyLayers, setAnomalyLayers] = useState<AnomalyLayer[]>([]);
    const [timeIndex, setTimeIndex] = useState<number>(0);

    useEffect(() => {
        // Fetch cube data (replace this with your actual data source)
        const cubePreds = getCubePredictions();
        const [centerLat, centerLon] = calculateMapCenter(cubePreds);
        setMapCenter([centerLat, centerLon]);

        // Define map boundaries for rectangles and overlays
        setMapBounds(createMapBounds(cubePreds));

        // Create anomaly layers for the initial time index (0)
        setAnomalyLayers(createAnomalyLayers(cubePreds, timeIndex));
    }, [timeIndex]);

    const getCubePredictions = (): CubePrediction[] => {
        // Placeholder for cube data; replace with actual data fetching
        return [
            {
                lat: [10, 20],
                lon: [30, 40],
                anomaly: [
                    [-2, 0, 1],
                    [1, -1, -2],
                ],
            },
            // Add more minicubes here...
        ];
    };

    const calculateMapCenter = (cubes: CubePrediction[]): [number, number] => {
        let minLat = Infinity,
            maxLat = -Infinity,
            minLon = Infinity,
            maxLon = -Infinity;

        cubes.forEach((cube) => {
            minLat = Math.min(minLat, ...cube.lat);
            maxLat = Math.max(maxLat, ...cube.lat);
            minLon = Math.min(minLon, ...cube.lon);
            maxLon = Math.max(maxLon, ...cube.lon);
        });

        return [(minLat + maxLat) / 2.0, (minLon + maxLon) / 2.0];
    };

    const createMapBounds = (cubes: CubePrediction[]): L.LatLngBoundsExpression[] => {
        return cubes.map((cube) => {
            const minLat = Math.min(...cube.lat);
            const maxLat = Math.max(...cube.lat);
            const minLon = Math.min(...cube.lon);
            const maxLon = Math.max(...cube.lon);
            return [
                [minLat, minLon],
                [maxLat, maxLon],
            ];
        });
    };

    const createAnomalyLayers = (cubes: CubePrediction[], timeIndex: number): AnomalyLayer[] => {
        return cubes.map((cube) => {
            const minLat = Math.min(...cube.lat);
            const maxLat = Math.max(...cube.lat);
            const minLon = Math.min(...cube.lon);
            const maxLon = Math.max(...cube.lon);

            const anomalyData = cube.anomaly[timeIndex]; // Simplified anomaly data
            const imageUrl = createImageOverlay(anomalyData);

            return {
                bounds: [
                    [minLat, minLon],
                    [maxLat, maxLon],
                ],
                imageUrl: imageUrl,
            };
        });
    };

    const createImageOverlay = (data: number[]): string => {
        // Simplified version for creating an image URL
        // Here, you need to render an image based on data (e.g., using a canvas or pre-generated URLs)
        return 'path/to/your/generated/image.png';
    };

    const handleSliderChange = (event: Event, newValue: number | number[]) => {
        setTimeIndex(newValue as number);
    };

    return (
        <Box sx={{ width: '100%', height: '100vh' }}>
            <Box sx={{ width: '100%', p: 2 }}>
                <Slider
                    min={0}
                    max={10} // Assuming you have 10 time points
                    value={timeIndex}
                    onChange={handleSliderChange}
                    aria-labelledby="time-slider"
                    valueLabelDisplay="auto"
                />
            </Box>
            {/*<MapContainer*/}
            {/*    // center={mapCenter}*/}
            {/*    bounds={mapBounds}*/}
            {/*    // zoom={8}*/}
            {/*    scrollWheelZoom={true}*/}
            {/*    style={{ height: '85vh', width: '100%' }}*/}
            {/*>*/}
            {/*    <TileLayer*/}
            {/*        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"*/}
            {/*        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'*/}
            {/*    />*/}
            {/*    {mapBounds.map((bounds, index) => (*/}
            {/*        <Rectangle*/}
            {/*            key={`rectangle-${index}`}*/}
            {/*            bounds={bounds}*/}
            {/*            color="black"*/}
            {/*            weight={1}*/}
            {/*            fillOpacity={0}*/}
            {/*        />*/}
            {/*    ))}*/}
            {/*    {anomalyLayers.map((layer, index) => (*/}
            {/*        <ImageOverlay*/}
            {/*            key={`image-overlay-${index}`}*/}
            {/*            url={layer.imageUrl}*/}
            {/*            bounds={layer.bounds}*/}
            {/*            opacity={0.5}*/}
            {/*        />*/}
            {/*    ))}*/}
            {/*</MapContainer>*/}
        </Box>
    );
};

export default Visualizer;
