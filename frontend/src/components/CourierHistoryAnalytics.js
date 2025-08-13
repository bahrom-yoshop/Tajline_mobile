import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  MapPin, 
  Clock, 
  TrendingUp,
  Activity,
  Route,
  Target,
  BarChart3,
  Calendar,
  Navigation,
  Truck,
  Timer,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';

const CourierHistoryAnalytics = ({ userRole, apiCall, selectedCourierId = null }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [etaCalculation, setEtaCalculation] = useState(null);
  
  // Фильтры и параметры
  const [dateFrom, setDateFrom] = useState(() => {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return weekAgo.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [selectedCourier, setSelectedCourier] = useState(selectedCourierId || '');
  const [couriers, setCouriers] = useState([]);
  const [destinationAddress, setDestinationAddress] = useState('');

  // Загрузить список курьеров для выбора
  const fetchCouriers = async () => {
    try {
      const endpoint = userRole === 'admin' 
        ? '/api/admin/couriers'
        : '/api/operator/couriers';
      
      const response = await apiCall(endpoint, 'GET');
      if (response && response.couriers) {
        setCouriers(response.couriers);
        if (!selectedCourier && response.couriers.length > 0) {
          setSelectedCourier(response.couriers[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching couriers:', error);
    }
  };

  // Загрузить историю перемещений курьера
  const fetchCourierHistory = async () => {
    if (!selectedCourier) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const endpoint = userRole === 'admin' 
        ? `/api/admin/couriers/${selectedCourier}/history`
        : `/api/operator/couriers/${selectedCourier}/history`;
      
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const response = await apiCall(`${endpoint}?${params.toString()}`, 'GET');
      if (response) {
        setHistoryData(response);
      }
    } catch (error) {
      console.error('Error fetching courier history:', error);
      setError(`Ошибка загрузки истории: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Загрузить аналитику по всем курьерам (только для админов)
  const fetchCouriersAnalytics = async () => {
    if (userRole !== 'admin') return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const response = await apiCall(`/api/admin/couriers/analytics?${params.toString()}`, 'GET');
      if (response) {
        setAnalyticsData(response);
      }
    } catch (error) {
      console.error('Error fetching courier analytics:', error);
      setError(`Ошибка загрузки аналитики: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Рассчитать время прибытия
  const calculateETA = async () => {
    if (!destinationAddress.trim()) {
      setError('Введите адрес назначения');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall('/api/courier/eta/calculate', 'POST', {
        destination_address: destinationAddress
      });
      
      if (response) {
        setEtaCalculation(response);
      }
    } catch (error) {
      console.error('Error calculating ETA:', error);
      setError(`Ошибка расчета времени прибытия: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Инициализация
  useEffect(() => {
    fetchCouriers();
  }, [userRole]);

  useEffect(() => {
    if (selectedCourier) {
      fetchCourierHistory();
    }
  }, [selectedCourier, dateFrom, dateTo]);

  // Форматировать время
  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleString('ru-RU');
  };

  // Форматировать дату
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  // Получить название статуса
  const getStatusLabel = (status) => {
    const labels = {
      'offline': 'Не в сети',
      'online': 'Свободен',
      'on_route': 'Едет к клиенту',
      'at_pickup': 'На месте забора',
      'at_delivery': 'На месте доставки',
      'busy': 'Занят'
    };
    return labels[status] || status;
  };

  // Получить цвет статуса
  const getStatusColor = (status) => {
    const colors = {
      'offline': 'bg-gray-500',
      'online': 'bg-green-500',
      'on_route': 'bg-blue-500',
      'at_pickup': 'bg-orange-500',
      'at_delivery': 'bg-purple-500',
      'busy': 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">История и аналитика курьеров</h2>
          <p className="text-gray-600">Анализ перемещений, расчет времени прибытия и эффективности</p>
        </div>
      </div>

      <Tabs defaultValue="history" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="history">История перемещений</TabsTrigger>
          <TabsTrigger value="eta">Расчет времени прибытия</TabsTrigger>
          {userRole === 'admin' && <TabsTrigger value="analytics">Аналитика</TabsTrigger>}
          <TabsTrigger value="realtime">Real-time данные</TabsTrigger>
        </TabsList>

        {/* История перемещений */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Route className="mr-2 h-5 w-5" />
                История перемещений курьера
              </CardTitle>
              <CardDescription>
                Просмотр траектории движения и активности курьера
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Фильтры */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label htmlFor="courier-select">Курьер</Label>
                  <Select value={selectedCourier} onValueChange={setSelectedCourier}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите курьера" />
                    </SelectTrigger>
                    <SelectContent>
                      {couriers.map((courier) => (
                        <SelectItem key={courier.id} value={courier.id}>
                          {courier.full_name} ({courier.transport_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="date-from">Дата от</Label>
                  <Input
                    id="date-from"
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                  />
                </div>
                
                <div>
                  <Label htmlFor="date-to">Дата до</Label>
                  <Input
                    id="date-to"
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                  />
                </div>
                
                <div className="flex items-end">
                  <Button 
                    onClick={fetchCourierHistory}
                    disabled={isLoading || !selectedCourier}
                    className="w-full"
                  >
                    <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Обновить
                  </Button>
                </div>
              </div>

              {/* Результаты истории */}
              {historyData && (
                <div className="space-y-4">
                  {/* Статистика */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <MapPin className="h-5 w-5 text-blue-500" />
                          <div>
                            <p className="text-sm text-gray-500">Точек маршрута</p>
                            <p className="text-lg font-bold">{historyData.total_points}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <Route className="h-5 w-5 text-green-500" />
                          <div>
                            <p className="text-sm text-gray-500">Пройдено км</p>
                            <p className="text-lg font-bold">{historyData.total_distance_km}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-5 w-5 text-purple-500" />
                          <div>
                            <p className="text-sm text-gray-500">Дней активности</p>
                            <p className="text-lg font-bold">
                              {historyData.daily_stats ? historyData.daily_stats.length : 0}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <Activity className="h-5 w-5 text-orange-500" />
                          <div>
                            <p className="text-sm text-gray-500">Период</p>
                            <p className="text-sm font-bold">
                              {formatDate(historyData.date_from)} - {formatDate(historyData.date_to)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Ежедневная статистика */}
                  {historyData.daily_stats && historyData.daily_stats.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Ежедневная активность</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {historyData.daily_stats.map((day) => (
                            <div key={day.date} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-3">
                                <Calendar className="h-4 w-4 text-gray-500" />
                                <div>
                                  <p className="font-medium">{formatDate(day.date)}</p>
                                  <div className="flex space-x-4 text-sm text-gray-500">
                                    <span>{day.points_count} точек</span>
                                    <span>{day.distance_km} км</span>
                                    {day.avg_speed > 0 && <span>{day.avg_speed} км/ч макс</span>}
                                  </div>
                                </div>
                              </div>
                              <div className="flex space-x-1">
                                {day.statuses.map((status) => (
                                  <Badge
                                    key={status}
                                    className={`${getStatusColor(status)} text-white text-xs`}
                                  >
                                    {getStatusLabel(status)}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Последние точки маршрута */}
                  {historyData.history && historyData.history.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Последние перемещения</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {historyData.history.slice(-20).reverse().map((point, index) => (
                            <div key={point.id} className="flex items-center justify-between p-2 border-b">
                              <div className="flex items-center space-x-3">
                                <div className={`w-3 h-3 rounded-full ${getStatusColor(point.status)}`}></div>
                                <div>
                                  <p className="text-sm font-medium">{formatTime(point.timestamp)}</p>
                                  <p className="text-xs text-gray-500">
                                    {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
                                  </p>
                                  {point.current_address && (
                                    <p className="text-xs text-gray-600">{point.current_address}</p>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <Badge variant="outline" className="text-xs">
                                  {getStatusLabel(point.status)}
                                </Badge>
                                {point.speed && (
                                  <p className="text-xs text-gray-500 mt-1">{point.speed} км/ч</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Расчет времени прибытия */}
        <TabsContent value="eta" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Timer className="mr-2 h-5 w-5" />
                Расчет времени прибытия (ETA)
              </CardTitle>
              <CardDescription>
                Рассчитать приблизительное время прибытия курьера к адресу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <Label htmlFor="destination">Адрес назначения</Label>
                  <Input
                    id="destination"
                    value={destinationAddress}
                    onChange={(e) => setDestinationAddress(e.target.value)}
                    placeholder="Введите адрес назначения"
                  />
                </div>
                <div className="flex items-end">
                  <Button 
                    onClick={calculateETA}
                    disabled={isLoading || !destinationAddress.trim()}
                    className="w-full"
                  >
                    <Target className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Рассчитать ETA
                  </Button>
                </div>
              </div>

              {etaCalculation && (
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold text-blue-800 mb-2">Маршрут</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 text-green-500 mr-2" />
                            <span>Текущее местоположение: {etaCalculation.current_location.latitude.toFixed(4)}, {etaCalculation.current_location.longitude.toFixed(4)}</span>
                          </div>
                          <div className="flex items-center">
                            <Target className="h-4 w-4 text-red-500 mr-2" />
                            <span>Назначение: {etaCalculation.destination_address}</span>
                          </div>
                          <div className="flex items-center">
                            <Route className="h-4 w-4 text-blue-500 mr-2" />
                            <span>Расстояние: {etaCalculation.distance_km} км</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold text-blue-800 mb-2">Время прибытия</h4>
                        <div className="space-y-2">
                          <div className="bg-white p-3 rounded-lg border">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Время в пути:</span>
                              <span className="font-bold text-blue-600">{etaCalculation.estimated_time_minutes} мин</span>
                            </div>
                          </div>
                          <div className="bg-white p-3 rounded-lg border">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Прибытие:</span>
                              <span className="font-bold text-green-600">
                                {formatTime(etaCalculation.estimated_arrival)}
                              </span>
                            </div>
                          </div>
                          <div className="text-xs text-gray-600 space-y-1">
                            <div>Транспорт: {etaCalculation.transport_type}</div>
                            <div>Средняя скорость: {etaCalculation.avg_speed_kmh} км/ч</div>
                            <div>Буферное время: {etaCalculation.buffer_minutes} мин</div>
                            <div>Рассчитано: {formatTime(etaCalculation.calculated_at)}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Аналитика (только для админов) */}
        {userRole === 'admin' && (
          <TabsContent value="analytics" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="mr-2 h-5 w-5" />
                  Аналитика эффективности курьеров
                </CardTitle>
                <CardDescription>
                  Анализ производительности и эффективности всех курьеров
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="analytics-date-from">Период анализа от</Label>
                      <Input
                        id="analytics-date-from"
                        type="date"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="analytics-date-to">до</Label>
                      <Input
                        id="analytics-date-to"
                        type="date"
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                      />
                    </div>
                  </div>
                  <Button onClick={fetchCouriersAnalytics} disabled={isLoading}>
                    <TrendingUp className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Сгенерировать аналитику
                  </Button>
                </div>

                {analyticsData && (
                  <div className="space-y-6">
                    {/* Общая статистика */}
                    <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
                      <CardHeader>
                        <CardTitle className="text-lg">Общая статистика</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <p className="text-2xl font-bold text-blue-600">{analyticsData.summary.total_couriers}</p>
                            <p className="text-sm text-gray-600">Активных курьеров</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold text-green-600">{analyticsData.summary.total_distance_km} км</p>
                            <p className="text-sm text-gray-600">Общий пробег</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold text-purple-600">{analyticsData.summary.total_requests}</p>
                            <p className="text-sm text-gray-600">Всего заявок</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold text-orange-600">{analyticsData.summary.avg_completion_rate}%</p>
                            <p className="text-sm text-gray-600">Средний % выполнения</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Детальная аналитика по курьерам */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Производительность курьеров</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {analyticsData.analytics.map((courier) => (
                            <div key={courier.courier_id} className="p-4 border rounded-lg">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                  <Truck className="h-5 w-5 text-gray-500" />
                                  <div>
                                    <h4 className="font-semibold">{courier.courier_name}</h4>
                                    <p className="text-sm text-gray-500">
                                      {courier.transport_type} • {courier.warehouse_name}
                                    </p>
                                  </div>
                                </div>
                                <Badge className={courier.metrics.completion_rate >= 80 ? 'bg-green-500' : 'bg-orange-500'}>
                                  {courier.metrics.completion_rate}% выполнения
                                </Badge>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <p className="text-gray-500">Пройдено</p>
                                  <p className="font-semibold">{courier.metrics.total_distance_km} км</p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Активность</p>
                                  <p className="font-semibold">{courier.metrics.total_active_hours} ч</p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Средняя скорость</p>
                                  <p className="font-semibold">{courier.metrics.avg_speed_kmh} км/ч</p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Заявки</p>
                                  <p className="font-semibold">
                                    {courier.metrics.completed_requests}/{courier.metrics.total_requests}
                                  </p>
                                </div>
                              </div>
                              
                              {/* Статусы активности */}
                              <div className="mt-3 flex flex-wrap gap-1">
                                {Object.entries(courier.metrics.status_breakdown).map(([status, count]) => (
                                  <Badge key={status} variant="outline" className="text-xs">
                                    {getStatusLabel(status)}: {count}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Real-time данные */}
        <TabsContent value="realtime" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="mr-2 h-5 w-5" />
                Real-time мониторинг
              </CardTitle>
              <CardDescription>
                Текущая активность и статистика в реальном времени
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Real-time данные</h3>
                <p className="text-gray-500">
                  Эта функция интегрирована с основной картой отслеживания курьеров.
                  Перейдите в раздел "Курьеры" → "Карта отслеживания" для просмотра real-time данных.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Ошибки */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-700">
            {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default CourierHistoryAnalytics;