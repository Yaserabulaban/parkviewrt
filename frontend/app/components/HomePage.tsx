import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import logoImage from '@/assets/mmu-logo.png';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-8">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-12 text-center space-y-8">
        <img 
          src={logoImage} 
          alt="MMU Logo" 
          className="w-64 mx-auto mb-6"
        />
        
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          MMU Real Time Car Park System
        </h1>
        
        <p className="text-xl text-gray-700 mb-8">
          Please Select The Parking You Would Like To View
        </p>
        
        <div className="flex flex-col md:flex-row gap-6 justify-center items-center">
          <Button 
            onClick={() => navigate('/fci-parking')}
            className="w-64 h-16 text-lg"
            size="lg"
          >
            View FCI Parking
          </Button>
          
          <Button 
            onClick={() => navigate('/faie-parking')}
            className="w-64 h-16 text-lg"
            size="lg"
          >
            View FAIE Parking
          </Button>
        </div>
      </div>
    </div>
  );
}