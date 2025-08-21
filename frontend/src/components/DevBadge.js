import React from 'react';

/**
 * Компонент для отображения номеров разработчика
 * Показывает номера страниц, модалей, форм и карточек для упрощения разработки
 */
const DevBadge = ({ id, type = 'page', label, className = '' }) => {
  // Показывать только в режиме разработки или если установлена переменная среды
  const showDevBadges = process.env.NODE_ENV === 'development' || 
                       localStorage.getItem('showDevBadges') === 'true' ||
                       window.location.search.includes('dev=true');

  if (!showDevBadges) return null;

  // Цвет и префикс в зависимости от типа
  const getTypeConfig = (type) => {
    switch (type) {
      case 'page':
        return { prefix: 'P', color: 'bg-blue-600 text-white', title: 'Страница' };
      case 'modal':
        return { prefix: 'M', color: 'bg-purple-600 text-white', title: 'Модальное окно' };
      case 'form':
        return { prefix: 'F', color: 'bg-green-600 text-white', title: 'Форма' };
      case 'card':
        return { prefix: 'C', color: 'bg-orange-600 text-white', title: 'Карточка' };
      case 'component':
        return { prefix: 'CP', color: 'bg-red-600 text-white', title: 'Компонент' };
      case 'section':
        return { prefix: 'S', color: 'bg-indigo-600 text-white', title: 'Секция' };
      default:
        return { prefix: 'X', color: 'bg-gray-600 text-white', title: 'Элемент' };
    }
  };

  const { prefix, color, title } = getTypeConfig(type);

  return (
    <div 
      className={`fixed top-2 right-2 z-[9999] ${className}`}
      title={`${title}: ${label || id}`}
      style={{ 
        position: 'absolute',
        top: '4px',
        right: '4px',
        pointerEvents: 'none'
      }}
    >
      <div className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-mono font-bold shadow-lg ${color}`}>
        <span className="mr-1">{prefix}</span>
        <span>{id}</span>
      </div>
      {label && (
        <div className="text-xs text-gray-500 mt-1 text-right font-mono">
          {label}
        </div>
      )}
    </div>
  );
};

export default DevBadge;