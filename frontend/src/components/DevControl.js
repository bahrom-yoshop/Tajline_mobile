import React, { useState, useEffect } from 'react';
import { Settings, Eye, EyeOff } from 'lucide-react';

/**
 * Компонент для управления отображением номеров разработчика
 */
const DevControl = () => {
  const [showBadges, setShowBadges] = useState(false);
  const [showControl, setShowControl] = useState(false);

  useEffect(() => {
    try {
      // Проверяем сохраненное состояние
      const saved = localStorage.getItem('showDevBadges') === 'true';
      setShowBadges(saved);
      
      // Показываем контроль в режиме разработки или по URL параметру
      const shouldShow = process.env.NODE_ENV === 'development' || 
                        window.location.search.includes('dev=true');
      setShowControl(shouldShow);
    } catch (error) {
      console.error('DevControl error:', error);
      setShowControl(false);
    }
  }, []);

  const toggleBadges = () => {
    try {
      const newValue = !showBadges;
      setShowBadges(newValue);
      localStorage.setItem('showDevBadges', newValue.toString());
      
      // Перезагрузка страницы для применения изменений
      window.location.reload();
    } catch (error) {
      console.error('Error toggling dev badges:', error);
    }
  };

  if (!showControl) return null;

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <button
        onClick={toggleBadges}
        className={`px-3 py-2 rounded-md shadow-lg text-sm font-medium transition-colors ${
          showBadges 
            ? 'bg-blue-600 text-white hover:bg-blue-700' 
            : 'bg-white text-gray-700 border hover:bg-gray-50'
        }`}
        title={showBadges ? 'Скрыть номера разработчика' : 'Показать номера разработчика'}
      >
        {showBadges ? <EyeOff className="inline h-4 w-4 mr-1" /> : <Eye className="inline h-4 w-4 mr-1" />}
        <Settings className="inline h-4 w-4 ml-1" />
        <span className="ml-1 text-xs">
          {showBadges ? 'ON' : 'OFF'}
        </span>
      </button>
    </div>
  );
};

export default DevControl;