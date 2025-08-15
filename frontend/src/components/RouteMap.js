import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Clock, Calculator, AlertCircle } from 'lucide-react';

const RouteMap = ({ fromAddress, toAddress, warehouseName, onRouteCalculated }) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [route, setRoute] = useState(null);
  const [distance, setDistance] = useState('');
  const [duration, setDuration] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapReady, setMapReady] = useState(false);

  // Инициализация карты
  useEffect(() => {
    if (!mapRef.current || map || mapReady) return;

    const initMap = async () => {
      try {
        console.log('🗺️ Начинаем инициализацию карты...');
        
        // Проверяем наличие API ключа
        const apiKey = process.env.REACT_APP_YANDEX_MAPS_API_KEY;
        if (!apiKey) {
          throw new Error('API ключ Yandex Maps не найден');
        }

        // Загружаем Yandex Maps API если не загружен
        if (!window.ymaps) {
          console.log('📡 Загружаем Yandex Maps API...');
          await loadYandexMapsScript(apiKey);
        }

        // Ждем готовности API
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Таймаут загрузки Yandex Maps API'));
          }, 10000); // 10 секунд таймаут

          window.ymaps.ready(() => {
            clearTimeout(timeout);
            resolve();
          });
        });

        // Создаем карту
        const ymaps = window.ymaps;
        const newMap = new ymaps.Map(mapRef.current, {
          center: [38.5736, 68.7870], // Центр Душанбе
          zoom: 10,
          controls: ['zoomControl', 'fullscreenControl']
        });

        setMap(newMap);
        setMapReady(true);
        console.log('✅ Карта успешно инициализирована');

      } catch (error) {
        console.error('❌ Ошибка инициализации карты:', error);
        setError(`Ошибка загрузки карты: ${error.message}`);
      }
    };

    initMap();
  }, [map, mapReady]);

  // Функция загрузки скрипта Yandex Maps
  const loadYandexMapsScript = (apiKey) => {
    return new Promise((resolve, reject) => {
      // Проверяем, не загружен ли уже скрипт
      if (document.querySelector('script[src*="api-maps.yandex.ru"]')) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`;
      script.async = true;
      
      script.onload = () => {
        console.log('✅ Yandex Maps скрипт загружен');
        resolve();
      };
      
      script.onerror = () => {
        reject(new Error('Не удалось загрузить Yandex Maps API'));
      };
      
      document.head.appendChild(script);
    });
  };

  // Построение маршрута
  useEffect(() => {
    if (!map || !fromAddress || !toAddress || !mapReady) {
      console.log('⏳ Ожидание готовности карты или адресов:', { 
        map: !!map, 
        fromAddress: !!fromAddress, 
        toAddress: !!toAddress, 
        mapReady 
      });
      return;
    }

    const buildRoute = async () => {
      setLoading(true);
      setError('');
      setDistance('');
      setDuration('');

      try {
        const ymaps = window.ymaps;
        if (!ymaps) {
          throw new Error('Yandex Maps API не доступен');
        }

        // Очищаем предыдущий маршрут и маркеры
        map.geoObjects.removeAll();

        console.log(`🗺️ Строим маршрут от "${fromAddress}" до "${toAddress}"`);

        // Создаем мультимаршрут с улучшенными настройками
        const multiRoute = new ymaps.multiRouter.MultiRoute({
          referencePoints: [fromAddress, toAddress],
          params: {
            routingMode: 'auto',
            avoidTrafficJams: false
          }
        }, {
          boundsAutoApply: true,
          routeActiveStrokeWidth: 4,
          routeActiveStrokeColor: '#3B82F6',
          routeInactiveStrokeWidth: 3,
          routeInactiveStrokeColor: '#94A3B8',
          wayPointDraggable: false
        });

        // Добавляем маршрут на карту
        map.geoObjects.add(multiRoute);
        setRoute(multiRoute);

        // Обработчик успешного построения маршрута
        multiRoute.model.events.add('requestsuccess', () => {
          try {
            console.log('✅ Маршрут успешно построен');
            const activeRoute = multiRoute.getActiveRoute();
            
            if (activeRoute) {
              // Получаем данные маршрута
              const distanceValue = activeRoute.properties.get('distance');
              const durationObj = activeRoute.properties.get('duration');

              console.log('📊 Данные маршрута:', { 
                distance: distanceValue, 
                duration: durationObj 
              });

              // Форматируем расстояние
              let distanceText = 'Неизвестно';
              if (typeof distanceValue === 'number' && !isNaN(distanceValue) && distanceValue > 0) {
                distanceText = distanceValue >= 1000 
                  ? `${(distanceValue / 1000).toFixed(1)} км`
                  : `${Math.round(distanceValue)} м`;
              }

              // Форматируем время
              let durationText = 'Неизвестно';
              let durationValue = 0;
              
              if (durationObj) {
                if (typeof durationObj.value === 'number') {
                  durationValue = durationObj.value;
                  const totalMinutes = Math.round(durationValue / 60);
                  const hours = Math.floor(totalMinutes / 60);
                  const minutes = totalMinutes % 60;
                  durationText = hours > 0 
                    ? `${hours} ч ${minutes} мин`
                    : `${minutes} мин`;
                } else if (typeof durationObj.text === 'string') {
                  durationText = durationObj.text;
                }
              }

              setDistance(distanceText);
              setDuration(durationText);

              // Передаем данные родителю
              if (onRouteCalculated) {
                onRouteCalculated({
                  distance: distanceText,
                  duration: durationText,
                  distanceValue: distanceValue || 0,
                  durationValue: durationValue
                });
              }

              console.log(`✅ Результат: ${distanceText}, время: ${durationText}`);

              // Добавляем кастомные маркеры
              try {
                const routeCoords = activeRoute.geometry.getCoordinates();
                if (routeCoords && routeCoords.length > 0) {
                  const startCoord = routeCoords[0];
                  const endCoord = routeCoords[routeCoords.length - 1];

                  // Маркер начальной точки
                  const startPlacemark = new ymaps.Placemark(startCoord, {
                    balloonContent: `<strong>Адрес забора:</strong><br/>${fromAddress}`,
                    iconContent: 'А'
                  }, {
                    preset: 'islands#redStretchyIcon'
                  });

                  // Маркер конечной точки  
                  const endPlacemark = new ymaps.Placemark(endCoord, {
                    balloonContent: `<strong>Склад:</strong><br/>${toAddress}`,
                    iconContent: 'Б'
                  }, {
                    preset: 'islands#greenStretchyIcon'
                  });

                  map.geoObjects.add(startPlacemark);
                  map.geoObjects.add(endPlacemark);
                  
                  console.log('✅ Маркеры добавлены');
                }
              } catch (markerError) {
                console.error('⚠️ Ошибка добавления маркеров:', markerError);
              }
            }
          } catch (routeError) {
            console.error('❌ Ошибка обработки маршрута:', routeError);
            setError('Ошибка обработки данных маршрута');
          }
        });

        // Обработчик ошибок построения маршрута
        multiRoute.model.events.add('requestfail', (e) => {
          console.error('❌ Ошибка построения маршрута:', e);
          setError('Не удалось построить маршрут. Проверьте правильность адресов.');
        });

      } catch (error) {
        console.error('❌ Ошибка при построении маршрута:', error);
        setError(`Ошибка: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    // Debounce для избежания частых запросов
    const debounceTimer = setTimeout(buildRoute, 1500);
    return () => clearTimeout(debounceTimer);
  }, [map, fromAddress, toAddress, mapReady]);

  // Показываем состояние загрузки карты
  if (!mapReady && !error) {
    return (
      <div className="space-y-3">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent mr-3"></div>
            <span className="text-blue-700">Загрузка карты...</span>
          </div>
        </div>
        <div className="border border-gray-300 rounded-lg bg-gray-100 h-64 flex items-center justify-center">
          <span className="text-gray-500">Инициализация карты</span>
        </div>
      </div>
    );
  }

  // Показываем ошибку загрузки карты
  if (error && !mapReady) {
    return (
      <div className="space-y-3">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700 font-medium">Ошибка загрузки карты</span>
          </div>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Перезагрузить страницу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Информация о маршруте */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center mb-2">
          <Navigation className="h-4 w-4 text-blue-600 mr-2" />
          <span className="font-medium text-blue-900">Маршрут доставки</span>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex items-start">
            <div className="bg-red-100 text-red-700 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-2 mt-0.5 flex-shrink-0">
              А
            </div>
            <div>
              <span className="font-medium text-red-800">Адрес забора:</span>
              <p className="text-gray-700">{fromAddress}</p>
            </div>
          </div>
          
          <div className="flex items-start">
            <div className="bg-green-100 text-green-700 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-2 mt-0.5 flex-shrink-0">
              Б
            </div>
            <div>
              <span className="font-medium text-green-800">{warehouseName}:</span>
              <p className="text-gray-700">{toAddress}</p>
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center mt-3 text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent mr-2"></div>
            <span className="text-sm">Построение маршрута...</span>
          </div>
        )}

        {error && mapReady && (
          <div className="mt-3 text-red-600 text-sm">
            <AlertCircle className="h-4 w-4 inline mr-1" />
            {error}
          </div>
        )}

        {distance && duration && !loading && !error && (
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-blue-200">
            <div className="flex items-center text-blue-700">
              <Calculator className="h-4 w-4 mr-1" />
              <span className="font-medium">{distance}</span>
            </div>
            <div className="flex items-center text-blue-700">
              <Clock className="h-4 w-4 mr-1" />
              <span className="font-medium">{duration}</span>
            </div>
          </div>
        )}
      </div>

      {/* Карта */}
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <div
          ref={mapRef}
          style={{ width: '100%', height: '300px' }}
          className="bg-gray-100"
        />
      </div>
    </div>
  );
};

export default RouteMap;