import React, { useEffect, useRef, useState } from 'react';
import { Navigation, AlertCircle } from 'lucide-react';

const SimpleRouteMap = ({ fromAddress, toAddress, warehouseName }) => {
  const mapRef = useRef(null);
  const [status, setStatus] = useState('Инициализация...');
  const [error, setError] = useState('');

  useEffect(() => {
    const initSimpleMap = async () => {
      try {
        setStatus('Проверяем API ключ...');
        
        const apiKey = process.env.REACT_APP_YANDEX_MAPS_API_KEY;
        console.log('🔑 API ключ Yandex Maps:', apiKey ? `${apiKey.substring(0, 8)}...` : 'НЕ НАЙДЕН');
        
        if (!apiKey) {
          throw new Error('API ключ Yandex Maps не найден в переменных окружения');
        }

        setStatus('Загружаем скрипт...');
        
        // Проверяем доступность Yandex Maps
        const testUrl = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`;
        console.log('🌐 URL скрипта:', testUrl);

        // Простая загрузка скрипта
        const script = document.createElement('script');
        script.src = testUrl;
        script.async = true;
        
        const loadPromise = new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = () => reject(new Error('Скрипт не загружается'));
          setTimeout(() => reject(new Error('Таймаут загрузки скрипта (20 сек)')), 20000);
        });
        
        document.head.appendChild(script);
        await loadPromise;
        
        setStatus('Скрипт загружен, ждем API...');
        console.log('✅ Скрипт загружен, window.ymaps:', !!window.ymaps);

        // Ждем готовности API
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('API не готов в течение 10 секунд'));
          }, 10000);
          
          if (window.ymaps) {
            window.ymaps.ready(() => {
              clearTimeout(timeout);
              console.log('✅ Yandex Maps API готов');
              resolve();
            });
          } else {
            clearTimeout(timeout);
            reject(new Error('window.ymaps недоступен после загрузки скрипта'));
          }
        });

        setStatus('Создаем карту...');
        
        // Создаем карту
        const ymaps = window.ymaps;
        const map = new ymaps.Map(mapRef.current, {
          center: [55.7558, 37.6173], // Москва
          zoom: 10,
          controls: []
        });

        setStatus('✅ Карта создана успешно!');
        console.log('✅ Простая карта создана');

        // Если есть адреса, добавляем маркеры
        if (fromAddress && toAddress) {
          setStatus('Добавляем маркеры...');
          
          // Геокодируем адреса
          const geocoder = ymaps.geocode(fromAddress);
          geocoder.then((res) => {
            const firstGeoObject = res.geoObjects.get(0);
            const coords = firstGeoObject.geometry.getCoordinates();
            
            const placemark = new ymaps.Placemark(coords, {
              balloonContent: `Адрес забора: ${fromAddress}`
            }, {
              preset: 'islands#redIcon'
            });
            
            map.geoObjects.add(placemark);
            setStatus('✅ Карта готова с маркерами!');
          }).catch((error) => {
            console.error('Ошибка геокодирования:', error);
            setStatus('⚠️ Карта создана, но без маркеров');
          });
        }

      } catch (error) {
        console.error('❌ Ошибка простой карты:', error);
        setError(`Ошибка: ${error.message}`);
        setStatus(`❌ ${error.message}`);
      }
    };

    if (mapRef.current) {
      initSimpleMap();
    }
  }, [fromAddress, toAddress]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center mb-2">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700 font-medium">Простая карта: Ошибка</span>
        </div>
        <p className="text-red-600 text-sm">{error}</p>
        <div className="text-xs text-gray-600 mt-2">
          Статус: {status}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <div className="flex items-center mb-2">
          <Navigation className="h-4 w-4 text-green-600 mr-2" />
          <span className="font-medium text-green-900">Простая тестовая карта</span>
        </div>
        <div className="text-sm text-green-700">
          Статус: {status}
        </div>
        {fromAddress && toAddress && (
          <div className="text-xs text-gray-600 mt-2">
            От: {fromAddress} → До: {toAddress}
          </div>
        )}
      </div>
      
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <div
          ref={mapRef}
          style={{ width: '100%', height: '250px' }}
          className="bg-gray-100"
        />
      </div>
    </div>
  );
};

export default SimpleRouteMap;