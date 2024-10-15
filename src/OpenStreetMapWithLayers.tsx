import React, {useEffect, useState} from 'react';
import {ImageOverlay, MapContainer, Rectangle, TileLayer} from 'react-leaflet';
import {LatLngBoundsExpression} from 'leaflet';
import 'leaflet/dist/leaflet.css';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

interface CubeValues {
    lat: number[];
    lon: number[];
    anomaly: number[][][];
    time: string[];
}

interface Props {
    cubeValues: CubeValues[];
}

const OpenStreetMapWithLayers: React.FC<Props> = ({ cubeValues }: Props): JSX.Element => {
    const [timeIndex, setTimeIndex] = useState<number>(0);
    const [mapCenter, setMapCenter] = useState<[number, number]>([0, 0]);

    useEffect((): void => {
        if (cubeValues.length > 0) {
            const centerLat: number = (Math.min(...cubeValues.map((c: CubeValues): number => Math.min(...c.lat))) +
                    Math.max(...cubeValues.map((c: CubeValues): number => Math.max(...c.lat)))) /
                2;
            const centerLon: number = (Math.min(...cubeValues.map((c: CubeValues): number => Math.min(...c.lon))) +
                    Math.max(...cubeValues.map((c: CubeValues): number => Math.max(...c.lon)))) /
                2;
            setMapCenter([centerLat, centerLon]);
        }
    }, [cubeValues]);

    const createOverlayImage = (data: number[][]): string => {
        const canvas: HTMLCanvasElement = document.createElement('canvas');
        canvas.width = data[0].length;
        canvas.height = data.length;
        const ctx: CanvasRenderingContext2D | null = canvas.getContext('2d');
        if (!ctx) return '';

        const imgData: ImageData = ctx.createImageData(canvas.width, canvas.height);
        for (let y: number = 0; y < data.length; y++) {
            for (let x: number = 0; x < data[0].length; x++) {
                const idx: number = (y * canvas.width + x) * 4;
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
                max={cubeValues[0]?.time.length - 1 || 0}
                value={timeIndex}
                onChange={(value: number | number[]): void => setTimeIndex(value as number)}
                marks={cubeValues[0]?.time.reduce((acc: Record<number, string>, t: string, i: number) => {
                    acc[i] = t;
                    return acc;
                }, {})}
            />
            <MapContainer center={mapCenter} zoom={8} scrollWheelZoom={true} style={{ height: '800px', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {cubeValues.map((minicube: CubeValues, index: number) => {
                    const minLat: number = Math.min(...minicube.lat);
                    const maxLat: number = Math.max(...minicube.lat);
                    const minLon: number = Math.min(...minicube.lon);
                    const maxLon: number = Math.max(...minicube.lon);

                    const bounds: LatLngBoundsExpression = [
                        [minLat, minLon],
                        [maxLat, maxLon],
                    ];

                    const dataValues: number[][] = minicube.anomaly[timeIndex];
                    dataValues.forEach((row: number[]) => {
                        row.forEach((value: number, idx: number) => {
                            if (value === 1 || value === 2) {
                                row[idx] = 0;
                            }
                        });
                    });
                    const overlayUrl: string = createOverlayImage(dataValues);

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