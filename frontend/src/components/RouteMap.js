import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Clock, Calculator } from 'lucide-react';

const RouteMap = ({ fromAddress, toAddress, warehouseName, onRouteCalculated }) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [route, setRoute] = useState(null);
  const [distance, setDistance] = useState('');
  const [duration, setDuration] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Инициализация карты
  useEffect(() => {
    if (!mapRef.current || map) return;

    const initMap = async () => {
      try {
        // Ждем загрузки Yandex Maps API
        await new Promise((resolve) => {
          if (window.ymaps && window.ymaps.ready) {
            window.ymaps.ready(resolve);
          } else {
            // Если API еще не загружен, загружаем его
            const script = document.createElement('script');
            script.src = `https://api-maps.yandex.ru/2.1/?apikey=${process.env.REACT_APP_YANDEX_MAPS_API_KEY}&lang=ru_RU`;
            script.onload = () => {
              window.ymaps.ready(resolve);
            };
            document.head.appendChild(script);
          }
        });

        // Создаем карту
        const ymaps = window.ymaps;
        const newMap = new ymaps.Map(mapRef.current, {
          center: [38.5736, 68.7870], // Центр Душанбе
          zoom: 10,
          controls: ['zoomControl', 'fullscreenControl']
        });

        setMap(newMap);
        console.log('✅ Карта инициализирована');
      } catch (error) {
        console.error('❌ Ошибка инициализации карты:', error);
        setError('Ошибка загрузки карты');
      }
    };

    initMap();
  }, []);

  // Построение маршрута
  useEffect(() => {
    if (!map || !fromAddress || !toAddress) return;

    const buildRoute = async () => {
      setLoading(true);
      setError('');
      setDistance('');
      setDuration('');

      try {
        const ymaps = window.ymaps;

        // Очищаем предыдущий маршрут
        if (route) {
          map.geoObjects.remove(route);
        }

        console.log(`🗺️ Строим маршрут от "${fromAddress}" до "${toAddress}"`);

        // Создаем мультимаршрут с улучшенными настройками
        const multiRoute = new ymaps.multiRouter.MultiRoute({
          referencePoints: [fromAddress, toAddress],
          params: {
            routingMode: 'auto', // Автомобильный маршрут
            avoidTrafficJams: false
          }
        }, {
          // Настройки внешнего вида маршрута
          boundsAutoApply: true,
          routeActiveStrokeWidth: 4,
          routeActiveStrokeColor: '#3B82F6', // Синий цвет маршрута
          routeInactiveStrokeWidth: 3,
          routeInactiveStrokeColor: '#94A3B8', // Серый цвет неактивного маршрута
          wayPointDraggable: false,
          
          // Настройки маркеров точек
          wayPointIconLayout: 'default#imageWithContent',
          wayPointIconImageHref: '', // Используем стандартные маркеры
          wayPointIconImageSize: [30, 42],
          wayPointIconImageOffset: [-15, -42],
          
          // Настройки подписей маркеров
          wayPointIconContentLayout: ymaps.templateLayoutFactory.createClass(
            '<div style="color: #fff; font-weight: bold; text-align: center; margin-top: 5px;">{{ properties.iconContent }}</div>'
          )
        });

        // Добавляем маршрут на карту
        map.geoObjects.add(multiRoute);
        setRoute(multiRoute);

        // Обработчик готовности маршрута
        multiRoute.model.events.add('requestsuccess', () => {
          console.log('✅ Маршрут успешно построен');
          const activeRoute = multiRoute.getActiveRoute();
          if (activeRoute) {
            // Получаем свойства маршрута
            const distanceValue = activeRoute.properties.get('distance');
            const durationObj = activeRoute.properties.get('duration');

            console.log('📏 Данные маршрута:', { 
              distance: distanceValue, 
              duration: durationObj 
            });

            // ИСПРАВЛЕНИЕ: Правильное форматирование расстояния
            let distanceText = 'Неизвестно';
            if (typeof distanceValue === 'number' && !isNaN(distanceValue)) {
              distanceText = distanceValue >= 1000 
                ? `${(distanceValue / 1000).toFixed(1)} км`
                : `${Math.round(distanceValue)} м`;
            }

            // ИСПРАВЛЕНИЕ: Правильное форматирование времени
            let durationText = 'Неизвестно';
            if (durationObj && typeof durationObj.value === 'number') {
              const totalMinutes = Math.round(durationObj.value / 60);
              const hours = Math.floor(totalMinutes / 60);
              const minutes = totalMinutes % 60;
              durationText = hours > 0 
                ? `${hours} ч ${minutes} мин`
                : `${minutes} мин`;
            } else if (durationObj && typeof durationObj.text === 'string') {
              durationText = durationObj.text;
            }

            setDistance(distanceText);
            setDuration(durationText);

            // Передаем данные родительскому компоненту
            if (onRouteCalculated) {
              onRouteCalculated({
                distance: distanceText,
                duration: durationText,
                distanceValue: distanceValue || 0,
                durationValue: durationObj?.value || 0
              });
            }

            console.log(`✅ Маршрут: ${distanceText}, время: ${durationText}`);

            // Добавляем кастомные маркеры для лучшей видимости
            const startPlacemark = new ymaps.Placemark(activeRoute.geometry.get(0), {
              balloonContent: `<strong>Точка А:</strong><br/>${fromAddress}`,
              iconContent: 'А'
            }, {
              preset: 'islands#redStretchyIcon',
              iconColor: '#ff0000'
            });

            const endPoint = activeRoute.geometry.get(activeRoute.geometry.getLength() - 1);
            const endPlacemark = new ymaps.Placemark(endPoint, {
              balloonContent: `<strong>Точка Б:</strong><br/>${toAddress}`,
              iconContent: 'Б'
            }, {
              preset: 'islands#greenStretchyIcon', 
              iconColor: '#00ff00'
            });

            map.geoObjects.add(startPlacemark);
            map.geoObjects.add(endPlacemark);
          }
        });

        // Обработчик ошибок
        multiRoute.model.events.add('requestfail', (e) => {
          console.error('❌ Ошибка построения маршрута:', e);
          setError('Не удалось построить маршрут. Проверьте правильность адресов.');
        });

      } catch (error) {
        console.error('❌ Ошибка построения маршрута:', error);
        setError('Ошибка построения маршрута');
      } finally {
        setLoading(false);
      }
    };

    // Задержка для избежания частых запросов
    const debounceTimer = setTimeout(buildRoute, 1000);
    return () => clearTimeout(debounceTimer);
  }, [map, fromAddress, toAddress, route]);

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
            <div className="bg-red-100 text-red-700 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-2 mt-0.5">
              А
            </div>
            <div>
              <span className="font-medium text-red-800">Адрес забора:</span>
              <p className="text-gray-700">{fromAddress}</p>
            </div>
          </div>
          
          <div className="flex items-start">
            <div className="bg-green-100 text-green-700 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-2 mt-0.5">
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

        {error && (
          <div className="mt-3 text-red-600 text-sm">
            ⚠️ {error}
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