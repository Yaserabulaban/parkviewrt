import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from '../app/components/HomePage';
import FCIParkingView from '../app/components/FCIParkingView';
import FAIEParkingView from '../app/components/FAIEParkingView';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/fci-parking" element={<FCIParkingView />} />
        <Route path="/faie-parking" element={<FAIEParkingView />} />
      </Routes>
    </BrowserRouter>
  );
}