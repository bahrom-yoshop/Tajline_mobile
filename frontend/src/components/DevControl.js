import React, { useState, useEffect } from 'react';
import { Settings, Eye, EyeOff } from 'lucide-react';
import { Button } from './ui/button';

/**
 * Компонент для управления отображением номеров разработчика
 */
const DevControl = () => {
  const [showBadges, setShowBadges] = useState(false);
  const [showControl, setShowControl] = useState(false);

  useEffect(() => {
    // Проверяем сохраненное состояние
    const saved = localStorage.getItem('showDevBadges') === 'true';
    setShowBadges(saved);
    
    // Показываем контроль в режиме разработки или по URL параметру
    const shouldShow = process.env.NODE_ENV === 'development' || 
                      window.location.search.includes('dev=true');
    setShowControl(shouldShow);
  }, []);

  const toggleBadges = () => {
    const newValue = !showBadges;
    setShowBadges(newValue);
    localStorage.setItem('showDevBadges', newValue.toString());
    
    // Перезагрузка страницы для применения изменений
    window.location.reload();
  };

  if (!showControl) return null;

  return (
    <div className="fixed bottom-4 left-4 z-[9999]">
      <Button
        onClick={toggleBadges}
        variant={showBadges ? "default" : "outline"}
        size="sm"
        className="shadow-lg"
        title={showBadges ? 'Скрыть номера разработчика' : 'Показать номера разработчика'}
      >
        {showBadges ? <EyeOff className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
        <Settings className="h-4 w-4 ml-1" />
        <span className="ml-1 text-xs">
          {showBadges ? 'ON' : 'OFF'}
        </span>
      </Button>
    </div>
  );
};

export default DevControl;