import React, {useEffect, useState} from 'react';
import {ImageOverlay, MapContainer, Rectangle, TileLayer} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

interface CubePrediction {
    lat: number[];
    lon: number[];
    anomaly: number[][][];
    time: string[];
}

interface Props {
    cubePredictions: CubePrediction[];
}

const OpenStreetMapWithLayers: React.FC<Props> = ({ cubePredictions }) => {
    const [timeIndex, setTimeIndex] = useState(0);
    const [mapCenter, setMapCenter] = useState<[number, number]>([0, 0]);

    useEffect(() => {
        if (cubePredictions.length > 0) {
            const centerLat = (Math.min(...cubePredictions.map((c) => Math.min(...c.lat))) +
                    Math.max(...cubePredictions.map((c) => Math.max(...c.lat)))) /
                2;
            const centerLon = (Math.min(...cubePredictions.map((c) => Math.min(...c.lon))) +
                    Math.max(...cubePredictions.map((c) => Math.max(...c.lon)))) /
                2;
            setMapCenter([centerLat, centerLon]);
        }
    }, [cubePredictions]);

    const createOverlayImage = (data: number[][]) => {
        const canvas = document.createElement('canvas');
        canvas.width = data[0].length;
        canvas.height = data.length;
        const ctx = canvas.getContext('2d');
        if (!ctx) return '';

        const imgData = ctx.createImageData(canvas.width, canvas.height);
        for (let y = 0; y < data.length; y++) {
            for (let x = 0; x < data[0].length; x++) {
                const idx = (y * canvas.width + x) * 4;
                if (data[y][x] === -2) {
                    imgData.data[idx] = 255;
                    imgData.data[idx + 1] = 0;
                    imgData.data[idx + 2] = 0;
                    imgData.data[idx + 3] = 255;
                } else if (data[y][x] === -1) {
                    imgData.data[idx] = 255;
                    imgData.data[idx + 1] = 128;
                    imgData.data[idx + 2] = 0;
                    imgData.data[idx + 3] = 255;
                } else {
                    imgData.data[idx + 3] = 0;
                }
            }
        }
        ctx.putImageData(imgData, 0, 0);
        return canvas.toDataURL();
    };

    return (
        <div>
            <Slider
                min={0}
                max={cubePredictions[0]?.time.length - 1 || 0}
                value={timeIndex}
                onChange={(value) => setTimeIndex(value as number)}
                marks={cubePredictions[0]?.time.reduce((acc, t, i) => {
                    acc[i] = t;
                    return acc;
                }, {} as Record<number, string>)}
            />
            <MapContainer center={mapCenter} zoom={8} scrollWheelZoom style={{ height: '800px', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {cubePredictions.map((minicube, index) => {
                    const minLat = Math.min(...minicube.lat);
                    const maxLat = Math.max(...minicube.lat);
                    const minLon = Math.min(...minicube.lon);
                    const maxLon = Math.max(...minicube.lon);

                    const bounds: L.LatLngBoundsExpression = [
                        [minLat, minLon],
                        [maxLat, maxLon],
                    ];

                    const dataValues = minicube.anomaly[timeIndex];
                    dataValues.forEach((row) => {
                        row.forEach((value, idx) => {
                            if (value === 1 || value === 2) {
                                row[idx] = 0;
                            }
                        });
                    });
                    const overlayUrl = createOverlayImage(dataValues);

                    return (
                        <React.Fragment key={index}>
                            <Rectangle bounds={bounds} pathOptions={{ color: 'black', weight: 1, fillOpacity: 0 }} />
                            {overlayUrl && (
                                <ImageOverlay bounds={bounds} url={overlayUrl} opacity={0.5} />
                            )}
                        </React.Fragment>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default OpenStreetMapWithLayers;