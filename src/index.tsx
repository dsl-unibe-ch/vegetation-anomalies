import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import reportWebVitals from './reportWebVitals';
import MapWithRaster from "./MapWithRaster";

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

const cubePredictions = [
    {
        lat: [34.5, 34.6],
        lon: [-117.9, -117.8],
        anomaly: [
            [
                [-2, -1, 0, 1],
                [-2, 0, 0, 2]
            ],
            [
                [-1, 0, 0, 1],
                [-2, -1, 2, 1]
            ]
        ],
        time: ['2023-01-01', '2023-01-02']
    },
];

root.render(
  <React.StrictMode>
    {/*<App />*/}
    {/*<Visualizer />*/}
    {/*<OpenStreetMapWithLayers cubeValues={cubePredictions}/>*/}
      <MapWithRaster/>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
