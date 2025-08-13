import React, { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { MapPin, Maximize2, Minimize2, ExternalLink } from 'lucide-react';

const YandexMap = ({ addresses = [], isOpen = false, onToggle }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Загрузка скрипта Яндекс.Карт
  useEffect(() => {
    if (!isOpen) return;

    const loadYandexMapsScript = () => {
      return new Promise((resolve, reject) => {
        // Проверяем, не загружен ли уже скрипт
        if (window.ymaps) {
          resolve();
          return;
        }

        const script = document.createElement('script');
        const apiKey = process.env.REACT_APP_YANDEX_MAPS_API_KEY;
        script.src = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`;
        script.type = 'text/javascript';
        
        script.onload = () => {
          setScriptLoaded(true);
          resolve();
        };
        
        script.onerror = () => {
          reject(new Error('Не удалось загрузить Яндекс.Карты'));
        };

        document.head.appendChild(script);
      });
    };

    loadYandexMapsScript()
      .then(() => {
        if (window.ymaps) {
          window.ymaps.ready(() => {
            initMap();
          });
        }
      })
      .catch((err) => {
        setError(err.message);
        setIsLoading(false);
      });
  }, [isOpen]);

  // Инициализация карты
  const initMap = async () => {
    if (!mapRef.current || !window.ymaps) return;

    setIsLoading(true);
    setError(null);

    try {
      // Очищаем предыдущую карту
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy();
        mapInstanceRef.current = null;
      }

      // Центр карты - Москва по умолчанию
      let center = [55.751244, 37.618423];
      let zoom = 10;

      // Если есть адреса, попробуем геокодировать первый
      if (addresses.length > 0) {
        try {
          const firstAddress = addresses[0].pickup_address || addresses[0];
          const geocodeResult = await window.ymaps.geocode(firstAddress);
          const firstGeoObject = geocodeResult.geoObjects.get(0);
          
          if (firstGeoObject) {
            center = firstGeoObject.geometry.getCoordinates();
            zoom = addresses.length === 1 ? 16 : 12;
          }
        } catch (geocodeError) {
          console.warn('Ошибка геокодирования:', geocodeError);
        }
      }

      // Создаем карту
      const map = new window.ymaps.Map(mapRef.current, {
        center: center,
        zoom: zoom,
        controls: ['zoomControl', 'typeSelector', 'fullscreenControl']
      });

      mapInstanceRef.current = map;

      // Добавляем маркеры для всех адресов
      const placemarksPromises = addresses.map(async (addressData, index) => {
        try {
          const address = addressData.pickup_address || addressData;
          const geocodeResult = await window.ymaps.geocode(address);
          const geoObject = geocodeResult.geoObjects.get(0);
          
          if (geoObject) {
            const coordinates = geoObject.geometry.getCoordinates();
            
            // Создаем маркер
            const placemark = new window.ymaps.Placemark(coordinates, {
              balloonContent: `
                <div style="max-width: 300px;">
                  <h4 style="margin: 0 0 8px 0; color: #333;">
                    Заявка №${index + 1}
                  </h4>
                  <p style="margin: 0 0 4px 0; font-weight: bold;">
                    ${addressData.sender_full_name || 'Отправитель'}
                  </p>
                  <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                    ${addressData.cargo_name || 'Груз'}
                  </p>
                  <p style="margin: 0 0 8px 0; font-size: 12px;">
                    📍 ${address}
                  </p>
                  ${addressData.sender_phone ? `
                    <p style="margin: 0; font-size: 12px; color: #666;">
                      📞 ${addressData.sender_phone}
                    </p>
                  ` : ''}
                </div>
              `,
              hintContent: `${addressData.sender_full_name || 'Заявка'} №${index + 1}`
            }, {
              preset: 'islands#blueCircleDotIconWithCaption',
              iconCaption: `${index + 1}`
            });
            
            map.geoObjects.add(placemark);
            return placemark;
          }
        } catch (error) {
          console.warn(`Ошибка геокодирования адреса ${index + 1}:`, error);
        }
        return null;
      });

      // Ждем все маркеры и подстраиваем границы карты
      const placemarks = await Promise.all(placemarksPromises);
      const validPlacemarks = placemarks.filter(Boolean);
      
      if (validPlacemarks.length > 1) {
        // Подстраиваем карту под все маркеры
        const bounds = map.geoObjects.getBounds();
        if (bounds) {
          map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 50 });
        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Ошибка инициализации карты:', error);
      setError('Ошибка загрузки карты');
      setIsLoading(false);
    }
  };

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  if (!isOpen) return null;

  return (
    <div className="mt-4 border border-blue-200 rounded-lg overflow-hidden">
      {/* Заголовок карты */}
      <div className="bg-blue-50 px-4 py-3 border-b border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MapPin className="h-5 w-5 text-blue-600" />
            <h3 className="font-medium text-blue-800">
              Карта заявок ({addresses.length} адресов)
            </h3>
          </div>
          <div className="flex space-x-2">
            <Button
              onClick={() => {
                if (addresses.length > 0) {
                  const allAddresses = addresses.map(addr => addr.pickup_address || addr).join(' | ');
                  const encodedAddresses = encodeURIComponent(allAddresses);
                  const yandexMapsUrl = `https://yandex.ru/maps/?text=${encodedAddresses}&mode=search`;
                  window.open(yandexMapsUrl, '_blank');
                }
              }}
              variant="outline"
              size="sm"
              className="text-blue-600 border-blue-300"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Открыть в Яндекс.Картах
            </Button>
            <Button
              onClick={onToggle}
              variant="outline"
              size="sm"
              className="text-blue-600 border-blue-300"
            >
              <Minimize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Контейнер карты */}
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600">Загрузка карты...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 bg-red-50 flex items-center justify-center z-10">
            <div className="text-center">
              <MapPin className="h-8 w-8 text-red-400 mx-auto mb-2" />
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={() => {
                  setError(null);
                  initMap();
                }}
                variant="outline"
                size="sm"
                className="mt-2 text-red-600 border-red-300"
              >
                Попробовать снова
              </Button>
            </div>
          </div>
        )}

        <div
          ref={mapRef}
          className="w-full h-96"
          style={{ minHeight: '400px' }}
        />
      </div>

      {/* Подсказка */}
      <div className="bg-blue-50 px-4 py-2 border-t border-blue-200">
        <p className="text-xs text-blue-600">
          💡 Нажмите на маркер для просмотра деталей заявки
        </p>
      </div>
    </div>
  );
};

export default YandexMap;