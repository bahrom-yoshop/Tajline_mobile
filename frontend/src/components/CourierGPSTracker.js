import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  MapPin, 
  Navigation, 
  Clock, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Power,
  PowerOff,
  Truck,
  Home,
  Target,
  Package
} from 'lucide-react';

const CourierGPSTracker = ({ 
  courierTracking, 
  onStartTracking, 
  onStopTracking, 
  onStatusChange 
}) => {
  
  // Определить цвет и иконку статуса
  const getStatusConfig = (status) => {
    const configs = {
      'offline': {
        color: 'bg-gray-500',
        textColor: 'text-gray-700',
        icon: PowerOff,
        label: 'Не в сети',
        description: 'Отслеживание отключено'
      },
      'online': {
        color: 'bg-green-500',
        textColor: 'text-green-700',
        icon: CheckCircle,
        label: 'Свободен',
        description: 'Готов к новым заявкам'
      },
      'on_route': {
        color: 'bg-blue-500',
        textColor: 'text-blue-700',
        icon: Navigation,
        label: 'Едет к клиенту',
        description: 'В пути к месту забора/доставки'
      },
      'at_pickup': {
        color: 'bg-orange-500',
        textColor: 'text-orange-700',
        icon: Package,
        label: 'На месте забора',
        description: 'Прибыл к отправителю'
      },
      'at_delivery': {
        color: 'bg-purple-500',
        textColor: 'text-purple-700',
        icon: Home,
        label: 'На месте доставки',
        description: 'Прибыл к получателю'
      },
      'busy': {
        color: 'bg-red-500',
        textColor: 'text-red-700',
        icon: AlertTriangle,
        label: 'Занят',
        description: 'Выполняет другие задачи'
      }
    };
    return configs[status] || configs['offline'];
  };

  const statusConfig = getStatusConfig(courierTracking.status);
  const StatusIcon = statusConfig.icon;

  // Форматировать время последнего обновления
  const formatLastUpdate = (lastUpdate) => {
    if (!lastUpdate) return 'Никогда';
    
    const now = new Date();
    const diff = Math.floor((now - lastUpdate) / 1000); // секунды
    
    if (diff < 60) return 'только что';
    if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
    return lastUpdate.toLocaleDateString('ru-RU');
  };

  // Форматировать точность GPS
  const formatAccuracy = (accuracy) => {
    if (!accuracy) return 'Неизвестно';
    if (accuracy < 10) return `${Math.round(accuracy)}м (отлично)`;
    if (accuracy < 50) return `${Math.round(accuracy)}м (хорошо)`;
    if (accuracy < 100) return `${Math.round(accuracy)}м (удовлетворительно)`;
    return `${Math.round(accuracy)}м (слабо)`;
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${statusConfig.color}`}>
              <StatusIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg">GPS Отслеживание</CardTitle>
              <CardDescription>Управление местоположением курьера</CardDescription>
            </div>
          </div>
          <Badge 
            variant={courierTracking.isTracking ? "default" : "secondary"}
            className={`${courierTracking.isTracking ? statusConfig.color : 'bg-gray-400'} text-white`}
          >
            {statusConfig.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Основные кнопки управления */}
        <div className="flex gap-2">
          {!courierTracking.isTracking ? (
            <Button 
              onClick={onStartTracking}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              <Power className="mr-2 h-4 w-4" />
              Начать отслеживание
            </Button>
          ) : (
            <Button 
              onClick={onStopTracking}
              variant="outline"
              className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
            >
              <PowerOff className="mr-2 h-4 w-4" />
              Остановить отслеживание
            </Button>
          )}
        </div>

        {/* Выбор статуса (только если отслеживание включено) */}
        {courierTracking.isTracking && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Текущий статус:
            </label>
            <Select value={courierTracking.status} onValueChange={onStatusChange}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="online">
                  <div className="flex items-center">
                    <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                    Свободен
                  </div>
                </SelectItem>
                <SelectItem value="on_route">
                  <div className="flex items-center">
                    <Navigation className="mr-2 h-4 w-4 text-blue-500" />
                    Едет к клиенту
                  </div>
                </SelectItem>
                <SelectItem value="at_pickup">
                  <div className="flex items-center">
                    <Package className="mr-2 h-4 w-4 text-orange-500" />
                    На месте забора
                  </div>
                </SelectItem>
                <SelectItem value="at_delivery">
                  <div className="flex items-center">
                    <Home className="mr-2 h-4 w-4 text-purple-500" />
                    На месте доставки
                  </div>
                </SelectItem>
                <SelectItem value="busy">
                  <div className="flex items-center">
                    <AlertTriangle className="mr-2 h-4 w-4 text-red-500" />
                    Занят
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">{statusConfig.description}</p>
          </div>
        )}

        {/* Информация о местоположении */}
        {courierTracking.isTracking && (
          <div className="bg-gray-50 p-3 rounded-lg space-y-2">
            <div className="flex items-center text-sm">
              <MapPin className="mr-2 h-4 w-4 text-gray-500" />
              <span className="font-medium">Координаты:</span>
              {courierTracking.coordinates ? (
                <span className="ml-2 font-mono text-xs">
                  {courierTracking.coordinates.latitude.toFixed(6)}, {courierTracking.coordinates.longitude.toFixed(6)}
                </span>
              ) : (
                <span className="ml-2 text-gray-500">Определяются...</span>
              )}
            </div>

            <div className="flex items-center text-sm">
              <Activity className="mr-2 h-4 w-4 text-gray-500" />
              <span className="font-medium">Точность GPS:</span>
              <span className="ml-2">{formatAccuracy(courierTracking.accuracy)}</span>
            </div>

            <div className="flex items-center text-sm">
              <Clock className="mr-2 h-4 w-4 text-gray-500" />
              <span className="font-medium">Последнее обновление:</span>
              <span className="ml-2">{formatLastUpdate(courierTracking.lastUpdate)}</span>
            </div>
          </div>
        )}

        {/* Ошибки */}
        {courierTracking.error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-700">
              {courierTracking.error}
            </AlertDescription>
          </Alert>
        )}

        {/* Подсказки и информация */}
        <div className="bg-blue-50 p-3 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-2">💡 Советы по использованию:</h4>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• Включите GPS для точного определения местоположения</li>
            <li>• Обновляйте статус при изменении ситуации</li>
            <li>• Отслеживание работает в фоновом режиме</li>
            <li>• Координаты отправляются каждые 30 секунд</li>
            {!courierTracking.isTracking && (
              <li className="text-blue-600 font-medium">• Нажмите "Начать отслеживание" для активации</li>
            )}
          </ul>
        </div>

        {/* Статистика отслеживания */}
        {courierTracking.isTracking && (
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-green-50 p-2 rounded">
              <div className="text-lg font-bold text-green-600">
                {courierTracking.coordinates ? '✓' : '○'}
              </div>
              <div className="text-xs text-green-700">GPS</div>
            </div>
            <div className="bg-blue-50 p-2 rounded">
              <div className="text-lg font-bold text-blue-600">
                {courierTracking.lastUpdate ? '✓' : '○'}
              </div>
              <div className="text-xs text-blue-700">Синхронизация</div>
            </div>
            <div className="bg-purple-50 p-2 rounded">
              <div className="text-lg font-bold text-purple-600">
                {courierTracking.status !== 'offline' ? '✓' : '○'}
              </div>
              <div className="text-xs text-purple-700">Статус</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CourierGPSTracker;